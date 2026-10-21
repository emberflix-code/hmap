<?php

namespace App\Services;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

/**
 * CESU-only access gate.
 *
 * An active HRMO account proves the user is a current city employee, but only
 * CESU personnel listed in hmap_db.user_roles (is_active = 1) may use the
 * system. The role always comes from user_roles, never from the HRMO role, so
 * the CESU Administrator alone decides who gets in and at what level.
 */
class CesuAccess
{
    /**
     * Role of an authorized CESU staff member, or null if the employee is not
     * on the authorization list (or has been deactivated).
     */
    public static function roleFor(int $employeeId): ?string
    {
        return DB::table('user_roles')
            ->where('employee_id', $employeeId)
            ->where('is_active', 1)
            ->value('role');
    }

    /**
     * Record a refused login or request in the audit log (RA 10173 Sec. 20).
     * Never throws: a logging failure must not turn a denial into an error page.
     */
    public static function logDenied(int $employeeId, ?string $ip, string $reason): void
    {
        try {
            DB::table('audit_log')->insert([
                'employee_id'  => $employeeId,
                'action_type'  => 'ACCESS_DENIED',
                'target_table' => 'user_roles',
                'new_values'   => json_encode(['reason' => $reason]),
                'ip_address'   => $ip,
            ]);
        } catch (\Throwable $e) {
            Log::warning('Could not write ACCESS_DENIED audit row: ' . $e->getMessage());
        }
    }
}
