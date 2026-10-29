<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

/**
 * SMS channel for outbreak notifications (Module 7).
 *
 * The gateway is not chosen yet, so the driver is configurable:
 *   none  every SMS is recorded as 'skipped' (no gateway). The delivery log
 *         never claims a message was sent when it was not.
 *   http  JSON POST to HMAP_SMS_HTTP_URL with a Bearer token; field names are
 *         configurable to fit the gateway CESU provides. Any 2xx = sent.
 * A gateway with a different API gets its own case here.
 */
class SmsSender
{
    /** @return array{0:string,1:?string} [status, error] with status sent|failed|skipped */
    public static function send(string $number, string $text): array
    {
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

    /** Philippine mobile numbers in the 09XXXXXXXXX or +639XXXXXXXXX form. */
    public static function validNumber(?string $n): bool
    {
        return $n !== null && preg_match('/^(\+639|09)\d{9}$/', $n) === 1;
    }
}
