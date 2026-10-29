<?php

namespace App\Http\Controllers;

use App\Services\Mfa;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * The CESU staff authorization list (user_roles), maintained by the
 * Administrator (Ch.3 Module 9: "manages users, roles").
 *
 *   GET  /admin/staff                      everyone on the list, with MFA status
 *   POST /admin/staff                      add (or reactivate) an employee with a role
 *   PUT  /admin/staff/{employeeId}         change name, role, or active flag
 *   POST /admin/staff/{employeeId}/reset-mfa   remove a lost authenticator
 *
 * An HRMO account alone grants nothing: only employees on this list can sign
 * in, at the role given here. Two rules prevent a lock-out: an Administrator
 * cannot demote or deactivate themselves, and the last active Administrator
 * cannot be removed. The very first Administrator is added directly in the
 * database (docs/DEPLOYMENT.md). Every change is written to audit_log.
 */
class StaffController extends Controller
{
    private const ROLES = ['Encoder', 'Analyst', 'Administrator'];

    public function index(): JsonResponse
    {
        $enrolled = DB::table('user_mfa')->whereNotNull('confirmed_at')->pluck('employee_id')->flip();
        $lastSignIn = DB::table('audit_log')->whereIn('action_type', ['MFA_VERIFIED', 'MFA_RECOVERY_USED', 'MFA_ENROLLED'])
            ->groupBy('employee_id')->selectRaw('employee_id, MAX(action_at) AS at')->pluck('at', 'employee_id');
        $rows = DB::table('user_roles')->orderByDesc('is_active')->orderBy('full_name')->orderBy('employee_id')->get()
            ->map(function ($r) use ($enrolled, $lastSignIn) {
                return [
                    'employee_id'  => (int) $r->employee_id,
                    'full_name'    => $r->full_name,
                    'role'         => $r->role,
                    'is_active'    => (bool) $r->is_active,
                    'assigned_by'  => $r->assigned_by !== null ? (int) $r->assigned_by : null,
                    'assigned_at'  => $r->assigned_at,
                    'mfa_enrolled' => isset($enrolled[$r->employee_id]),
                    'last_sign_in' => $lastSignIn[$r->employee_id] ?? null,
                ];
            });
        return response()->json($rows);
    }

    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'employee_id' => 'required|integer|min:1|max:4294967295',
            'full_name'   => 'nullable|string|max:120',
            'role'        => 'required|in:' . implode(',', self::ROLES),
        ]);
        $me = (int) $request->attributes->get('hmap.employee_id');
        $existing = DB::table('user_roles')->where('employee_id', $data['employee_id'])->first();
        if ($existing && $existing->is_active) {
            return response()->json(['message' => 'This employee is already on the list.',
                                     'errors' => ['employee_id' => ['Already authorized; change the role instead.']]], 422);
        }
        $row = [
            'full_name'   => $data['full_name'] ?? ($existing->full_name ?? null),
            'role'        => $data['role'],
            'is_active'   => 1,
            'assigned_by' => $me,
            'assigned_at' => now(),
        ];
        DB::table('user_roles')->updateOrInsert(['employee_id' => $data['employee_id']], $row);
        $this->audit($me, $existing ? 'STAFF_REACTIVATE' : 'STAFF_ADD', (int) $data['employee_id'],
            $existing ? ['role' => $existing->role, 'is_active' => 0] : null,
            ['role' => $row['role'], 'full_name' => $row['full_name']], $request->ip());
        return response()->json(['success' => true], 201);
    }

    public function update(Request $request, int $employeeId): JsonResponse
    {
        $data = $request->validate([
            'full_name' => 'sometimes|nullable|string|max:120',
            'role'      => 'sometimes|in:' . implode(',', self::ROLES),
            'is_active' => 'sometimes|boolean',
        ]);
        $old = DB::table('user_roles')->where('employee_id', $employeeId)->first();
        if (!$old) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $me = (int) $request->attributes->get('hmap.employee_id');
        $losesAdmin = $old->role === 'Administrator' && $old->is_active
            && ((isset($data['role']) && $data['role'] !== 'Administrator')
                || (array_key_exists('is_active', $data) && !$data['is_active']));
        if ($losesAdmin && $employeeId === $me) {
            return $this->refuse('You cannot remove your own Administrator access. Ask another Administrator.');
        }
        if ($losesAdmin && DB::table('user_roles')->where('role', 'Administrator')->where('is_active', 1)->count() <= 1) {
            return $this->refuse('At least one active Administrator must remain.');
        }

        $changes = array_intersect_key($data, array_flip(['full_name', 'role', 'is_active']));
        if (array_key_exists('is_active', $changes)) {
            $changes['is_active'] = $changes['is_active'] ? 1 : 0;
        }
        DB::table('user_roles')->where('employee_id', $employeeId)->update($changes);
        $this->audit($me, 'STAFF_UPDATE', $employeeId, array_intersect_key((array) $old, $changes), $changes, $request->ip());
        return response()->json(['success' => true]);
    }

    public function resetMfa(Request $request, int $employeeId): JsonResponse
    {
        if (!DB::table('user_roles')->where('employee_id', $employeeId)->exists()) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $me = (int) $request->attributes->get('hmap.employee_id');
        $done = Mfa::reset($employeeId, $me, $request->ip());
        return response()->json([
            'success' => $done,
            'message' => $done ? 'Authenticator removed. The employee sets it up again at next sign-in.'
                               : 'This employee has no authenticator set up.',
        ]);
    }

    private function refuse(string $message): JsonResponse
    {
        return response()->json(['message' => $message, 'errors' => ['role' => [$message]]], 422);
    }

    private function audit(int $employeeId, string $action, int $targetId, ?array $old, ?array $new, ?string $ip): void
    {
        DB::table('audit_log')->insert([
            'employee_id'  => $employeeId,
            'action_type'  => $action,
            'target_table' => 'user_roles',
            'target_id'    => $targetId,
            'old_values'   => $old ? json_encode($old) : null,
            'new_values'   => $new ? json_encode($new) : null,
            'ip_address'   => $ip,
        ]);
    }
}
