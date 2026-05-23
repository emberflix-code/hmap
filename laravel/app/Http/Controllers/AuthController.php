<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Cookie;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * H-MAP auth shim in front of the HRMO REST API (POST /api/v1/auth/login,
 * GET /api/v1/auth/me, POST /api/v1/auth/logout).
 *
 * Flow:
 *   1. Browser POSTs username+password to /api/auth/login on H-MAP
 *   2. H-MAP forwards to HRMO /api/v1/auth/login
 *   3. On success H-MAP sets the HRMO-issued JWT in an HttpOnly cookie
 *      (`hmap_jwt`) so it can't be exfiltrated by XSS
 *   4. Every subsequent H-MAP API call goes through HrmoSessionAuth,
 *      which reads the cookie and calls /auth/me to resolve the user
 */
class AuthController extends Controller
{
    public function login(Request $request): JsonResponse
    {
        $data = $request->validate([
            'username' => 'required|string|max:80',
            'password' => 'required|string|max:200',
        ]);

        $base = config('hmap.hrmo.api_base');
        try {
            $resp = Http::timeout(10)
                ->acceptJson()
                ->asJson()
                ->post($base . '/auth/login', $data);
        } catch (\Throwable $e) {
            Log::warning('HRMO /auth/login unreachable: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'HRMO authentication service is unreachable.',
            ], 503);
        }

        $body = $resp->json();
        if (!$resp->successful() || empty($body['access_token'])) {
            return response()->json([
                'success' => false,
                'message' => $body['message'] ?? 'Invalid username or password',
            ], $resp->status() ?: 401);
        }

        $token = $body['access_token'];
        $ttlMinutes = isset($body['expires_in']) ? max(1, (int) ($body['expires_in'] / 60)) : 60;
        $cookieName = config('hmap.hrmo.jwt_cookie');

        // HttpOnly so JS can't read the JWT; Secure because the app runs on HTTPS;
        // SameSite=Lax so navigation from links still carries the cookie.
        $cookie = Cookie::make(
            $cookieName,
            $token,
            $ttlMinutes,
            '/',           // path
            null,          // domain — default to current host
            $request->isSecure(),  // secure
            true,          // httpOnly
            false,         // raw
            'lax'          // sameSite
        );

        return response()->json([
            'success' => true,
            'user'    => $body['user'] ?? null,
        ])->withCookie($cookie);
    }

    public function me(Request $request): JsonResponse
    {
        // The HrmoSessionAuth middleware already validated and attached the
        // user on success, so we just echo what it attached.
        return response()->json([
            'employee_id'   => $request->attributes->get('hmap.employee_id'),
            'employee_name' => $request->attributes->get('hmap.employee_name'),
            'role'          => $request->attributes->get('hmap.role'),
        ]);
    }

    public function logout(Request $request): JsonResponse
    {
        $cookieName = config('hmap.hrmo.jwt_cookie');
        $token = $request->cookie($cookieName);
        $base = config('hmap.hrmo.api_base');

        // Best-effort logout on HRMO so the token is server-side invalidated.
        // Don't block the client response on this — if HRMO is unreachable
        // we still want to clear the local cookie.
        if ($token) {
            Cache::forget('hmap:hrmo_me:' . hash('sha256', $token));
            try {
                Http::timeout(3)
                    ->withToken($token)
                    ->acceptJson()
                    ->post($base . '/auth/logout');
            } catch (\Throwable $e) {
                Log::info('HRMO /auth/logout best-effort failed: ' . $e->getMessage());
            }
        }

        return response()
            ->json(['success' => true])
            ->withCookie(Cookie::forget($cookieName));
    }
}
