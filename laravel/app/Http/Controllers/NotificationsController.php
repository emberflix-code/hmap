<?php

namespace App\Http\Controllers;

use App\Services\Notifier;
use App\Services\SmsSender;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

/**
 * Outbreak notifications (Module 7).
 *
 *   GET  /notifications                          any CESU role: recent alerts + delivery status
 *   GET  /notification-recipients                Administrator
 *   POST /notification-recipients                Administrator
 *   PUT  /notification-recipients/{id}           Administrator (edit or deactivate)
 *   POST /notification-recipients/{id}/test      Administrator: send a test message now
 *
 * Alerts are created by `php artisan hmap:notify` (cron), not by these routes.
 */
class NotificationsController extends Controller
{
    public function index(): JsonResponse
    {
        $rows = DB::table('notifications as n')
            ->join('diseases as d', 'd.disease_id', '=', 'n.disease_id')
            ->join('barangays as b', 'b.barangay_id', '=', 'n.barangay_id')
            ->orderByDesc('n.created_at')->orderByDesc('n.notification_id')
            ->limit(30)
            ->get(['n.notification_id', 'n.alert_type', 'n.morbidity_year', 'n.morbidity_week',
                   'n.case_count', 'n.subject', 'n.created_at', 'd.disease_code', 'b.barangay_name']);

        $status = DB::table('notification_deliveries')
            ->whereIn('notification_id', $rows->pluck('notification_id'))
            ->groupBy('notification_id', 'status')
            ->selectRaw('notification_id, status, COUNT(*) AS n')
            ->get();
        $summary = [];
        foreach ($status as $s) {
            $summary[$s->notification_id][$s->status] = (int) $s->n;
        }
        return response()->json($rows->map(function ($r) use ($summary) {
            $r->deliveries = $summary[$r->notification_id] ?? new \stdClass();
            return $r;
        }));
    }

    public function recipients(): JsonResponse
    {
        return response()->json(DB::table('notification_recipients')->orderBy('full_name')->get());
    }

    public function storeRecipient(Request $request): JsonResponse
    {
        $data = $this->recipientInput($request);
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        $id = DB::table('notification_recipients')->insertGetId($data + [
            'updated_by' => $employeeId, 'updated_at' => now(),
        ]);
        $this->audit($employeeId, 'RECIPIENT_CREATE', $id, null, $data, $request->ip());
        return response()->json(DB::table('notification_recipients')->where('recipient_id', $id)->first(), 201);
    }

    public function updateRecipient(Request $request, int $id): JsonResponse
    {
        $old = DB::table('notification_recipients')->where('recipient_id', $id)->first();
        if (!$old) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $data = $this->recipientInput($request, (array) $old);
        $employeeId = (int) $request->attributes->get('hmap.employee_id');
        DB::table('notification_recipients')->where('recipient_id', $id)
            ->update($data + ['updated_by' => $employeeId, 'updated_at' => now()]);
        $this->audit($employeeId, 'RECIPIENT_UPDATE', $id, array_intersect_key((array) $old, $data), $data, $request->ip());
        return response()->json(DB::table('notification_recipients')->where('recipient_id', $id)->first());
    }

    public function testRecipient(Request $request, int $id): JsonResponse
    {
        $r = DB::table('notification_recipients')->where('recipient_id', $id)->first();
        if (!$r) {
            return response()->json(['error' => 'not_found'], 404);
        }
        $text = 'CESU TEST: notifications from the disease surveillance system reach you on this channel. '
            . 'Dashboard: ' . rtrim(config('hmap.notifications.dashboard_url'), '/');
        $result = [];
        if ($r->via_email) {
            [$s, $e] = Notifier::sendEmail($r->email, 'CESU alert test', $text);
            $result['email'] = ['status' => $s, 'error' => $e];
        }
        if ($r->via_sms) {
            [$s, $e] = Notifier::sendSms($r->mobile, $text);
            $result['sms'] = ['status' => $s, 'error' => $e];
        }
        $this->audit((int) $request->attributes->get('hmap.employee_id'), 'RECIPIENT_TEST', $id, null, $result, $request->ip());
        return response()->json($result);
    }

    /** Validated recipient fields; $current fills in what a partial update leaves out. */
    private function recipientInput(Request $request, ?array $current = null): array
    {
        $req = $current ? 'sometimes|' : 'required|';
        $data = $request->validate([
            'full_name' => $req . 'string|max:120',
            'position'  => 'nullable|string|max:120',
            'email'     => 'nullable|email|max:190',
            'mobile'    => ['nullable', 'regex:/^(\+639|09)\d{9}$/'],
            'via_email' => 'sometimes|boolean',
            'via_sms'   => 'sometimes|boolean',
            'is_active' => 'sometimes|boolean',
        ], ['mobile.regex' => 'Use a mobile number like 09171234567 or +639171234567.']);

        $merged = array_merge($current ?? ['via_email' => 1, 'via_sms' => 0, 'email' => null, 'mobile' => null], $data);
        $errors = [];
        if ($merged['via_email'] && !$merged['email']) {
            $errors['email'] = ['An email address is needed to receive email alerts.'];
        }
        if ($merged['via_sms'] && !SmsSender::validNumber($merged['mobile'])) {
            $errors['mobile'] = ['A mobile number is needed to receive SMS alerts.'];
        }
        if ($errors) {
            abort(response()->json(['message' => 'The given data was invalid.', 'errors' => $errors], 422));
        }
        return $data;
    }

    private function audit(int $employeeId, string $action, int $targetId, ?array $old, ?array $new, ?string $ip): void
    {
        DB::table('audit_log')->insert([
            'employee_id'  => $employeeId,
            'action_type'  => $action,
            'target_table' => 'notification_recipients',
            'target_id'    => $targetId,
            'old_values'   => $old ? json_encode($old) : null,
            'new_values'   => $new ? json_encode($new) : null,
            'ip_address'   => $ip,
        ]);
    }
}
