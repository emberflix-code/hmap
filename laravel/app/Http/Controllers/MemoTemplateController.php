<?php

namespace App\Http\Controllers;

use App\Services\MemoTemplate;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * The weekly dengue memo template, maintained by the Administrator.
 *
 *   GET  /admin/memo-template            current template, placeholders, default
 *   POST /admin/memo-template/preview    fill a template (unsaved) with a week's data
 *   PUT  /admin/memo-template            save
 *   POST /admin/memo-template/reset      go back to the built-in default
 *
 * Every save and reset is written to audit_log with the old and new text.
 */
class MemoTemplateController extends Controller
{
    public function show(): JsonResponse
    {
        $row = MemoTemplate::saved();
        return response()->json([
            'body'         => $row ? $row->body : MemoTemplate::DEFAULT,
            'is_default'   => $row === null,
            'updated_at'   => $row->updated_at ?? null,
            'updated_by'   => $row->updated_by ?? null,
            'default'      => MemoTemplate::DEFAULT,
            'placeholders' => collect(MemoTemplate::PLACEHOLDERS)
                ->map(function ($desc, $key) { return ['key' => $key, 'description' => $desc]; })->values(),
        ]);
    }

    public function preview(Request $request, DashboardController $dashboard): JsonResponse
    {
        $data = $request->validate([
            'body' => 'required|string|max:20000',
            'year' => 'required|integer|min:2010|max:2100',
            'week' => 'required|integer|min:1|max:53',
        ]);
        return response()->json([
            'memo'    => MemoTemplate::render($data['body'], $dashboard->memoValues((int) $data['year'], (int) $data['week'])),
            'unknown' => MemoTemplate::unknownPlaceholders($data['body']),
        ]);
    }

    public function update(Request $request): JsonResponse
    {
        $body = $request->validate(['body' => 'required|string|max:20000'])['body'];
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $old = MemoTemplate::body();
        DB::table('memo_templates')->updateOrInsert(['template_key' => MemoTemplate::KEY], [
            'body' => $body, 'updated_by' => $employeeId, 'updated_at' => now(),
        ]);
        $this->audit($employeeId, 'MEMO_TEMPLATE_UPDATE', $old, $body, $request->ip());
        return response()->json(['success' => true, 'unknown' => MemoTemplate::unknownPlaceholders($body)]);
    }

    public function reset(Request $request): JsonResponse
    {
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $old = MemoTemplate::body();
        DB::table('memo_templates')->where('template_key', MemoTemplate::KEY)->delete();
        $this->audit($employeeId, 'MEMO_TEMPLATE_RESET', $old, MemoTemplate::DEFAULT, $request->ip());
        return response()->json(['success' => true, 'body' => MemoTemplate::DEFAULT]);
    }

    private function audit(int $employeeId, string $action, string $old, string $new, ?string $ip): void
    {
        DB::table('audit_log')->insert([
            'employee_id'  => $employeeId,
            'action_type'  => $action,
            'target_table' => 'memo_templates',
            'old_values'   => json_encode(['body' => $old]),
            'new_values'   => json_encode(['body' => $new]),
            'ip_address'   => $ip,
        ]);
    }
}
