<?php

namespace App\Http\Controllers;

use App\Services\Mfa;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Second login step (Module 9). These routes run under `hrmo:mfa-pending`:
 * the HRMO password and the CESU authorization check have already passed,
 * but the session has not yet entered a one-time code.
 *
 *   GET  /auth/mfa/status          enrolled? verified?
 *   POST /auth/mfa/enroll          first login: new secret + QR code URI
 *   POST /auth/mfa/enroll/confirm  first code from the app → recovery codes
 *   POST /auth/mfa/verify          every later login: app code or recovery code
 */
class MfaController extends Controller
{
    public function status(Request $request): JsonResponse
    {
        $id = $this->employeeId($request);
        return response()->json([
            'enrolled' => Mfa::isEnrolled($id),
            'verified' => Mfa::sessionVerified($request->attributes->get('hmap.mfa_session'), $id),
        ]);
    }

    public function enroll(Request $request): JsonResponse
    {
        $id = $this->employeeId($request);
        if (Mfa::isEnrolled($id)) {
            return response()->json([
                'error'  => 'already_enrolled',
                'detail' => 'An authenticator is already set up. Ask the CESU Administrator '
                    . 'to reset it if you no longer have it.',
            ], 409);
        }
        $name = (string) $request->attributes->get('hmap.employee_name');
        return response()->json(Mfa::startEnrollment($id, $name ?: 'employee ' . $id));
    }

    public function confirm(Request $request): JsonResponse
    {
        $code = $request->validate(['code' => 'required|string|max:20'])['code'];
        $id = $this->employeeId($request);
        if ($locked = $this->lockedResponse($id)) {
            return $locked;
        }

        $recovery = Mfa::confirmEnrollment($id, $code);
        if ($recovery === null) {
            return $this->wrongCode($request, $id, 'enrollment');
        }

        Mfa::clearFailures($id);
        Mfa::markVerified($request->attributes->get('hmap.mfa_session'), $id);
        Mfa::audit($id, $request->ip(), 'MFA_ENROLLED');
        return response()->json(['success' => true, 'recovery_codes' => $recovery]);
    }

    public function verify(Request $request): JsonResponse
    {
        $code = $request->validate(['code' => 'required|string|max:20'])['code'];
        $id = $this->employeeId($request);
        if ($locked = $this->lockedResponse($id)) {
            return $locked;
        }

        $method = Mfa::verify($id, $code);
        if ($method === null) {
            return $this->wrongCode($request, $id, 'login');
        }

        Mfa::clearFailures($id);
        Mfa::markVerified($request->attributes->get('hmap.mfa_session'), $id);
        $left = Mfa::recoveryCodesLeft($id);
        if ($method === 'recovery') {
            Mfa::audit($id, $request->ip(), 'MFA_RECOVERY_USED', ['codes_left' => $left]);
        } else {
            Mfa::audit($id, $request->ip(), 'MFA_VERIFIED');
        }
        return response()->json([
            'success'              => true,
            'method'               => $method,
            'recovery_codes_left'  => $left,
        ]);
    }

    private function employeeId(Request $request): int
    {
        return (int) $request->attributes->get('hmap.employee_id');
    }

    private function lockedResponse(int $id): ?JsonResponse
    {
        if (!Mfa::lockedOut($id)) {
            return null;
        }
        return response()->json([
            'error'  => 'mfa_locked',
            'detail' => 'Too many wrong codes. Wait 15 minutes, then try again.',
        ], 429);
    }

    private function wrongCode(Request $request, int $id, string $step): JsonResponse
    {
        $nowLocked = Mfa::recordFailure($id);
        Mfa::audit($id, $request->ip(), $nowLocked ? 'MFA_LOCKED' : 'MFA_FAILED', ['step' => $step]);
        if ($nowLocked) {
            return $this->lockedResponse($id);
        }
        return response()->json([
            'error'  => 'invalid_code',
            'detail' => 'That code is not valid. Check that your phone\'s time is set automatically.',
        ], 422);
    }
}
