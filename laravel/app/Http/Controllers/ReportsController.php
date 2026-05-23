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
                    ->join('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
                    ->where('c.entered_by', $employeeId)
                    ->where('c.status_flag', 'Active')
                    ->orderBy('c.entered_at', 'desc')
                    ->select(
                        'c.case_id', 'd.disease_code', 'c.case_classification', 'b.barangay_name',
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

        return $this->streamCsv(
            "disease-summary-{$suffix}.csv",
            ['disease_code', 'disease_name', 'barangay', 'morbidity_year',
              'morbidity_week', 'confirmed_probable', 'suspect', 'total_cases',
              'mean_5yr', 'threshold', 'alert'],
            function () use ($year, $diseaseCode) {
                $q = DB::table('cases as c')
                    ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
                    ->join('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
                    ->leftJoin('thresholds as t', function ($j) {
                        $j->on('t.disease_id', '=', 'c.disease_id')
                          ->on('t.morbidity_week', '=', 'c.morbidity_week');
                    })
                    ->where('c.morbidity_year', $year)
                    ->where('c.status_flag', 'Active')
                    ->groupBy('d.disease_code', 'd.disease_name', 'b.barangay_name',
                              'c.morbidity_year', 'c.morbidity_week',
                              't.mean_cases', 't.threshold_value')
                    ->orderBy('d.disease_code')
                    ->orderBy('b.barangay_name')
                    ->orderBy('c.morbidity_week')
                    ->selectRaw("
                        d.disease_code, d.disease_name, b.barangay_name AS barangay,
                        c.morbidity_year, c.morbidity_week,
                        SUM(CASE WHEN c.case_classification IN ('Confirmed','Probable') THEN 1 ELSE 0 END) AS confirmed_probable,
                        SUM(CASE WHEN c.case_classification = 'Suspect' THEN 1 ELSE 0 END) AS suspect,
                        COUNT(*) AS total_cases,
                        t.mean_cases AS mean_5yr,
                        t.threshold_value AS threshold
                    ");
                if ($diseaseCode) {
                    $q->where('d.disease_code', $diseaseCode);
                }
                return $q;
            },
            function ($r) {
                $alert = ($r->threshold !== null && (int) $r->confirmed_probable > (float) $r->threshold) ? 'YES' : '';
                return [
                    $r->disease_code, $r->disease_name, $r->barangay,
                    $r->morbidity_year, $r->morbidity_week,
                    $r->confirmed_probable, $r->suspect, $r->total_cases,
                    $r->mean_5yr !== null ? round((float) $r->mean_5yr, 2) : '',
                    $r->threshold !== null ? round((float) $r->threshold, 2) : '',
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
