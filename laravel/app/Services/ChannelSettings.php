<?php

namespace App\Services;

use Illuminate\Support\Facades\Crypt;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

/**
 * Email and SMS settings the CESU Administrator maintains from the dashboard,
 * following the HRIS Portal's module_smtp_config / module_sms_config design.
 *
 *   email  host, port, encryption (tls|ssl|none), username, password,
 *          from_email, from_name
 *   sms    base_url, client_id, client_secret, department_code
 *          (Paranaque SMS API, app.paranaque.gov.ph/sms-api)
 *
 * Each channel's settings are stored as one JSON object encrypted with the
 * APP_KEY. The API never returns the password or client secret. Saving with
 * a blank secret keeps the stored one, so an Administrator can change the
 * host without retyping the password.
 */
class ChannelSettings
{
    const FIELDS = [
        'email' => ['host', 'port', 'encryption', 'username', 'password', 'from_email', 'from_name'],
        'sms'   => ['base_url', 'client_id', 'client_secret', 'department_code'],
    ];
    const SECRETS = ['password', 'client_secret'];
    const DEFAULTS = [
        'email' => ['port' => 587, 'encryption' => 'tls', 'from_name' => 'CESU Disease Surveillance'],
        'sms'   => ['base_url' => 'https://app.paranaque.gov.ph/sms-api/public'],
    ];

    /** Active settings for a channel, or null when not set up or switched off. */
    public static function active(string $channel): ?array
    {
        $row = DB::table('channel_settings')->where('channel', $channel)->first();
        if (!$row || !$row->is_active) {
            return null;
        }
        return self::decrypt($row->settings_enc);
    }

    /** For the settings screen: every field except the secrets, plus whether each secret is set. */
    public static function forDisplay(string $channel): array
    {
        $row = DB::table('channel_settings')->where('channel', $channel)->first();
        $s = $row ? self::decrypt($row->settings_enc) : self::DEFAULTS[$channel];
        $out = ['is_active' => $row ? (bool) $row->is_active : false, 'updated_at' => $row->updated_at ?? null];
        foreach (self::FIELDS[$channel] as $f) {
            if (in_array($f, self::SECRETS, true)) {
                $out[$f . '_set'] = !empty($s[$f]);
            } else {
                $out[$f] = $s[$f] ?? null;
            }
        }
        return $out;
    }

    /** Save submitted fields; a blank secret keeps the stored one. Returns the changed field names. */
    public static function save(string $channel, array $input, bool $isActive, int $employeeId): array
    {
        $row = DB::table('channel_settings')->where('channel', $channel)->first();
        $current = $row ? self::decrypt($row->settings_enc) : self::DEFAULTS[$channel];
        $next = $current;
        foreach (self::FIELDS[$channel] as $f) {
            if (!array_key_exists($f, $input)) {
                continue;
            }
            if (in_array($f, self::SECRETS, true) && ($input[$f] === null || $input[$f] === '')) {
                continue;
            }
            $next[$f] = $input[$f];
        }
        $changed = [];
        foreach (self::FIELDS[$channel] as $f) {
            if (($current[$f] ?? null) !== ($next[$f] ?? null)) {
                $changed[] = $f;
            }
        }
        if ($row && (bool) $row->is_active !== $isActive) {
            $changed[] = 'is_active';
        }
        DB::table('channel_settings')->updateOrInsert(['channel' => $channel], [
            'settings_enc' => Crypt::encryptString(json_encode($next)),
            'is_active'    => $isActive ? 1 : 0,
            'updated_by'   => $employeeId,
            'updated_at'   => now(),
        ]);
        return $changed;
    }

    private static function decrypt(string $enc): array
    {
        try {
            return json_decode(Crypt::decryptString($enc), true) ?: [];
        } catch (\Throwable $e) {
            // APP_KEY changed since the settings were saved: treat as not configured
            Log::warning('channel_settings could not be decrypted: ' . $e->getMessage());
            return [];
        }
    }
}
