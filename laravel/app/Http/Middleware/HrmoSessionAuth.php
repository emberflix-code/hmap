<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
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

        switch ($config['mode']) {
            case 'stub':
                $user = $this->resolveStub($config);
                break;
            case 'php':
                $user = $this->resolvePhpSession($request, $config);
                break;
            case 'jwt':
                $user = $this->resolveJwt($request, $config);
                break;
            default:
                $user = null;
        }

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

    /**
     * Bearer-token auth via HRMO's JWT API. The token is read from
     * (in priority order):
     *   1. The `hmap_jwt` HttpOnly cookie that AuthController issues on login
     *   2. The Authorization: Bearer header (for direct API clients/tests)
     *
     * Each token's user payload is cached for `me_cache_ttl` seconds so we
     * don't hammer HRMO on every dashboard XHR.
     */
    private function resolveJwt(Request $request, array $config): ?array
    {
        $token = $request->cookie($config['jwt_cookie'])
            ?: $this->bearerFromHeader($request);
        if (!$token) {
            return null;
        }

        // Cache key uses a short hash of the token so we never log the
        // raw JWT (it would be a credential leak).
        $cacheKey = 'hmap:hrmo_me:' . hash('sha256', $token);
        $cached = Cache::get($cacheKey);
        if ($cached) {
            return $cached;
        }

        try {
            $resp = Http::timeout(5)
                ->withToken($token)
                ->acceptJson()
                ->get($config['api_base'] . '/auth/me');
        } catch (\Throwable $e) {
            Log::warning('HRMO /auth/me unreachable: ' . $e->getMessage());
            return null;
        }

        if (!$resp->successful()) {
            // 401/403 = stale token; anything else = upstream problem worth logging
            if ($resp->status() >= 500) {
                Log::warning('HRMO /auth/me returned ' . $resp->status());
            }
            return null;
        }

        $body = $resp->json();
        $payload = $body['user'] ?? null;
        if (!$payload || empty($payload['id'])) {
            return null;
        }

        $hmapUser = [
            'employee_id' => (int) $payload['id'],
            'name'        => $payload['full_name'] ?? $payload['username'] ?? 'HRMO user',
            'role'        => $this->mapHrmoRole($payload['role'] ?? null, $config),
        ];

        Cache::put($cacheKey, $hmapUser, $config['me_cache_ttl']);
        return $hmapUser;
    }

    private function bearerFromHeader(Request $request): ?string
    {
        $h = $request->header('Authorization', '');
        if (preg_match('/^Bearer\s+(.+)$/i', $h, $m)) {
            return trim($m[1]);
        }
        return null;
    }

    private function mapHrmoRole(?string $hrmoRole, array $config): string
    {
        if ($hrmoRole === null || $hrmoRole === '') {
            return $config['default_role'];
        }
        $map = $config['role_map'] ?? [];
        return $map[strtolower($hrmoRole)] ?? $config['default_role'];
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
