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
