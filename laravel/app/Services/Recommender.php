<?php

namespace App\Services;

use Illuminate\Support\Facades\DB;

/**
 * Knowledge-based resource allocation recommender (Ch.3 Module 6).
 *
 * For every barangay that RiskTiers rates Moderate or High in the selected
 * disease and week, the active rules in recommendation_rules give the teams,
 * supplies, medicines and information materials to deploy:
 *
 *   - 'Moderate' rules apply to Moderate and High barangays, 'High' rules
 *     only to High (High is Moderate plus escalation).
 *   - A disease without rules of its own uses the rules with no disease.
 *   - Quantities scale by the rule's basis: fixed, per active case (Confirmed
 *     + Probable in the 4 weeks ending with the selected week), per 1,000
 *     residents, or as assessed by CESU (no quantity).
 *
 * Barangays are ranked by tier, then active cases (Shea et al., 2023:
 * rankings are more reliable than magnitudes). Results are saved in
 * recommendations so the Health Analyst can record the action taken; saving
 * again keeps recorded actions and drops pending items that no longer apply.
 */
class Recommender
{
    const WINDOW_WEEKS = 4;

    public static function generate(string $diseaseCode, int $year, int $week): ?array
    {
        $risk = RiskTiers::compute($diseaseCode, $year, $week);
        if ($risk === null) {
            return null;
        }
        $diseaseId = (int) DB::table('diseases')->where('disease_code', $diseaseCode)->value('disease_id');

        $rules = DB::table('recommendation_rules')->where('disease_id', $diseaseId)
            ->where('is_active', 1)->orderBy('priority')->orderBy('rule_id')->get();
        $fallback = $rules->isEmpty();
        if ($fallback) {
            $rules = DB::table('recommendation_rules')->whereNull('disease_id')
                ->where('is_active', 1)->orderBy('priority')->orderBy('rule_id')->get();
        }

        $active = self::activeCases($diseaseId, $year, $week);
        $population = DB::table('barangays')->pluck('population', 'barangay_id');

        $flagged = array_values(array_filter($risk['tiers'], function ($t) {
            return $t['tier'] !== 'Low';
        }));
        foreach ($flagged as &$t) {
            $t['active_cases'] = (int) ($active[$t['barangay_id']] ?? 0);
        }
        unset($t);
        usort($flagged, function ($a, $b) {
            return [$b['tier'] === 'High', $b['active_cases'], $b['current_cases'], $a['barangay_name']]
               <=> [$a['tier'] === 'High', $a['active_cases'], $a['current_cases'], $b['barangay_name']];
        });

        $now = now();
        $keep = [];
        DB::transaction(function () use ($flagged, $rules, $population, $diseaseId, $year, $week, $now, &$keep) {
            foreach ($flagged as $i => $t) {
                $items = [];
                foreach ($rules as $r) {
                    if ($r->risk_tier === 'High' && $t['tier'] !== 'High') {
                        continue;
                    }
                    $key = [
                        'disease_id'     => $diseaseId,
                        'barangay_id'    => $t['barangay_id'],
                        'morbidity_year' => $year,
                        'morbidity_week' => $week,
                        'rule_id'        => $r->rule_id,
                    ];
                    DB::table('recommendations')->updateOrInsert($key, [
                        'risk_tier'     => $t['tier'],
                        'barangay_rank' => $i + 1,
                        'active_cases'  => $t['active_cases'],
                        'category'      => $r->category,
                        'item'          => $r->item,
                        'quantity'      => self::quantity($r, $t['active_cases'], $population[$t['barangay_id']] ?? null),
                        'unit'          => $r->unit,
                        'rule_status'   => $r->status,
                        'generated_at'  => $now,
                    ]);
                    $keep[] = $t['barangay_id'] . ':' . $r->rule_id;
                }
            }

            // Pending items whose barangay or rule no longer applies are removed;
            // items with a recorded action stay, marked as no longer applying.
            $existing = DB::table('recommendations')->where('disease_id', $diseaseId)
                ->where('morbidity_year', $year)->where('morbidity_week', $week)->get();
            foreach ($existing as $e) {
                if (!in_array($e->barangay_id . ':' . $e->rule_id, $keep, true) && $e->action_status === 'Pending') {
                    DB::table('recommendations')->where('recommendation_id', $e->recommendation_id)->delete();
                }
            }
        });

        $rows = DB::table('recommendations as r')
            ->join('recommendation_rules as rr', 'rr.rule_id', '=', 'r.rule_id')
            ->where('r.disease_id', $diseaseId)->where('r.morbidity_year', $year)->where('r.morbidity_week', $week)
            ->orderBy('r.barangay_rank')->orderBy('rr.priority')->orderBy('r.rule_id')
            ->get(['r.*', 'rr.source', 'rr.notes', 'rr.scaling_basis']);

        $byBarangay = [];
        foreach ($rows as $r) {
            $byBarangay[$r->barangay_id][] = [
                'recommendation_id' => (int) $r->recommendation_id,
                'category'          => $r->category,
                'item'              => $r->item,
                'quantity'          => $r->quantity !== null ? (int) $r->quantity : null,
                'unit'              => $r->unit,
                'scaling_basis'     => $r->scaling_basis,
                'source'            => $r->source,
                'notes'             => $r->notes,
                'rule_status'       => $r->rule_status,
                'still_applies'     => in_array($r->barangay_id . ':' . $r->rule_id, $keep, true),
                'action_status'     => $r->action_status,
                'action_note'       => $r->action_note,
                'action_by'         => $r->action_by !== null ? (int) $r->action_by : null,
                'action_at'         => $r->action_at,
            ];
        }
        $barangays = [];
        foreach ($flagged as $i => $t) {
            $barangays[] = [
                'rank'          => $i + 1,
                'barangay_id'   => $t['barangay_id'],
                'barangay_name' => $t['barangay_name'],
                'tier'          => $t['tier'],
                'reasons'       => $t['reasons'],
                'current_cases' => $t['current_cases'],
                'active_cases'  => $t['active_cases'],
                'items'         => $byBarangay[$t['barangay_id']] ?? [],
            ];
        }
        // barangays no longer flagged but with recorded actions, kept for the record
        $flaggedIds = array_column($flagged, 'barangay_id');
        foreach ($byBarangay as $bid => $items) {
            if (!in_array($bid, $flaggedIds, true)) {
                $barangays[] = [
                    'rank' => null, 'barangay_id' => $bid,
                    'barangay_name' => DB::table('barangays')->where('barangay_id', $bid)->value('barangay_name'),
                    'tier' => 'Low', 'reasons' => [], 'current_cases' => null, 'active_cases' => null,
                    'items' => $items,
                ];
            }
        }

        return [
            'disease_code'        => $diseaseCode,
            'morbidity_year'      => $year,
            'morbidity_week'      => $week,
            'uses_fallback_rules' => $fallback,
            'draft_rules'         => $rules->where('status', 'Draft')->count(),
            'forecast_considered' => $risk['forecast_considered'],
            'barangays'           => $barangays,
        ];
    }

    /** Quantity for one rule, or null when CESU assesses it (or there is nothing to scale by). */
    public static function quantity(object $rule, int $activeCases, ?int $population): ?int
    {
        $f = $rule->quantity_factor !== null ? (float) $rule->quantity_factor : null;
        switch ($rule->scaling_basis) {
            case 'fixed':
                return $f !== null ? (int) ceil($f) : null;
            case 'per_case':
                return ($f !== null && $activeCases > 0) ? (int) ceil($f * $activeCases) : null;
            case 'per_1000_pop':
                return ($f !== null && $population) ? (int) ceil($f * $population / 1000) : null;
            default:
                return null;
        }
    }

    /** Confirmed + Probable cases per barangay in the 4 weeks ending with the selected week. */
    public static function activeCases(int $diseaseId, int $year, int $week): array
    {
        $d = new \DateTime();
        $d->setISODate($year, $week);
        $weeks = [];
        for ($i = 0; $i < self::WINDOW_WEEKS; $i++) {
            $weeks[] = [(int) $d->format('o'), (int) $d->format('W')];
            $d->modify('-7 days');
        }
        $q = DB::table('cases')->where('disease_id', $diseaseId)
            ->whereIn('case_classification', ['Confirmed', 'Probable'])
            ->where('status_flag', 'Active')
            ->where(function ($w) use ($weeks) {
                foreach ($weeks as [$y, $wk]) {
                    $w->orWhere(function ($x) use ($y, $wk) {
                        $x->where('morbidity_year', $y)->where('morbidity_week', $wk);
                    });
                }
            });
        return $q->groupBy('barangay_id')->selectRaw('barangay_id, COUNT(*) AS n')
            ->pluck('n', 'barangay_id')->map(function ($n) { return (int) $n; })->all();
    }
}
