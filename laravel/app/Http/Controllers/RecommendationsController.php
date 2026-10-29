<?php

namespace App\Http\Controllers;

use App\Services\Recommender;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * Resource allocation recommendations and their rule table (Ch.3 Module 6).
 *
 *   GET  /recommendations?disease_code=&year=&week=   Analyst+  ranked list for one week
 *   POST /recommendations/{id}/action                 Analyst+  record Acted / Not acted
 *   GET  /recommendation-rules                        Analyst+  the rule table
 *   POST /recommendation-rules                        Administrator  add a rule
 *   PUT  /recommendation-rules/{id}                   Administrator  edit or deactivate
 *   POST /recommendation-rules/{id}/validate          Administrator  mark as CESU-validated
 *
 * Rules are never deleted (generated recommendations refer to them); they
 * are deactivated instead. Editing a rule's content returns it to Draft.
 * Every action and rule change is written to audit_log.
 */
class RecommendationsController extends Controller
{
    private const CONTENT_FIELDS = ['disease_id', 'risk_tier', 'category', 'item', 'scaling_basis',
                                    'quantity_factor', 'unit', 'source'];

    public function index(Request $request): JsonResponse
    {
        $q = $request->validate([
            'disease_code' => 'required|string|max:20',
            'year'         => 'required|integer|min:2010|max:2100',
            'week'         => 'required|integer|min:1|max:53',
        ]);
        $result = Recommender::generate($q['disease_code'], (int) $q['year'], (int) $q['week']);
        if ($result === null) {
            return response()->json(['error' => 'unknown_disease'], 404);
        }
        return response()->json($result);
    }

    public function action(Request $request, int $id): JsonResponse
    {
        $data = $request->validate([
            'action_status' => 'required|in:Pending,Acted,Not acted',
            'action_note'   => 'nullable|string|max:500',
        ]);
        $row = DB::table('recommendations')->where('recommendation_id', $id)->first();
        if (!$row) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $new = [
            'action_status' => $data['action_status'],
            'action_note'   => $data['action_note'] ?? null,
            'action_by'     => $data['action_status'] === 'Pending' ? null : $employeeId,
            'action_at'     => $data['action_status'] === 'Pending' ? null : now(),
        ];
        DB::table('recommendations')->where('recommendation_id', $id)->update($new);
        $this->audit($employeeId, 'RECOMMENDATION_ACTION', 'recommendations', $id,
            ['action_status' => $row->action_status, 'action_note' => $row->action_note],
            ['action_status' => $new['action_status'], 'action_note' => $new['action_note']],
            $request->ip());
        return response()->json(['success' => true] + $new);
    }

    public function rules(): JsonResponse
    {
        $rows = DB::table('recommendation_rules as r')
            ->leftJoin('diseases as d', 'd.disease_id', '=', 'r.disease_id')
            ->orderByRaw('d.display_order IS NULL, d.display_order')
            ->orderByRaw("CASE r.risk_tier WHEN 'Moderate' THEN 0 ELSE 1 END")
            ->orderBy('r.priority')->orderBy('r.rule_id')
            ->get(['r.*', 'd.disease_code', 'd.disease_name']);
        return response()->json($rows);
    }

    public function storeRule(Request $request): JsonResponse
    {
        $data = $this->ruleInput($request);
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $id = DB::table('recommendation_rules')->insertGetId($data + [
            'status' => 'Draft', 'updated_by' => $employeeId, 'updated_at' => now(),
        ]);
        $this->audit($employeeId, 'RULE_CREATE', 'recommendation_rules', $id, null, $data, $request->ip());
        return response()->json(DB::table('recommendation_rules')->where('rule_id', $id)->first(), 201);
    }

    public function updateRule(Request $request, int $id): JsonResponse
    {
        $old = DB::table('recommendation_rules')->where('rule_id', $id)->first();
        if (!$old) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $data = $this->ruleInput($request, true);
        $employeeId = (int) $request->attributes->get('hmap.employee_id');

        $contentChanged = false;
        foreach (self::CONTENT_FIELDS as $f) {
            if (array_key_exists($f, $data) && (string) $data[$f] !== (string) $old->$f) {
                $contentChanged = true;
            }
        }
        $update = $data + ['updated_by' => $employeeId, 'updated_at' => now()];
        if ($contentChanged) {
            $update += ['status' => 'Draft', 'validated_by' => null, 'validated_at' => null];
        }
        DB::table('recommendation_rules')->where('rule_id', $id)->update($update);

        $oldValues = array_intersect_key((array) $old, $data);
        $this->audit($employeeId, 'RULE_UPDATE', 'recommendation_rules', $id, $oldValues, $data, $request->ip());
        return response()->json(DB::table('recommendation_rules')->where('rule_id', $id)->first());
    }

    public function validateRule(Request $request, int $id): JsonResponse
    {
        $old = DB::table('recommendation_rules')->where('rule_id', $id)->first();
        if (!$old) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        DB::table('recommendation_rules')->where('rule_id', $id)->update([
            'status' => 'Validated', 'validated_by' => $employeeId, 'validated_at' => now(),
        ]);
        $this->audit($employeeId, 'RULE_VALIDATE', 'recommendation_rules', $id,
            ['status' => $old->status], ['status' => 'Validated'], $request->ip());
        return response()->json(DB::table('recommendation_rules')->where('rule_id', $id)->first());
    }

    private function ruleInput(Request $request, bool $partial = false): array
    {
        $req = $partial ? 'sometimes|' : 'required|';
        $data = $request->validate([
            'disease_id'      => 'nullable|integer|exists:diseases,disease_id',
            'risk_tier'       => $req . 'in:Moderate,High',
            'category'        => $req . 'in:Team,Supply,Medicine,IEC',
            'item'            => $req . 'string|max:200',
            'scaling_basis'   => $req . 'in:fixed,per_case,per_1000_pop,as_assessed',
            'quantity_factor' => 'nullable|numeric|min:0|max:999999',
            'unit'            => 'nullable|string|max:40',
            'priority'        => 'sometimes|integer|min:0|max:255',
            'source'          => $req . 'string|max:255',
            'notes'           => 'nullable|string|max:500',
            'is_active'       => 'sometimes|boolean',
        ]);
        if (isset($data['scaling_basis']) && $data['scaling_basis'] !== 'as_assessed'
            && !isset($data['quantity_factor']) && !$partial) {
            abort(response()->json([
                'message' => 'A quantity factor is required unless the basis is as_assessed.',
                'errors'  => ['quantity_factor' => ['Required for this scaling basis.']],
            ], 422));
        }
        return $data;
    }

    private function audit(int $employeeId, string $action, string $table, int $targetId,
                           ?array $oldValues, ?array $newValues, ?string $ip): void
    {
        DB::table('audit_log')->insert([
            'employee_id'  => $employeeId,
            'action_type'  => $action,
            'target_table' => $table,
            'target_id'    => $targetId,
            'old_values'   => $oldValues ? json_encode($oldValues) : null,
            'new_values'   => $newValues ? json_encode($newValues) : null,
            'ip_address'   => $ip,
        ]);
    }
}
