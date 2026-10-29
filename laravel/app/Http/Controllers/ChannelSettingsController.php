<?php

namespace App\Http\Controllers;

use App\Services\ChannelSettings;
use App\Services\Notifier;
use App\Services\SmsSender;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * Email and SMS settings maintained by the CESU Administrator (Module 7).
 *
 *   GET  /admin/channel-settings                 both channels, secrets never returned
 *   PUT  /admin/channel-settings/{channel}       save; a blank secret keeps the stored one
 *   POST /admin/channel-settings/{channel}/test  send a test message to {to}
 *
 * Audit rows list which fields changed, never their values.
 */
class ChannelSettingsController extends Controller
{
    public function index(): JsonResponse
    {
        return response()->json([
            'email' => ChannelSettings::forDisplay('email'),
            'sms'   => ChannelSettings::forDisplay('sms'),
        ]);
    }

    public function update(Request $request, string $channel): JsonResponse
    {
        $rules = $channel === 'email' ? [
            'host'       => 'required|string|max:190',
            'port'       => 'required|integer|min:1|max:65535',
            'encryption' => 'required|in:tls,ssl,none',
            'username'   => 'nullable|string|max:190',
            'password'   => 'nullable|string|max:255',
            'from_email' => 'required|email|max:190',
            'from_name'  => 'nullable|string|max:120',
            'is_active'  => 'required|boolean',
        ] : [
            'base_url'        => 'required|url|max:255',
            'client_id'       => 'required|string|max:64',
            'client_secret'   => 'nullable|string|max:255',
            'department_code' => 'required|string|max:32',
            'is_active'       => 'required|boolean',
        ];
        $data = $request->validate($rules);
        $isActive = (bool) $data['is_active'];
        unset($data['is_active']);

        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $changed = ChannelSettings::save($channel, $data, $isActive, $employeeId);
        $this->audit($employeeId, 'CHANNEL_SETTINGS_UPDATE', $channel, ['changed' => $changed], $request->ip());
        return response()->json(ChannelSettings::forDisplay($channel));
    }

    public function test(Request $request, string $channel): JsonResponse
    {
        $to = $request->validate(['to' => 'required|string|max:190'])['to'];
        $text = 'CESU TEST: outbreak notifications from the disease surveillance system reach you on this channel.';
        if ($channel === 'email') {
            if (!filter_var($to, FILTER_VALIDATE_EMAIL)) {
                return response()->json(['message' => 'Enter a valid email address.'], 422);
            }
            [$status, $error] = Notifier::sendEmail($to, 'CESU alert test', $text);
        } else {
            if (!SmsSender::validNumber($to)) {
                return response()->json(['message' => 'Enter a mobile number like 09171234567.'], 422);
            }
            [$status, $error] = Notifier::sendSms($to, $text);
        }
        $this->audit((int) $request->attributes->get('hmap.employee_id'), 'CHANNEL_TEST', $channel,
            ['status' => $status, 'error' => $error], $request->ip());
        return response()->json(['status' => $status, 'error' => $error]);
    }

    private function audit(int $employeeId, string $action, string $channel, array $values, ?string $ip): void
    {
        DB::table('audit_log')->insert([
            'employee_id'  => $employeeId,
            'action_type'  => $action,
            'target_table' => 'channel_settings',
            'new_values'   => json_encode(['channel' => $channel] + $values),
            'ip_address'   => $ip,
        ]);
    }
}
