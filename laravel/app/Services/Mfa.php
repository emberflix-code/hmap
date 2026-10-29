<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Crypt;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

/**
 * Multi-factor authentication for CESU staff (Ch.3 Module 9, Security a).
 *
 * The second factor is a time-based one-time password (TOTP, RFC 6238: SHA-1,
 * 6 digits, 30-second steps) from an authenticator app such as Google or
 * Microsoft Authenticator, so no SMS gateway is needed. Each enrolled user
 * also gets single-use recovery codes for a lost phone.
 *
 * A login session (the HRMO JWT, or the HRIS PHP session) counts as verified
 * once a correct code has been entered for it; HrmoSessionAuth checks this on
 * every request. Secrets are encrypted with the application key; recovery
 * codes are stored only as SHA-256 hashes.
 */
class Mfa
{
    const PERIOD = 30;
    const DIGITS = 6;
    const WINDOW = 1;            // accept the previous and next step (clock drift)
    const MAX_FAILURES = 5;      // per employee, then locked for LOCK_SECONDS
    const LOCK_SECONDS = 900;
    const RECOVERY_CODES = 8;
    const ISSUER = 'CESU Outbreak System';

    // ─── state ───────────────────────────────────────────────────────────

    public static function isEnrolled(int $employeeId): bool
    {
        return DB::table('user_mfa')
            ->where('employee_id', $employeeId)
            ->whereNotNull('confirmed_at')
            ->exists();
    }

    /** Cache key for one login session, from a hash of its credential. */
    public static function sessionKey(string $credential): string
    {
        return 'hmap:mfa_ok:' . hash('sha256', $credential);
    }

    /**
     * Verified for this session, and still enrolled: an Administrator reset
     * (hmap:mfa-reset) removes the enrollment and so ends verified sessions.
     */
    public static function sessionVerified(string $sessionKey, int $employeeId): bool
    {
        return (int) Cache::get($sessionKey) === $employeeId && self::isEnrolled($employeeId);
    }

    public static function markVerified(string $sessionKey, int $employeeId): void
    {
        Cache::put($sessionKey, $employeeId, (int) config('hmap.mfa.session_ttl'));
    }

    public static function forget(string $sessionKey): void
    {
        Cache::forget($sessionKey);
    }

    // ─── enrollment ──────────────────────────────────────────────────────

    /**
     * New secret for an employee who has not finished enrolling. Returns the
     * base32 secret and the otpauth:// URI the setup QR code encodes.
     */
    public static function startEnrollment(int $employeeId, string $accountName): array
    {
        // A pending secret from the last 10 minutes is reused, so a page
        // reload or a repeated request shows the same QR code as before.
        $pending = DB::table('user_mfa')->where('employee_id', $employeeId)
            ->whereNull('confirmed_at')->where('created_at', '>', now()->subMinutes(10))->first();
        if ($pending) {
            $secret = Crypt::decryptString($pending->secret_enc);
        } else {
            $secret = self::base32Encode(random_bytes(20));
            DB::table('user_mfa')->updateOrInsert(
                ['employee_id' => $employeeId],
                [
                    'secret_enc'     => Crypt::encryptString($secret),
                    'confirmed_at'   => null,
                    'last_used_step' => null,
                    'recovery_codes' => null,
                    'created_at'     => now(),
                ]
            );
        }

        $label = rawurlencode(self::ISSUER) . ':' . rawurlencode($accountName);
        $uri = 'otpauth://totp/' . $label . '?secret=' . $secret
            . '&issuer=' . rawurlencode(self::ISSUER)
            . '&algorithm=SHA1&digits=' . self::DIGITS . '&period=' . self::PERIOD;

        return ['secret' => $secret, 'otpauth_uri' => $uri];
    }

    /**
     * Confirm enrollment with the first code from the app. Returns the
     * plaintext recovery codes (shown once), or null if the code is wrong.
     */
    public static function confirmEnrollment(int $employeeId, string $code): ?array
    {
        $row = DB::table('user_mfa')->where('employee_id', $employeeId)
            ->whereNull('confirmed_at')->first();
        if (!$row || !self::checkTotp($row, $code)) {
            return null;
        }

        $codes = [];
        for ($i = 0; $i < self::RECOVERY_CODES; $i++) {
            $raw = self::base32Encode(random_bytes(5));   // 8 characters, 40 bits
            $codes[] = substr($raw, 0, 4) . '-' . substr($raw, 4, 4);
        }
        DB::table('user_mfa')->where('employee_id', $employeeId)->update([
            'confirmed_at'   => now(),
            'recovery_codes' => json_encode(array_map([self::class, 'hashRecovery'], $codes)),
        ]);
        return $codes;
    }

    // ─── verification ────────────────────────────────────────────────────

    /** 'totp' or 'recovery' when the code is accepted, otherwise null. */
    public static function verify(int $employeeId, string $code): ?string
    {
        $row = DB::table('user_mfa')->where('employee_id', $employeeId)
            ->whereNotNull('confirmed_at')->first();
        if (!$row) {
            return null;
        }
        if (self::checkTotp($row, $code)) {
            return 'totp';
        }

        // Recovery codes are longer than 6 digits; each works once.
        $hash = self::hashRecovery($code);
        $hashes = json_decode($row->recovery_codes ?? '[]', true) ?: [];
        $i = array_search($hash, $hashes, true);
        if ($i === false) {
            return null;
        }
        array_splice($hashes, $i, 1);
        DB::table('user_mfa')->where('employee_id', $employeeId)
            ->update(['recovery_codes' => json_encode($hashes)]);
        return 'recovery';
    }

    public static function recoveryCodesLeft(int $employeeId): int
    {
        $json = DB::table('user_mfa')->where('employee_id', $employeeId)->value('recovery_codes');
        return count(json_decode($json ?? '[]', true) ?: []);
    }

    /**
     * TOTP check against a user_mfa row. A code is accepted at most once:
     * last_used_step blocks replaying a code someone saw over a shoulder.
     */
    private static function checkTotp(object $row, string $code): bool
    {
        $code = preg_replace('/\s+/', '', $code);
        if (!preg_match('/^\d{' . self::DIGITS . '}$/', $code)) {
            return false;
        }
        $secret = self::base32Decode(Crypt::decryptString($row->secret_enc));
        $now = intdiv(time(), self::PERIOD);
        for ($step = $now - self::WINDOW; $step <= $now + self::WINDOW; $step++) {
            if ($row->last_used_step !== null && $step <= (int) $row->last_used_step) {
                continue;
            }
            if (hash_equals(self::totp($secret, $step), $code)) {
                DB::table('user_mfa')->where('employee_id', $row->employee_id)
                    ->update(['last_used_step' => $step]);
                return true;
            }
        }
        return false;
    }

    /** RFC 4226 HOTP value for one 30-second step. */
    public static function totp(string $secretBin, int $step): string
    {
        $hmac = hash_hmac('sha1', pack('J', $step), $secretBin, true);
        $offset = ord($hmac[19]) & 0x0f;
        $value = ((ord($hmac[$offset]) & 0x7f) << 24)
            | (ord($hmac[$offset + 1]) << 16)
            | (ord($hmac[$offset + 2]) << 8)
            | ord($hmac[$offset + 3]);
        return str_pad((string) ($value % (10 ** self::DIGITS)), self::DIGITS, '0', STR_PAD_LEFT);
    }

    // ─── attempt limit ───────────────────────────────────────────────────

    public static function lockedOut(int $employeeId): bool
    {
        return (int) Cache::get('hmap:mfa_fail:' . $employeeId, 0) >= self::MAX_FAILURES;
    }

    /** Count a wrong code; true when this failure triggers the lock. */
    public static function recordFailure(int $employeeId): bool
    {
        $key = 'hmap:mfa_fail:' . $employeeId;
        Cache::add($key, 0, self::LOCK_SECONDS);
        return Cache::increment($key) >= self::MAX_FAILURES;
    }

    public static function clearFailures(int $employeeId): void
    {
        Cache::forget('hmap:mfa_fail:' . $employeeId);
    }

    // ─── audit (RA 10173 Sec. 20) ────────────────────────────────────────

    public static function audit(int $employeeId, ?string $ip, string $action, array $detail = []): void
    {
        try {
            DB::table('audit_log')->insert([
                'employee_id'  => $employeeId,
                'action_type'  => $action,
                'target_table' => 'user_mfa',
                'target_id'    => $employeeId,
                'new_values'   => $detail ? json_encode($detail) : null,
                'ip_address'   => $ip,
            ]);
        } catch (\Throwable $e) {
            Log::warning("Could not write {$action} audit row: " . $e->getMessage());
        }
    }

    // ─── encoding ────────────────────────────────────────────────────────

    private static function hashRecovery(string $code): string
    {
        return hash('sha256', strtoupper(preg_replace('/[^A-Za-z0-9]/', '', $code)));
    }

    public static function base32Encode(string $bin): string
    {
        $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        $bits = '';
        foreach (str_split($bin) as $c) {
            $bits .= str_pad(decbin(ord($c)), 8, '0', STR_PAD_LEFT);
        }
        $out = '';
        foreach (str_split($bits, 5) as $chunk) {
            $out .= $alphabet[bindec(str_pad($chunk, 5, '0'))];
        }
        return $out;
    }

    public static function base32Decode(string $b32): string
    {
        $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        $bits = '';
        foreach (str_split(strtoupper(rtrim($b32, '='))) as $c) {
            $bits .= str_pad(decbin(strpos($alphabet, $c)), 5, '0', STR_PAD_LEFT);
        }
        $out = '';
        foreach (str_split($bits, 8) as $byte) {
            if (strlen($byte) === 8) {
                $out .= chr(bindec($byte));
            }
        }
        return $out;
    }
}
