<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class DashboardController extends Controller
{
    /**
     * Reference list: 16 Parañaque barangays.
     */
    public function barangays(): JsonResponse
    {
        $rows = DB::table('barangays')
            ->select('barangay_id', 'barangay_name', 'population', 'centroid_lat', 'centroid_lng', 'district')
            ->orderBy('barangay_name')
            ->get();
        return response()->json($rows);
    }

    /**
     * Reference list: 29 PIDSR diseases (alert_enabled flag tells the frontend
     * which ones support thresholds; forecast_enabled tells which support Prophet).
     */
    public function diseases(): JsonResponse
    {
        $rows = DB::table('diseases')
            ->select('disease_id', 'disease_code', 'disease_name', 'disease_category', 'alert_enabled', 'forecast_enabled')
            ->orderBy('display_order')
            ->get();
        return response()->json($rows);
    }

    /**
     * Weekly case counts for a disease over a year range, optionally filtered
     * by barangay. Used by the trend-chart and the heat-map data layer.
     */
    public function weeklySeries(Request $request): JsonResponse
    {
        $request->validate([
            'disease_code'  => 'required|string|max:20',
            'year_start'    => 'required|integer|min:2010|max:2100',
            'year_end'      => 'required|integer|min:2010|max:2100',
            'barangay_id'   => 'nullable|integer|min:1|max:16',
            'classifications' => 'nullable|string',  // CSV e.g. "Confirmed,Probable"
        ]);

        $classes = explode(',', $request->input('classifications', 'Confirmed,Probable'));
        $classes = array_values(array_filter(array_map('trim', $classes)));

        $q = DB::table('cases as c')
            ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
            ->where('d.disease_code', $request->disease_code)
            ->whereBetween('c.morbidity_year', [$request->year_start, $request->year_end])
            ->whereIn('c.case_classification', $classes)
            ->where('c.status_flag', 'Active')
            ->groupBy('c.morbidity_year', 'c.morbidity_week')
            ->selectRaw('c.morbidity_year AS year, c.morbidity_week AS week, COUNT(*) AS cases')
            ->orderBy('c.morbidity_year')
            ->orderBy('c.morbidity_week');

        if ($request->filled('barangay_id')) {
            $q->where('c.barangay_id', (int) $request->barangay_id);
        }

        return response()->json($q->get());
    }

    /**
     * WHO EWARN thresholds (pre-computed) for the trend chart's overlay.
     */
    public function thresholds(Request $request): JsonResponse
    {
        $request->validate([
            'disease_code' => 'required|string|max:20',
        ]);

        $rows = DB::table('thresholds as t')
            ->join('diseases as d', 'd.disease_id', '=', 't.disease_id')
            ->where('d.disease_code', $request->disease_code)
            ->orderBy('t.morbidity_week')
            ->select('t.morbidity_week', 't.baseline_years', 't.mean_cases', 't.std_dev', 't.threshold_value')
            ->get();

        return response()->json($rows);
    }

    /**
     * Per-barangay case counts for a single (disease, year, week). Drives the
     * heat-map intensity layer.
     */
    public function heatmapWeek(Request $request): JsonResponse
    {
        $request->validate([
            'disease_code'   => 'required|string|max:20',
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]);

        $rows = DB::table('cases as c')
            ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
            ->join('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
            ->where('d.disease_code', $request->disease_code)
            ->where('c.morbidity_year', $request->morbidity_year)
            ->where('c.morbidity_week', $request->morbidity_week)
            ->whereIn('c.case_classification', ['Confirmed', 'Probable'])
            ->where('c.status_flag', 'Active')
            ->groupBy('b.barangay_id', 'b.barangay_name', 'b.centroid_lat', 'b.centroid_lng')
            ->selectRaw('b.barangay_id, b.barangay_name, b.centroid_lat, b.centroid_lng, COUNT(*) AS cases')
            ->get();

        return response()->json($rows);
    }

    /**
     * Identity echo — confirms the HRMO middleware attached attributes.
     */
    public function whoami(Request $request): JsonResponse
    {
        return response()->json([
            'employee_id'   => $request->attributes->get('hmap.employee_id'),
            'employee_name' => $request->attributes->get('hmap.employee_name'),
            'role'          => $request->attributes->get('hmap.role'),
        ]);
    }

    /**
     * KPIs for the top-of-dashboard strip. For the selected (disease, year, week):
     *   - cases_this_week:   Confirmed+Probable across all barangays
     *   - cases_ytd:         Confirmed+Probable since Jan 1 of `year`
     *   - alerts_this_week:  count of barangays where this week's cases exceed the EWARN threshold
     *   - cases_prior_year:  same week of `year - 1` (Confirmed+Probable, all barangays)
     */
    public function summary(Request $request): JsonResponse
    {
        $request->validate([
            'disease_code'   => 'required|string|max:20',
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]);
        $disease = $request->disease_code;
        $year = (int) $request->morbidity_year;
        $week = (int) $request->morbidity_week;

        $diseaseRow = DB::table('diseases')->where('disease_code', $disease)->first(['disease_id']);
        if (!$diseaseRow) {
            return response()->json([
                'cases_this_week' => 0, 'cases_ytd' => 0,
                'alerts_this_week' => 0, 'cases_prior_year' => 0,
            ]);
        }
        $did = $diseaseRow->disease_id;

        $confProb = ['Confirmed', 'Probable'];

        $casesThisWeek = DB::table('cases')
            ->where('disease_id', $did)
            ->where('morbidity_year', $year)
            ->where('morbidity_week', $week)
            ->whereIn('case_classification', $confProb)
            ->where('status_flag', 'Active')
            ->count();

        $casesYtd = DB::table('cases')
            ->where('disease_id', $did)
            ->where('morbidity_year', $year)
            ->where('morbidity_week', '<=', $week)
            ->whereIn('case_classification', $confProb)
            ->where('status_flag', 'Active')
            ->count();

        $casesPriorYear = DB::table('cases')
            ->where('disease_id', $did)
            ->where('morbidity_year', $year - 1)
            ->where('morbidity_week', $week)
            ->whereIn('case_classification', $confProb)
            ->where('status_flag', 'Active')
            ->count();

        // Count barangays where this week's case count exceeds the (mean+2σ) threshold
        // computed against the prior 5 years. Reuse the same logic the RF labels use.
        $alertsThisWeek = $this->countAlertsAtWeek($did, $year, $week);

        return response()->json([
            'cases_this_week'  => $casesThisWeek,
            'cases_ytd'        => $casesYtd,
            'cases_prior_year' => $casesPriorYear,
            'alerts_this_week' => $alertsThisWeek,
        ]);
    }

    /**
     * Summary Weekly Update mirror — Category I and Category II tables for the
     * PIDSR workbook's `Summary Weekly Update` sheet. For each alert-enabled
     * disease and the given (year, week), returns:
     *   - cases_current:    YTD-through-week-N this year (all classifications, matches CESU)
     *   - deaths_current:   YTD-through-week-N this year, outcome='Died'
     *   - cases_prior:      Same for year-1
     *   - deaths_prior:     Same for year-1
     *   - avg_5yr_cases:    Mean of YTD-through-week-N counts across the 5 prior calendar years
     *   - avg_5yr_deaths:   Same, deaths
     * CFR is computed client-side (deaths / cases).
     *
     * IMPORTANT: This uses ALL classifications (the CESU basis), NOT
     * Confirmed+Probable, because the PIDSR workbook does the same. The alerting
     * threshold (countAlertsAtWeek) uses Confirmed+Probable per EWARN — that
     * distinction is intentional.
     */
    public function weeklySummary(Request $request): JsonResponse
    {
        $request->validate([
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]);
        $year = (int) $request->morbidity_year;
        $week = (int) $request->morbidity_week;

        // YTD-through-week-N aggregation per (disease, year), all classifications,
        // limited to the 7 years that overlap our reporting window (current,
        // previous, and the 5 baseline years).
        $yearsWindow = array_merge([$year, $year - 1], range($year - 6, $year - 2));
        $yearsWindow = array_values(array_unique($yearsWindow));

        $rows = DB::table('cases as c')
            ->join('diseases as d', 'd.disease_id', '=', 'c.disease_id')
            ->where('d.alert_enabled', 1)
            ->whereIn('c.morbidity_year', $yearsWindow)
            ->where('c.morbidity_week', '<=', $week)
            ->where('c.status_flag', 'Active')
            ->groupBy('d.disease_id', 'd.disease_code', 'd.disease_name',
                       'd.disease_category', 'd.display_order', 'c.morbidity_year')
            ->selectRaw("
                d.disease_id, d.disease_code, d.disease_name, d.disease_category, d.display_order,
                c.morbidity_year,
                COUNT(*) AS cases,
                SUM(CASE WHEN c.outcome = 'Died' THEN 1 ELSE 0 END) AS deaths
            ")
            ->get();

        // Pivot to {disease_id: {year: [cases, deaths]}}
        $byDisease = [];
        foreach ($rows as $r) {
            $byDisease[$r->disease_id]['meta'] = [
                'code' => $r->disease_code,
                'name' => $r->disease_name,
                'category' => $r->disease_category,
                'order' => $r->display_order,
            ];
            $byDisease[$r->disease_id]['years'][(int) $r->morbidity_year] =
                [(int) $r->cases, (int) $r->deaths];
        }

        // Build the response: one entry per alert-enabled disease (including
        // those with zero observations in the window, so the table is dense)
        $allDiseases = DB::table('diseases')
            ->where('alert_enabled', 1)
            ->orderBy('display_order')
            ->get(['disease_id', 'disease_code', 'disease_name',
                    'disease_category', 'display_order']);

        $baselineYears = range($year - 5, $year - 1);
        $result = [];
        foreach ($allDiseases as $d) {
            $years = $byDisease[$d->disease_id]['years'] ?? [];
            $cur = $years[$year] ?? [0, 0];
            $prev = $years[$year - 1] ?? [0, 0];

            $baselineCases = [];
            $baselineDeaths = [];
            foreach ($baselineYears as $by) {
                $baselineCases[] = $years[$by][0] ?? 0;
                $baselineDeaths[] = $years[$by][1] ?? 0;
            }
            $result[] = [
                'disease_code'    => $d->disease_code,
                'disease_name'    => $d->disease_name,
                'disease_category' => $d->disease_category,
                'cases_current'   => $cur[0],
                'deaths_current'  => $cur[1],
                'cases_prior'     => $prev[0],
                'deaths_prior'    => $prev[1],
                'avg_5yr_cases'   => round(array_sum($baselineCases) / 5, 2),
                'avg_5yr_deaths'  => round(array_sum($baselineDeaths) / 5, 2),
            ];
        }

        return response()->json([
            'year' => $year,
            'week' => $week,
            'baseline_years' => $baselineYears,
            'rows' => $result,
        ]);
    }

    /**
     * Dengue detail mirror of the PIDSRMain sheet. For the given (year, week),
     * returns the YTD-through-week-N dengue case stats: this vs prior year,
     * sex split, age stats, DRU type breakdown, top sentinels.
     */
    public function dengueDetail(Request $request): JsonResponse
    {
        $request->validate([
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]);
        $year = (int) $request->morbidity_year;
        $week = (int) $request->morbidity_week;

        $dengueId = DB::table('diseases')->where('disease_code', 'DENGUE')->value('disease_id');
        if (!$dengueId) return response()->json(['error' => 'Dengue not seeded'], 500);

        // Reusable YTD scope
        $ytd = fn(int $y) => DB::table('cases')
            ->where('disease_id', $dengueId)
            ->where('morbidity_year', $y)
            ->where('morbidity_week', '<=', $week)
            ->where('status_flag', 'Active');

        $stats = function (int $y) use ($ytd) {
            $cases = (clone $ytd($y))->count();
            $deaths = (clone $ytd($y))->where('outcome', 'Died')->count();
            $males = (clone $ytd($y))->where('sex', 'Male')->count();
            $females = (clone $ytd($y))->where('sex', 'Female')->count();
            $ages = (clone $ytd($y))->whereNotNull('age')->pluck('age')->map(fn($v) => (int) $v)->all();
            sort($ages);
            $median = count($ages) > 0
                ? (count($ages) % 2 === 1
                    ? $ages[intdiv(count($ages), 2)]
                    : ($ages[count($ages) / 2 - 1] + $ages[count($ages) / 2]) / 2)
                : null;
            $byType = (clone $ytd($y))
                ->leftJoin('facilities as f', 'f.facility_id', '=', 'cases.facility_id')
                ->groupBy('f.facility_type')
                ->selectRaw("COALESCE(f.facility_type,'Unknown') AS facility_type, COUNT(*) AS n")
                ->get()
                ->pluck('n', 'facility_type')
                ->all();
            $bySentinel = (clone $ytd($y))
                ->join('facilities as f', 'f.facility_id', '=', 'cases.facility_id')
                ->where('f.is_sentinel', 1)
                ->groupBy('f.facility_id', 'f.facility_name')
                ->selectRaw('f.facility_name, COUNT(*) AS n')
                ->orderByDesc('n')
                ->limit(5)
                ->get()
                ->map(fn($r) => ['name' => $r->facility_name, 'cases' => (int) $r->n])
                ->all();
            $topAgeGroup = (clone $ytd($y))
                ->whereNotNull('age_group')
                ->groupBy('age_group')
                ->selectRaw('age_group, COUNT(*) AS n')
                ->orderByDesc('n')
                ->limit(1)
                ->first();
            return [
                'cases'      => $cases,
                'deaths'     => $deaths,
                'cfr'        => $cases > 0 ? round($deaths / $cases, 4) : 0,
                'males'      => $males,
                'females'    => $females,
                'age_min'    => count($ages) > 0 ? $ages[0] : null,
                'age_max'    => count($ages) > 0 ? end($ages) : null,
                'age_median' => $median,
                'by_dru_type' => $byType,
                'top_sentinels' => $bySentinel,
                'top_age_group' => $topAgeGroup
                    ? ['group' => $topAgeGroup->age_group, 'cases' => (int) $topAgeGroup->n]
                    : null,
            ];
        };

        return response()->json([
            'year' => $year,
            'week' => $week,
            'current' => $stats($year),
            'previous' => $stats($year - 1),
        ]);
    }

    /**
     * Per-barangay YTD rates mirror of the SBgy sheet. For (disease, year, week):
     *   - barangay, population (from barangays.population)
     *   - cases YTD-through-week-N (all classifications, CESU basis)
     *   - rate per 10,000 population
     *   - rank (1 = highest rate)
     */
    public function barangayRates(Request $request): JsonResponse
    {
        $request->validate([
            'disease_code'   => 'required|string|max:20',
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]);

        $rows = DB::table('barangays as b')
            ->leftJoin('cases as c', function ($j) use ($request) {
                $j->on('c.barangay_id', '=', 'b.barangay_id')
                  ->where('c.morbidity_year', (int) $request->morbidity_year)
                  ->where('c.morbidity_week', '<=', (int) $request->morbidity_week)
                  ->where('c.status_flag', 'Active');
            })
            ->leftJoin('diseases as d', function ($j) use ($request) {
                $j->on('d.disease_id', '=', 'c.disease_id')
                  ->where('d.disease_code', $request->disease_code);
            })
            ->groupBy('b.barangay_id', 'b.barangay_name', 'b.population', 'b.district')
            ->selectRaw("
                b.barangay_id, b.barangay_name, b.population, b.district,
                SUM(CASE WHEN d.disease_code = ? THEN 1 ELSE 0 END) AS cases
            ", [$request->disease_code])
            ->orderBy('b.barangay_name')
            ->get();

        $out = [];
        foreach ($rows as $r) {
            $pop = (int) ($r->population ?? 0);
            $cases = (int) $r->cases;
            $rate = $pop > 0 ? round(($cases / $pop) * 10000, 4) : 0;
            $out[] = [
                'barangay_id'   => $r->barangay_id,
                'barangay_name' => $r->barangay_name,
                'population'    => $pop,
                'district'      => $r->district,
                'cases'         => $cases,
                'rate_per_10k'  => $rate,
            ];
        }

        // Rank by rate descending; ties keep insertion order (alphabetical)
        usort($out, fn($a, $b) => $b['rate_per_10k'] <=> $a['rate_per_10k']);
        foreach ($out as $i => $row) $out[$i]['rank'] = $i + 1;

        $totalCases = array_sum(array_column($out, 'cases'));
        $totalPop = array_sum(array_column($out, 'population'));
        $cityRate = $totalPop > 0 ? round(($totalCases / $totalPop) * 10000, 4) : 0;

        return response()->json([
            'disease_code' => $request->disease_code,
            'year' => (int) $request->morbidity_year,
            'week' => (int) $request->morbidity_week,
            'rows' => $out,
            'total' => [
                'cases' => $totalCases,
                'population' => $totalPop,
                'rate_per_10k' => $cityRate,
            ],
        ]);
    }

    /**
     * Dengue narrative memo generator. Returns a JSON {memo: "..."} where the
     * memo body fills the template CESU uses in the workbook's `Weekly Updates
     * per disease` sheet. The City Epidemiologist edits this draft before
     * sending — it's not a final authored document.
     */
    public function dengueMemo(Request $request): JsonResponse
    {
        $request->validate([
            'morbidity_year' => 'required|integer|min:2010|max:2100',
            'morbidity_week' => 'required|integer|min:1|max:53',
        ]);
        $year = (int) $request->morbidity_year;
        $week = (int) $request->morbidity_week;

        // Reuse the dengue detail computation so the memo is consistent with
        // what the Dengue tab shows for the same (year, week).
        $detail = json_decode($this->dengueDetail($request)->getContent(), true);
        $ratesReq = new Request(['disease_code' => 'DENGUE', 'morbidity_year' => $year, 'morbidity_week' => $week]);
        $rates = json_decode($this->barangayRates($ratesReq)->getContent(), true);

        $cur = $detail['current'];
        $prev = $detail['previous'];

        // % change vs prior year YTD
        $changePct = $prev['cases'] > 0
            ? round((($cur['cases'] - $prev['cases']) / $prev['cases']) * 100)
            : null;
        $changeStr = $changePct === null
            ? 'with no prior-year comparison available'
            : ($changePct === 0
                ? 'unchanged from'
                : ($changePct > 0
                    ? "{$changePct}% higher than"
                    : abs($changePct) . '% lower than'));

        // Top two barangays by rate per 10k
        $top = array_slice($rates['rows'], 0, 2);
        $bgyParagraph = '';
        if (count($top) >= 1 && $top[0]['cases'] > 0) {
            $b1 = $top[0];
            $bgyParagraph = "Barangay {$b1['barangay_name']} had the highest case rate at "
                . number_format($b1['rate_per_10k'], 2) . " cases per 10,000 population";
            if (count($top) >= 2 && $top[1]['cases'] > 0) {
                $b2 = $top[1];
                $bgyParagraph .= ", followed by Barangay {$b2['barangay_name']} at "
                    . number_format($b2['rate_per_10k'], 2) . " per 10,000 (Table 1)";
            }
            $bgyParagraph .= '.';
        }

        // Age description
        $ageStr = '';
        if ($cur['age_min'] !== null && $cur['age_max'] !== null) {
            $minLabel = $cur['age_min'] === 0 ? 'under 1 year old' : "{$cur['age_min']} year(s) old";
            $maxLabel = "{$cur['age_max']} years old";
            $ageStr = "Age of cases ranged from {$minLabel} to {$maxLabel}";
            if ($cur['age_median'] !== null) {
                $ageStr .= " (median {$cur['age_median']} years)";
            }
            $ageStr .= '.';
        }

        // Top age group
        $ageGroupStr = '';
        if ($cur['top_age_group']) {
            $ag = $cur['top_age_group'];
            $pct = round(($ag['cases'] / max(1, $cur['cases'])) * 100);
            $ageGroupStr = "The largest share of cases ({$pct}%) was in the {$ag['group']} age group (Table 2).";
        }

        // Top DRU and sentinel
        $druStr = '';
        if (!empty($cur['top_sentinels'])) {
            $top1 = $cur['top_sentinels'][0];
            $top1Pct = round(($top1['cases'] / max(1, $cur['cases'])) * 100);
            $druStr = "Most cases ({$top1Pct}%) were reported by {$top1['name']}";
            if (count($cur['top_sentinels']) >= 2) {
                $druStr .= ", followed by " . $cur['top_sentinels'][1]['name'];
            }
            $druStr .= ' (Table 3).';
        }

        // Date label (best-effort: convert morbidity week to approx. cutoff date)
        // Morbidity week N ends on the Saturday of ISO week N
        $weekEnd = $this->morbidityWeekEndDate($year, $week);
        $dateRange = 'January 1 to ' . $weekEnd->format('F j, Y');

        $cfrCur = $cur['cases'] > 0 ? number_format($cur['cfr'] * 100, 2) . '%' : '0%';

        $today = now()->format('F j, Y');
        $memo = <<<MEMO
TO:     OLGA Z. VIRTUSIO, MD, MPH       — City Health Officer
        DR. DARWIN DAVID                  — Dengue Program Coordinator
        DR. FRANCISCO GOZOS II            — Head, Sanitation Division
        DIR. MARCO A.G. CABUENOS, JR.     — DILG-OIC, City Director
        DR. REGINALD SANTOS               — Infection Control Program Coordinator

FROM:   DARIUS J. SEBASTIAN, MD, PHSAE, MPH
        City Epidemiologist

RE:     Dengue Updates in Parañaque City, Morbidity Week {$week}

DATE:   {$today}

Time Period:   {$dateRange}
Data Source:   Philippine Integrated Disease Surveillance and Response (via H-MAP)


A. Dengue

There were {$cur['cases']} cases reported from {$dateRange}. This is {$changeStr} the same period
last year ({$prev['cases']} cases). Total deaths to date: {$cur['deaths']} (CFR {$cfrCur}).

{$bgyParagraph}

{$ageStr} {$ageGroupStr}

{$druStr}

Sex distribution: {$cur['males']} male ({$this->safePct($cur['males'], $cur['cases'])}%), {$cur['females']} female ({$this->safePct($cur['females'], $cur['cases'])}%).

— Auto-generated by H-MAP from PIDSR Registry data. Review and edit before sending.

MEMO;

        return response()->json([
            'year' => $year,
            'week' => $week,
            'memo' => $memo,
        ]);
    }

    private function safePct(int $n, int $total): string
    {
        return $total > 0 ? number_format(($n / $total) * 100, 1) : '0.0';
    }

    /**
     * Approximate the end-of-morbidity-week date for the report's "as of" line.
     * PIDSR follows the CDC MMWR convention: week 1 is the week containing
     * the year's first Saturday. We return the Saturday of the requested week.
     */
    private function morbidityWeekEndDate(int $year, int $week): \DateTime
    {
        // CDC MMWR: epi week starts Sunday, ends Saturday. Week 1 contains
        // the first Saturday of January OR the Saturday in the week of Jan 1
        // if it falls on Sunday-Wednesday. Simpler approximation: use ISO
        // weeks and shift to Saturday — accurate within ±1 week for display.
        $d = new \DateTime();
        $d->setISODate($year, $week);  // ISO Monday of given ISO week
        $d->modify('+5 days');         // Saturday
        return $d;
    }

    private function countAlertsAtWeek(int $diseaseId, int $year, int $week): int
    {
        // Per-barangay current-week counts
        $current = DB::table('cases')
            ->where('disease_id', $diseaseId)
            ->where('morbidity_year', $year)
            ->where('morbidity_week', $week)
            ->whereIn('case_classification', ['Confirmed', 'Probable'])
            ->where('status_flag', 'Active')
            ->groupBy('barangay_id')
            ->selectRaw('barangay_id, COUNT(*) AS n')
            ->pluck('n', 'barangay_id');

        if ($current->isEmpty()) return 0;

        // Per-barangay 5-year baseline mean + 2σ for the same week
        $baselineStart = $year - 5;
        $baselineEnd = $year - 1;
        $baseline = DB::table('cases')
            ->where('disease_id', $diseaseId)
            ->where('morbidity_week', $week)
            ->whereBetween('morbidity_year', [$baselineStart, $baselineEnd])
            ->whereIn('case_classification', ['Confirmed', 'Probable'])
            ->where('status_flag', 'Active')
            ->groupBy('barangay_id', 'morbidity_year')
            ->selectRaw('barangay_id, morbidity_year, COUNT(*) AS n')
            ->get();

        // Aggregate baseline rows → per-barangay mean and stddev
        $perBgy = [];
        foreach ($baseline as $r) {
            $perBgy[$r->barangay_id][] = (int) $r->n;
        }

        $alerts = 0;
        foreach ($current as $bid => $n) {
            $samples = $perBgy[$bid] ?? [];
            // Pad with zeros to a 5-year baseline (years with no case observations
            // still count as 0 for the baseline mean)
            while (count($samples) < 5) $samples[] = 0;
            $mean = array_sum($samples) / count($samples);
            $var = 0.0;
            foreach ($samples as $s) $var += ($s - $mean) ** 2;
            $std = sqrt($var / (count($samples) - 1));
            $threshold = $mean + 2 * $std;
            if ($n > $threshold && $n > 0) $alerts++;
        }
        return $alerts;
    }
}
