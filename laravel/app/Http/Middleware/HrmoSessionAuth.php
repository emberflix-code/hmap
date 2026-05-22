<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Symfony\Component\HttpFoundation\Response;

/**
 * Verifies the incoming request belongs to an active Parañaque City employee
 * by reading either a stub config (dev) or the HRIS Portal's PHP session (prod).
 *
 * On success it attaches three attributes to the request for downstream code:
 *   - hmap.employee_id
 *   - hmap.employee_name
 *   - hmap.role        ('Encoder' | 'Analyst' | 'Administrator')
 *
 * On failure: 401 with a JSON body for /api/*, redirect to HRIS login otherwise.
 */
class HrmoSessionAuth
{
    public function handle(Request $request, Closure $next, ?string $minRole = null): Response
    {
        $config = config('hmap.hrmo');

        $user = match ($config['mode']) {
            'stub'  => $this->resolveStub($config),
            'php'   => $this->resolvePhpSession($request, $config),
            default => null,
        };

        if (!$user) {
            return $this->unauthorized($request);
        }

        // Optional role gate per route (Encoder < Analyst < Administrator)
        if ($minRole && !$this->roleMeets($user['role'], $minRole)) {
            return response()->json([
                'error' => 'forbidden',
                'detail' => "Requires role {$minRole}; you are {$user['role']}",
            ], 403);
        }

        $request->attributes->set('hmap.employee_id', $user['employee_id']);
        $request->attributes->set('hmap.employee_name', $user['name']);
        $request->attributes->set('hmap.role', $user['role']);

        return $next($request);
    }

    private function resolveStub(array $config): ?array
    {
        return [
            'employee_id' => $config['stub_user_id'],
            'name' => $config['stub_user_name'],
            'role' => $config['stub_user_role'],
        ];
    }

    private function resolvePhpSession(Request $request, array $config): ?array
    {
        $sessionId = $request->cookie($config['session_cookie']);
        if (!$sessionId || !preg_match('/^[A-Za-z0-9,-]+$/', $sessionId)) {
            return null;
        }

        // Read the HRIS Portal's PHP session file directly. We never write to
        // it — H-MAP is a session reader, per docs/architecture.md.
        session_save_path($config['session_save_path']);
        session_id($sessionId);
        @session_start();
        $employeeId = $_SESSION['user_id'] ?? null;
        session_write_close();

        if (!$employeeId) {
            return null;
        }

        // Verify the employee is still active in the HRIS portal's users table
        // (read-only access via the hmap_app grant on hrmo_evaluation_db.users).
        try {
            $row = DB::connection('hrmo')->table('users')
                ->where('id', $employeeId)
                ->where('status', 'ACTIVE')
                ->first(['id', 'full_name', 'email']);
        } catch (\Throwable $e) {
            // hrmo connection not configured locally — treat as auth failure
            return null;
        }

        if (!$row) {
            return null;
        }

        $role = DB::table('user_roles')
            ->where('employee_id', $employeeId)
            ->where('is_active', 1)
            ->value('role') ?? 'Encoder';

        return [
            'employee_id' => $employeeId,
            'name' => $row->full_name,
            'role' => $role,
        ];
    }

    private function roleMeets(string $actual, string $required): bool
    {
        $levels = ['Encoder' => 1, 'Analyst' => 2, 'Administrator' => 3];
        return ($levels[$actual] ?? 0) >= ($levels[$required] ?? 0);
    }

    private function unauthorized(Request $request): Response
    {
        if ($request->is('api/*') || $request->wantsJson()) {
            return response()->json([
                'error' => 'unauthorized',
                'detail' => 'No active HRMO session. Sign in via the HRIS Portal.',
            ], 401);
        }
        // Production HRIS portal login. In dev with stub mode the middleware
        // shouldn't normally reach here at all.
        return redirect('/hris/login?return=' . urlencode($request->fullUrl()));
    }
}
