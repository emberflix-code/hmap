<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * Dengue cluster surveillance — surfaces clusters detected by
 * ml/detect_clusters.py (CESU's 200m / >=3 cases / 4-week rule).
 *
 * Three read-only endpoints, all under the hrmo middleware. Cluster
 * detection itself is offline (runs nightly or on-demand from the ML host);
 * Laravel just reads the persisted hmap_db tables.
 */
class ClustersController extends Controller
{
    /**
     * Latest detection_runs row + summary stats. Frontend uses this to
     * discover which run to display by default and to warn if no run exists.
     */
    public function latestRun(): JsonResponse
    {
        $run = DB::table('detection_runs')
            ->orderByDesc('run_at')
            ->first();

        if (!$run) {
            return response()->json([
                'detection_run_id' => null,
                'message' => 'No cluster-detection runs in the database yet.',
            ]);
        }

        return response()->json([
            'detection_run_id'  => (int) $run->detection_run_id,
            'run_at'            => $run->run_at,
            'disease_code'      => $run->disease_code,
            'eps_meters'        => (float) $run->eps_meters,
            'min_samples'       => (int) $run->min_samples,
            'window_weeks'      => (int) $run->window_weeks,
            'date_range_start'  => $run->date_range_start,
            'date_range_end'    => $run->date_range_end,
            'cases_evaluated'   => (int) $run->cases_evaluated,
            'clusters_detected' => (int) $run->clusters_detected,
        ]);
    }

    /**
     * List clusters in a detection run. Default: latest run, all years.
     * Filter by `year` to scope to a specific year; useful for the
     * year-selector in the cluster map UI.
     */
    public function index(Request $request): JsonResponse
    {
        $request->validate([
            'run_id'   => 'nullable|integer|min:1',
            'year'     => 'nullable|integer|min:2010|max:2100',
            'min_size' => 'nullable|integer|min:1|max:1000',
        ]);

        $runId = $request->input('run_id');
        if (!$runId) {
            $latest = DB::table('detection_runs')->orderByDesc('run_at')->value('detection_run_id');
            if (!$latest) {
                return response()->json([]);
            }
            $runId = (int) $latest;
        }

        $q = DB::table('case_clusters')
            ->where('detection_run_id', $runId)
            ->select(
                'cluster_id',
                'window_start',
                'window_end',
                'centroid_lat',
                'centroid_lng',
                'case_count',
                'radius_m',
                'barangays_involved',
            )
            ->orderBy('window_start')
            ->orderByDesc('case_count');

        if ($request->filled('year')) {
            $year = (int) $request->input('year');
            $q->whereYear('window_end', $year);
        }
        if ($request->filled('min_size')) {
            $q->where('case_count', '>=', (int) $request->input('min_size'));
        }

        $rows = $q->get()->map(function ($r) {
            return [
                'cluster_id'         => (int) $r->cluster_id,
                'window_start'       => $r->window_start,
                'window_end'         => $r->window_end,
                'centroid_lat'       => (float) $r->centroid_lat,
                'centroid_lng'       => (float) $r->centroid_lng,
                'case_count'         => (int) $r->case_count,
                'radius_m'           => (float) $r->radius_m,
                'barangays_involved' => $r->barangays_involved,
                // Number of barangays the cluster spans; the cross-barangay
                // count is the thesis's headline novelty (see Ch.4 / Ch.5).
                'barangay_count'     => $r->barangays_involved
                    ? count(array_filter(array_map('trim', explode(',', $r->barangays_involved))))
                    : 0,
            ];
        });

        return response()->json([
            'detection_run_id' => $runId,
            'count' => $rows->count(),
            'clusters' => $rows,
        ]);
    }

    /**
     * Detail for one cluster: same fields as the list row plus the full
     * member list (case_id, lat/lng, address, onset, classification).
     * Drives the side-panel detail view in the frontend.
     */
    public function show(int $clusterId): JsonResponse
    {
        $cluster = DB::table('case_clusters')->where('cluster_id', $clusterId)->first();
        if (!$cluster) {
            return response()->json(['error' => 'cluster_not_found'], 404);
        }

        $members = DB::table('case_cluster_members as m')
            ->join('cases as c', 'c.case_id', '=', 'm.case_id')
            ->join('case_addresses as a', 'a.case_id', '=', 'c.case_id')
            ->join('barangays as b', 'b.barangay_id', '=', 'c.barangay_id')
            ->where('m.cluster_id', $clusterId)
            ->orderBy('c.date_onset')
            ->select(
                'c.case_id',
                'c.date_onset',
                'c.morbidity_year',
                'c.morbidity_week',
                'c.case_classification',
                'c.age',
                'c.sex',
                'b.barangay_name',
                'a.raw_street_purok',
                'a.case_lat',
                'a.case_lng',
                'a.geocode_source',
            )
            ->get()
            ->map(fn ($m) => [
                'case_id'             => (int) $m->case_id,
                'date_onset'          => $m->date_onset,
                'morbidity_year'      => (int) $m->morbidity_year,
                'morbidity_week'      => (int) $m->morbidity_week,
                'case_classification' => $m->case_classification,
                'age'                 => $m->age !== null ? (int) $m->age : null,
                'sex'                 => $m->sex,
                'barangay_name'       => $m->barangay_name,
                'street_address'      => $m->raw_street_purok,
                'lat'                 => (float) $m->case_lat,
                'lng'                 => (float) $m->case_lng,
                'geocode_source'      => $m->geocode_source,
            ]);

        return response()->json([
            'cluster_id'         => (int) $cluster->cluster_id,
            'detection_run_id'   => (int) $cluster->detection_run_id,
            'window_start'       => $cluster->window_start,
            'window_end'         => $cluster->window_end,
            'centroid_lat'       => (float) $cluster->centroid_lat,
            'centroid_lng'       => (float) $cluster->centroid_lng,
            'case_count'         => (int) $cluster->case_count,
            'radius_m'           => (float) $cluster->radius_m,
            'barangays_involved' => $cluster->barangays_involved,
            'members'            => $members,
        ]);
    }
}
