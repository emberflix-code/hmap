<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;

/**
 * SMS channel for outbreak notifications (Module 7).
 *
 * When the Administrator has saved and switched on SMS settings
 * (ChannelSettings 'sms'), messages go through the Paranaque SMS API, the
 * same gateway the HRIS Portal uses:
 *   POST {base_url}/oauth/token        client_credentials → bearer token (cached)
 *   POST {base_url}/api/v1/send-sms    {mobile, message, department_code, requestor}
 * A rejected cached token (401) is replaced and the send retried once.
 * Success is HTTP 2xx with "error": false in the body.
 *
 * Otherwise the .env driver applies:
 *   none  every SMS is recorded as 'skipped' (no gateway). The delivery log
 *         never claims a message was sent when it was not.
 *   http  JSON POST to HMAP_SMS_HTTP_URL with a Bearer token; field names are
 *         configurable. Any 2xx = sent.
 */
class SmsSender
{
    /** @return array{0:string,1:?string} [status, error] with status sent|failed|skipped */
    public static function send(string $number, string $text): array
    {
        $api = ChannelSettings::active('sms');
        if ($api) {
            return self::sendParanaque($api, self::normalize($number), $text);
        }

        $cfg = config('hmap.notifications.sms');
        switch ($cfg['driver']) {
            case 'http':
                if (!$cfg['http_url']) {
                    return ['failed', 'HMAP_SMS_HTTP_URL is not set'];
                }
                $payload = [$cfg['number_field'] => $number, $cfg['message_field'] => $text];
                if ($cfg['sender']) {
                    $payload[$cfg['sender_field']] = $cfg['sender'];
                }
                try {
                    $req = Http::timeout(15)->acceptJson()->asJson();
                    if ($cfg['http_token']) {
                        $req = $req->withToken($cfg['http_token']);
                    }
                    $resp = $req->post($cfg['http_url'], $payload);
                } catch (\Throwable $e) {
                    return ['failed', 'gateway unreachable: ' . $e->getMessage()];
                }
                return $resp->successful()
                    ? ['sent', null]
                    : ['failed', 'gateway returned HTTP ' . $resp->status() . ': ' . substr($resp->body(), 0, 200)];
            case 'none':
            default:
                return ['skipped', 'No SMS gateway configured'];
        }
    }

    /** Paranaque SMS API: OAuth2 client credentials, then send-sms. */
    private static function sendParanaque(array $s, string $mobile, string $text): array
    {
        foreach (['base_url', 'client_id', 'client_secret', 'department_code'] as $f) {
            if (empty($s[$f])) {
                return ['failed', "SMS settings incomplete: {$f} is missing"];
            }
        }
        $base = rtrim($s['base_url'], '/');
        [$token, $error] = self::token($s);
        if (!$token) {
            return ['failed', $error];
        }

        $post = function (string $bearer) use ($base, $s, $mobile, $text) {
            return Http::timeout(25)->acceptJson()->asJson()->withToken($bearer)
                ->post($base . '/api/v1/send-sms', [
                    'mobile'          => $mobile,
                    'message'         => $text,
                    'department_code' => $s['department_code'],
                    'requestor'       => $s['client_secret'],   // per the API documentation
                ]);
        };
        try {
            $resp = $post($token);
            if ($resp->status() === 401) {
                Cache::forget(self::tokenKey($s));
                [$token, $error] = self::token($s);
                if (!$token) {
                    return ['failed', $error];
                }
                $resp = $post($token);
            }
        } catch (\Throwable $e) {
            return ['failed', 'SMS API unreachable: ' . $e->getMessage()];
        }

        $body = $resp->json();
        if ($resp->successful() && is_array($body) && array_key_exists('error', $body) && $body['error'] === false) {
            return ['sent', null];
        }
        $msg = is_array($body) ? ($body['message'] ?? $body['error_description'] ?? null) : null;
        return ['failed', 'SMS API HTTP ' . $resp->status() . ': ' . ($msg ?? substr($resp->body(), 0, 200))];
    }

    /** @return array{0:?string,1:?string} [token, error] */
    private static function token(array $s): array
    {
        $key = self::tokenKey($s);
        if ($t = Cache::get($key)) {
            return [$t, null];
        }
        try {
            $resp = Http::timeout(20)->acceptJson()->asForm()->post(rtrim($s['base_url'], '/') . '/oauth/token', [
                'grant_type'    => 'client_credentials',
                'client_id'     => $s['client_id'],
                'client_secret' => $s['client_secret'],
            ]);
        } catch (\Throwable $e) {
            return [null, 'SMS API token request failed: ' . $e->getMessage()];
        }
        $data = $resp->json();
        if (!$resp->successful() || empty($data['access_token'])) {
            $msg = is_array($data) ? ($data['error_description'] ?? $data['message'] ?? null) : null;
            return [null, 'SMS API token HTTP ' . $resp->status() . ': ' . ($msg ?? substr($resp->body(), 0, 200))];
        }
        // keep a 10-minute margin before the token's own expiry (30 days by default)
        $ttl = max(60, (int) ($data['expires_in'] ?? 2592000) - 600);
        Cache::put($key, $data['access_token'], $ttl);
        return [$data['access_token'], null];
    }

    private static function tokenKey(array $s): string
    {
        return 'hmap:sms_token:' . hash('sha256', $s['base_url'] . '|' . $s['client_id']);
    }

    /** 09XXXXXXXXX, the form the Paranaque SMS API expects. */
    public static function normalize(string $n): string
    {
        $d = preg_replace('/\D+/', '', $n);
        if (strlen($d) === 12 && strpos($d, '63') === 0) {
            $d = '0' . substr($d, 2);
        }
        return $d;
    }

    /** Philippine mobile numbers in the 09XXXXXXXXX or +639XXXXXXXXX form. */
    public static function validNumber(?string $n): bool
    {
        return $n !== null && preg_match('/^(\+639|09)\d{9}$/', $n) === 1;
    }
}
