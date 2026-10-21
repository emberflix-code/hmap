<?php

namespace App\Services;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Rule-based barangay risk tiers (Ch.3 Module 6).
 *
 *   High      above the PIDSR epidemic threshold AND an active hotspot
 *   Moderate  above the epidemic threshold, OR an active hotspot, OR a rising
 *             forecast trend
 *   Low       none of these
 *
 * "Above the epidemic threshold" uses each barangay's own 5-year baseline for
 * the same morbidity week (mean + 2 SD, Confirmed + Probable; DOH, 2014,
 * p. 57); for single-case-trigger diseases any case counts (p. 58). An active
 * hotspot is a cluster from the latest detection run with the CESU rule
 * (200 m, 3 cases, 4 weeks) that overlaps the 4 weeks ending with the selected
 * week and includes a case from the barangay. The forecast trend comes from
 * the ML service and is considered only for the current week, since forecasts
 * start from today.
 */
class RiskTiers
{
    private const CESU_EPS_METERS = 200;
    private const CESU_MIN_CASES = 3;
    private const CESU_WINDOW_WEEKS = 4;

    /**
     * Per-barangay baseline for one (disease, year, week):
     * [barangay_id => ['mean' => float, 'sd' => float]] over the 5 prior years,
     * zero-padded so years without cases count as 0.
     */
    public static function barangayBaselines(int $diseaseId, int $year, int $week): array
    {
        $rows = DB::table('cases')
            ->where('disease_id', $diseaseId)
            ->where('morbidity_week', $week)
            ->whereBetween('morbidity_year', [$year - 5, $year - 1])
            ->whereIn('case_classification', ['Confirmed', 'Probable'])
            ->where('status_flag', 'Active')
            ->groupBy('barangay_id', 'morbidity_year')
            ->selectRaw('barangay_id, morbidity_year, COUNT(*) AS n')
            ->get();

        $samples = [];
        foreach ($rows as $r) {
            $samples[$r->barangay_id][] = (int) $r->n;
        }
        $out = [];
        foreach (DB::table('barangays')->pluck('barangay_id') as $bid) {
            $s = $samples[$bid] ?? [];
            while (count($s) < 5) $s[] = 0;
            $mean = array_sum($s) / count($s);
            $var = 0.0;
            foreach ($s as $x) $var += ($x - $mean) ** 2;
            $out[$bid] = ['mean' => $mean, 'sd' => sqrt($var / (count($s) - 1))];
        }
        return $out;
    }

    /** Confirmed + Probable counts per barangay for one (disease, year, week). */
    public static function currentCounts(int $diseaseId, int $year, int $week)
    {
        return DB::table('cases')
            ->where('disease_id', $diseaseId)
            ->where('morbidity_year', $year)
            ->where('morbidity_week', $week)
            ->whereIn('case_classification', ['Confirmed', 'Probable'])
            ->where('status_flag', 'Active')
            ->groupBy('barangay_id')
            ->selectRaw('barangay_id, COUNT(*) AS n')
            ->pluck('n', 'barangay_id');
    }

    /**
     * Tier for every barangay. Returns null if the disease code is unknown.
     *
     * @return array{disease_code:string, morbidity_year:int, morbidity_week:int,
     *               forecast_considered:bool, hotspot_run_id:?int, tiers:array}|null
     */
    public static function compute(string $diseaseCode, int $year, int $week): ?array
    {
        $disease = DB::table('diseases')->where('disease_code', $diseaseCode)
            ->first(['disease_id', 'single_case_trigger']);
        if (!$disease) {
            return null;
        }
        $did = (int) $disease->disease_id;
        $singleCase = (bool) $disease->single_case_trigger;

        $counts = self::currentCounts($did, $year, $week);
        $baselines = self::barangayBaselines($did, $year, $week);
        [$hotspotBarangays, $runId] = self::hotspotBarangays($diseaseCode, $year, $week);
        $rising = self::isCurrentWeek($year, $week) ? self::risingForecast($diseaseCode) : null;

        $tiers = [];
        foreach (DB::table('barangays')->orderBy('barangay_id')->get(['barangay_id', 'barangay_name']) as $b) {
            $bid = (int) $b->barangay_id;
            $n = (int) ($counts[$bid] ?? 0);
            $mean = $baselines[$bid]['mean'];
            $sd = $baselines[$bid]['sd'];
            $epidemic = $mean + 2 * $sd;
            $aboveEpidemic = $singleCase ? $n > 0 : ($n > 0 && $n > $epidemic);
            $hotspot = isset($hotspotBarangays[$bid]);
            $risingTrend = $rising !== null && !empty($rising[$bid]);

            $reasons = [];
            if ($aboveEpidemic) {
                $reasons[] = $singleCase ? 'case of a single-case-trigger disease' : 'above epidemic threshold';
            }
            if ($hotspot) $reasons[] = 'active hotspot';
            if ($risingTrend) $reasons[] = 'rising forecast trend';

            if ($aboveEpidemic && $hotspot) {
                $tier = 'High';
            } elseif ($aboveEpidemic || $hotspot || $risingTrend) {
                $tier = 'Moderate';
            } else {
                $tier = 'Low';
            }

            $tiers[] = [
                'barangay_id'        => $bid,
                'barangay_name'      => $b->barangay_name,
                'tier'               => $tier,
                'reasons'            => $reasons,
                'current_cases'      => $n,
                'mean_5yr'           => round($mean, 2),
                'alert_threshold'    => round($mean + $sd, 2),
                'epidemic_threshold' => round($epidemic, 2),
                'above_epidemic'     => $aboveEpidemic,
                'active_hotspot'     => $hotspot,
                'rising_forecast'    => $rising === null ? null : $risingTrend,
            ];
        }

        return [
            'disease_code'        => $diseaseCode,
            'morbidity_year'      => $year,
            'morbidity_week'      => $week,
            'forecast_considered' => $rising !== null,
            'hotspot_run_id'      => $runId,
            'tiers'               => $tiers,
        ];
    }

    /**
     * Barangays with an active hotspot: [barangay_id => true], plus the
     * detection run used (latest run with the CESU parameters), or null.
     */
    private static function hotspotBarangays(string $diseaseCode, int $year, int $week): array
    {
        $runId = DB::table('detection_runs')
            ->where('disease_code', $diseaseCode)
            ->where('eps_meters', self::CESU_EPS_METERS)
            ->where('min_samples', self::CESU_MIN_CASES)
            ->where('window_weeks', self::CESU_WINDOW_WEEKS)
            ->orderByDesc('run_at')
            ->value('detection_run_id');
        if (!$runId) {
            return [[], null];
        }
        [$windowStart, $weekEnd] = self::windowDates($year, $week);
        $ids = DB::table('case_clusters as cc')
            ->join('case_cluster_members as m', 'm.cluster_id', '=', 'cc.cluster_id')
            ->join('cases as c', 'c.case_id', '=', 'm.case_id')
            ->where('cc.detection_run_id', $runId)
            ->where('cc.window_start', '<=', $weekEnd)
            ->where('cc.window_end', '>=', $windowStart)
            ->whereNotNull('c.barangay_id')
            ->distinct()
            ->pluck('c.barangay_id');
        return [array_fill_keys(array_map('intval', $ids->all()), true), (int) $runId];
    }

    /** [start, end] (Y-m-d) of the 4 weeks ending with the selected week's Saturday. */
    private static function windowDates(int $year, int $week): array
    {
        $end = new \DateTime();
        $end->setISODate($year, $week);   // ISO Monday
        $end->modify('+5 days');          // Saturday, end of the morbidity week
        $start = (clone $end)->modify('-' . (self::CESU_WINDOW_WEEKS * 7 - 1) . ' days');
        return [$start->format('Y-m-d'), $end->format('Y-m-d')];
    }

    private static function isCurrentWeek(int $year, int $week): bool
    {
        $now = new \DateTime();
        return (int) $now->format('o') === $year && abs((int) $now->format('W') - $week) <= 1;
    }

    /**
     * [barangay_id => bool] from the ML service's /predict/trend, or null when
     * no forecast is served for the disease or the service is unreachable.
     */
    private static function risingForecast(string $diseaseCode): ?array
    {
        try {
            $resp = Http::timeout(20)->acceptJson()->asJson()
                ->post(config('hmap.ml_url') . '/predict/trend', ['disease_code' => $diseaseCode]);
        } catch (\Throwable $e) {
            Log::warning('ML /predict/trend unreachable: ' . $e->getMessage());
            return null;
        }
        if (!$resp->successful()) {
            return null;  // 404 = no forecast served for this disease
        }
        $out = [];
        foreach ($resp->json('trends') ?? [] as $t) {
            $out[(int) $t['barangay_id']] = (bool) $t['rising'];
        }
        return $out;
    }
}
