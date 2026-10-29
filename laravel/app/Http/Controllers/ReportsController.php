<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Carbon;
use Illuminate\Support\Facades\DB;
use Symfony\Component\HttpFoundation\StreamedResponse;

/**
 * Module 5 — Reports and Data Export. Per Ch.3 (p.39-40):
 *
 *   Encoder       → personal entry log (cases I encoded)
 *   Analyst       → disease summary report (per-week, per-disease aggregates)
 *   Administrator → full case registry (all rows, all columns)
 *
 * Every export writes an EXPORT row to audit_log (RA 10173 §16 — "the data
 * subject has the right to be informed of any access, transfer, or disclosure
 * of their personal data"; we satisfy that by logging the export with the
 * employee_id, action_type, row count, and timestamp).
 *
 * CSVs are streamed via php://output rather than buffered in memory, so the
 * full-registry export at 35k rows doesn't OOM the PHP-FPM worker.
 */
class ReportsController extends Controller
{
    /**
     * GET /api/export/my-entries
     *
     * Encoder+ — every case the requesting employee personally encoded.
     * Smallest dataset; useful for an encoder verifying their week's work.
     */
    public function myEntries(Request $request): StreamedResponse
    {
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        return $this->streamCsv(
            'my-entries-' . $employeeId . '-' . Carbon::today()->toDateString() . '.csv',
            ['case_id', 'disease_code', 'case_classification', 'barangay',
              'morbidity_year', 'morbidity_week', 'date_onset', 'date_admitted',
              'age', 'sex', 'outcome', 'entered_at'],
            function () use ($employeeId) {
                return DB::table('cases as c')
                    ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
                    ->leftJoin('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
                    ->where('c.entered_by', $employeeId)
                    ->where('c.status_flag', 'Active')
                    ->orderBy('c.entered_at', 'desc')
                    ->select(
                        'c.case_id', 'd.disease_code', 'c.case_classification',
                        DB::raw("COALESCE(b.barangay_name, 'Unknown') AS barangay_name"),
                        'c.morbidity_year', 'c.morbidity_week', 'c.date_onset', 'c.date_admitted',
                        'c.age', 'c.sex', 'c.outcome', 'c.entered_at'
                    );
            },
            function ($r) {
                return [
                    $r->case_id, $r->disease_code, $r->case_classification, $r->barangay_name,
                    $r->morbidity_year, $r->morbidity_week, $r->date_onset, $r->date_admitted,
                    $r->age, $r->sex, $r->outcome, $r->entered_at,
                ];
            },
            $employeeId,
            $request->ip(),
            'my_entries'
        );
    }

    /**
     * GET /api/export/disease-summary?year=YYYY[&disease_code=XXX]
     *
     * Analyst+ — weekly aggregates per (disease, barangay) for the year.
     * Anonymized, no patient-level data; this is the report Analysts share
     * with city health office leadership.
     */
    public function diseaseSummary(Request $request): StreamedResponse
    {
        $request->validate([
            'year' => 'required|integer|min:2010|max:2100',
            'disease_code' => 'nullable|string|max:20',
        ]);
        $year = (int) $request->year;
        $diseaseCode = $request->disease_code;

        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $suffix = $diseaseCode ? "{$diseaseCode}-{$year}" : "all-{$year}";
        // Each row is one barangay, so it is judged against that barangay's own
        // 5-year baseline for the week, as the dashboard risk tiers are.
        $baselines = $this->barangayBaselines($year, $diseaseCode);

        return $this->streamCsv(
            "disease-summary-{$suffix}.csv",
            ['disease_code', 'disease_name', 'barangay', 'morbidity_year',
              'morbidity_week', 'confirmed_probable', 'suspect', 'total_cases',
              'barangay_mean_5yr', 'alert_threshold', 'epidemic_threshold', 'alert'],
            function () use ($year, $diseaseCode) {
                $q = DB::table('cases as c')
                    ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
                    // left join: cases with no recorded barangay are reported as "Unknown"
                    ->leftJoin('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
                    ->where('c.morbidity_year', $year)
                    ->where('c.status_flag', 'Active')
                    ->groupBy('d.disease_id', 'd.disease_code', 'd.disease_name', 'd.single_case_trigger',
                              'c.barangay_id', 'b.barangay_name', 'c.morbidity_year', 'c.morbidity_week')
                    ->orderBy('d.disease_code')
                    ->orderBy('b.barangay_name')
                    ->orderBy('c.morbidity_week')
                    ->selectRaw("
                        d.disease_id, d.disease_code, d.disease_name, d.single_case_trigger, c.barangay_id,
                        COALESCE(b.barangay_name, 'Unknown') AS barangay, c.morbidity_year, c.morbidity_week,
                        SUM(CASE WHEN c.case_classification IN ('Confirmed','Probable') THEN 1 ELSE 0 END) AS confirmed_probable,
                        SUM(CASE WHEN c.case_classification = 'Suspect' THEN 1 ELSE 0 END) AS suspect,
                        COUNT(*) AS total_cases
                    ");
                if ($diseaseCode) {
                    $q->where('d.disease_code', $diseaseCode);
                }
                return $q;
            },
            function ($r) use ($baselines) {
                // PIDSR levels (DOH, 2014, pp. 57-58): EPIDEMIC above mean + 2 SD,
                // ALERT above mean + 1 SD, or any case of a single-case disease.
                // Cases with no barangay have no barangay baseline.
                $n = (int) $r->confirmed_probable;
                $b = $r->barangay_id === null ? null
                    : ($baselines[$r->disease_id][$r->barangay_id][$r->morbidity_week] ?? ['mean' => 0.0, 'sd' => 0.0]);
                $alertAt = $b ? $b['mean'] + $b['sd'] : null;
                $epidemicAt = $b ? $b['mean'] + 2 * $b['sd'] : null;
                $alert = '';
                if ($r->single_case_trigger && $n > 0) {
                    $alert = 'ALERT (single case)';
                } elseif ($epidemicAt !== null && $n > 0 && $n > $epidemicAt) {
                    $alert = 'EPIDEMIC';
                } elseif ($alertAt !== null && $n > 0 && $n > $alertAt) {
                    $alert = 'ALERT';
                }
                return [
                    $r->disease_code, $r->disease_name, $r->barangay,
                    $r->morbidity_year, $r->morbidity_week,
                    $r->confirmed_probable, $r->suspect, $r->total_cases,
                    $b ? round($b['mean'], 2) : '',
                    $alertAt !== null ? round($alertAt, 2) : '',
                    $epidemicAt !== null ? round($epidemicAt, 2) : '',
                    $alert,
                ];
            },
            $employeeId,
            $request->ip(),
            'disease_summary'
        );
    }

    /**
     * GET /api/export/full-registry
     *
     * Administrator only — every active case record, all columns. The
     * thesis describes this as "for DOH submission or archival purposes."
     */
    public function fullRegistry(Request $request): StreamedResponse
    {
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        return $this->streamCsv(
            'hmap-registry-' . Carbon::today()->toDateString() . '.csv',
            ['case_id', 'disease_code', 'disease_name', 'case_classification',
              'date_onset', 'date_admitted', 'date_reported', 'barangay',
              'age', 'age_group', 'sex', 'outcome',
              'morbidity_year', 'morbidity_month', 'morbidity_week',
              'entered_by', 'entered_at', 'updated_at'],
            function () {
                return DB::table('cases as c')
                    ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
                    ->leftJoin('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
                    ->where('c.status_flag', 'Active')
                    ->orderBy('c.morbidity_year')->orderBy('c.morbidity_week')->orderBy('c.case_id')
                    ->select(
                        'c.case_id', 'd.disease_code', 'd.disease_name', 'c.case_classification',
                        'c.date_onset', 'c.date_admitted', 'c.date_reported', 'b.barangay_name',
                        'c.age', 'c.age_group', 'c.sex', 'c.outcome',
                        'c.morbidity_year', 'c.morbidity_month', 'c.morbidity_week',
                        'c.entered_by', 'c.entered_at', 'c.updated_at'
                    );
            },
            function ($r) {
                return [
                    $r->case_id, $r->disease_code, $r->disease_name, $r->case_classification,
                    $r->date_onset, $r->date_admitted, $r->date_reported, $r->barangay_name,
                    $r->age, $r->age_group, $r->sex, $r->outcome,
                    $r->morbidity_year, $r->morbidity_month, $r->morbidity_week,
                    $r->entered_by, $r->entered_at, $r->updated_at,
                ];
            },
            $employeeId,
            $request->ip(),
            'full_registry'
        );
    }

    /**
     * Per-barangay baselines for every (disease, week) of $year in one query:
     * [disease_id][barangay_id][week] => ['mean', 'sd'] over the 5 prior years,
     * Confirmed + Probable, years without cases counted as 0 (the same rule
     * as App\Services\RiskTiers::barangayBaselines). Missing keys mean 0 / 0.
     */
    private function barangayBaselines(int $year, ?string $diseaseCode): array
    {
        $q = DB::table('cases as c')
            ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
            ->whereBetween('c.morbidity_year', [$year - 5, $year - 1])
            ->whereIn('c.case_classification', ['Confirmed', 'Probable'])
            ->where('c.status_flag', 'Active')
            ->whereNotNull('c.barangay_id')
            ->groupBy('c.disease_id', 'c.barangay_id', 'c.morbidity_week', 'c.morbidity_year')
            ->selectRaw('c.disease_id, c.barangay_id, c.morbidity_week, COUNT(*) AS n');
        if ($diseaseCode) {
            $q->where('d.disease_code', $diseaseCode);
        }
        $samples = [];
        foreach ($q->get() as $r) {
            $samples[$r->disease_id][$r->barangay_id][$r->morbidity_week][] = (int) $r->n;
        }
        $out = [];
        foreach ($samples as $did => $byBgy) {
            foreach ($byBgy as $bid => $byWeek) {
                foreach ($byWeek as $week => $s) {
                    while (count($s) < 5) {
                        $s[] = 0;
                    }
                    $mean = array_sum($s) / 5;
                    $var = 0.0;
                    foreach ($s as $x) {
                        $var += ($x - $mean) ** 2;
                    }
                    $out[$did][$bid][$week] = ['mean' => $mean, 'sd' => sqrt($var / 4)];
                }
            }
        }
        return $out;
    }

    /**
     * Shared CSV streaming helper. Uses chunked iteration via the query
     * builder's lazy() so we don't load 35k rows into memory at once.
     * Writes the audit_log row after the stream completes successfully.
     */
    private function streamCsv(
        string $filename,
        array $headers,
        callable $queryBuilder,
        callable $rowMapper,
        int $employeeId,
        ?string $ip,
        string $exportLabel
    ): StreamedResponse {
        return response()->streamDownload(
            function () use ($queryBuilder, $rowMapper, $headers, $employeeId, $ip, $exportLabel) {
                $out = fopen('php://output', 'w');
                fputcsv($out, $headers);

                $rowCount = 0;
                foreach ($queryBuilder()->lazy(500) as $row) {
                    fputcsv($out, $rowMapper($row));
                    $rowCount++;
                }
                fclose($out);

                DB::table('audit_log')->insert([
                    'employee_id'  => $employeeId,
                    'action_type'  => 'EXPORT',
                    'target_table' => 'cases',
                    'target_id'    => null,
                    'old_values'   => null,
                    'new_values'   => json_encode([
                        'export' => $exportLabel,
                        'rows'   => $rowCount,
                    ]),
                    'ip_address'   => $ip,
                ]);
            },
            $filename,
            [
                'Content-Type'        => 'text/csv; charset=UTF-8',
                'Cache-Control'       => 'no-store',
            ],
        );
    }
}
