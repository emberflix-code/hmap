<?php

namespace App\Services;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Mail;

/**
 * Outbreak alerts and notifications (Ch.3 Module 7).
 *
 * detect() evaluates one morbidity week for every alert-enabled disease with
 * the same rules as the risk tiers (RiskTiers), and creates a notification
 * for each barangay that is
 *   - above its epidemic threshold          → epidemic_threshold
 *   - reporting a single-case-trigger case  → single_case
 *   - inside an active hotspot              → hotspot
 * The unique key on notifications allows one message per disease, barangay,
 * alert type and week, so re-running never repeats an alert. Each new
 * notification gets one delivery per active recipient and channel.
 *
 * deliver() sends pending deliveries and retries failed ones up to
 * max_attempts. Messages state the disease, barangay, alert type, the week's
 * case count and threshold, and the dashboard link; never patient data.
 */
class Notifier
{
    const SYSTEM_EMPLOYEE_ID = 0;   // audit_log actor for automated events

    /** @return int number of new notifications */
    public static function detect(int $year, int $week): int
    {
        $created = 0;
        $diseases = DB::table('diseases')->where('alert_enabled', 1)
            ->get(['disease_id', 'disease_code', 'disease_name', 'single_case_trigger']);
        foreach ($diseases as $d) {
            $risk = RiskTiers::compute($d->disease_code, $year, $week, false);
            if (!$risk) {
                continue;
            }
            foreach ($risk['tiers'] as $t) {
                $types = [];
                if ($t['above_epidemic']) {
                    $types[] = $d->single_case_trigger ? 'single_case' : 'epidemic_threshold';
                }
                if ($t['active_hotspot']) {
                    $types[] = 'hotspot';
                }
                foreach ($types as $type) {
                    if (self::create($d, $t, $type, $year, $week)) {
                        $created++;
                    }
                }
            }
        }
        return $created;
    }

    private static function create(object $d, array $t, string $type, int $year, int $week): bool
    {
        [$subject, $message] = self::compose($d->disease_name, $t['barangay_name'], $type,
            $t['current_cases'], $t['epidemic_threshold'], $year, $week);
        $inserted = DB::table('notifications')->insertOrIgnore([
            'disease_id'      => $d->disease_id,
            'barangay_id'     => $t['barangay_id'],
            'morbidity_year'  => $year,
            'morbidity_week'  => $week,
            'alert_type'      => $type,
            'case_count'      => $t['current_cases'],
            'threshold_value' => $type === 'epidemic_threshold' ? $t['epidemic_threshold'] : null,
            'subject'         => $subject,
            'message'         => $message,
            'created_at'      => now(),
        ]);
        if (!$inserted) {
            return false;   // already notified for this disease, barangay, type and week
        }
        $id = (int) DB::table('notifications')->where([
            'disease_id' => $d->disease_id, 'barangay_id' => $t['barangay_id'], 'alert_type' => $type,
            'morbidity_year' => $year, 'morbidity_week' => $week,
        ])->value('notification_id');

        $rows = [];
        foreach (DB::table('notification_recipients')->where('is_active', 1)->get() as $r) {
            if ($r->via_email) {
                $rows[] = ['notification_id' => $id, 'recipient_id' => $r->recipient_id, 'channel' => 'email'];
            }
            if ($r->via_sms) {
                $rows[] = ['notification_id' => $id, 'recipient_id' => $r->recipient_id, 'channel' => 'sms'];
            }
        }
        if ($rows) {
            DB::table('notification_deliveries')->insertOrIgnore($rows);
        }
        DB::table('audit_log')->insert([
            'employee_id'  => self::SYSTEM_EMPLOYEE_ID,
            'action_type'  => 'NOTIFICATION_CREATED',
            'target_table' => 'notifications',
            'target_id'    => $id,
            'new_values'   => json_encode(['alert_type' => $type, 'disease' => $d->disease_code,
                                           'barangay_id' => $t['barangay_id'], 'year' => $year,
                                           'week' => $week, 'deliveries' => count($rows)]),
        ]);
        return true;
    }

    /** [subject, message]. The message is short enough for one or two SMS. */
    public static function compose(string $disease, string $barangay, string $type, int $cases,
                                   ?float $threshold, int $year, int $week): array
    {
        $when = "MW {$week} {$year}";
        switch ($type) {
            case 'single_case':
                $what = "{$cases} case" . ($cases === 1 ? '' : 's') . ' reported (single-case alert disease)';
                $label = 'case reported';
                break;
            case 'hotspot':
                $what = 'active hotspot (3+ cases within 200 m in 4 weeks)';
                $label = 'active hotspot';
                break;
            default:
                $what = "above epidemic threshold ({$cases} cases vs " . round((float) $threshold, 1) . ')';
                $label = 'above epidemic threshold';
        }
        $link = rtrim(config('hmap.notifications.dashboard_url'), '/');
        $subject = "CESU alert: {$disease} {$label} in {$barangay} ({$when})";
        $message = "CESU ALERT {$when}: {$disease}, {$barangay}: {$what}. Dashboard: {$link}";
        return [$subject, $message];
    }

    /** @return array{sent:int, failed:int, skipped:int} */
    public static function deliver(): array
    {
        $max = (int) config('hmap.notifications.max_attempts');
        $todo = DB::table('notification_deliveries as d')
            ->join('notifications as n', 'n.notification_id', '=', 'd.notification_id')
            ->join('notification_recipients as r', 'r.recipient_id', '=', 'd.recipient_id')
            ->where(function ($q) use ($max) {
                $q->where('d.status', 'pending')
                  ->orWhere(function ($f) use ($max) {
                      $f->where('d.status', 'failed')->where('d.attempts', '<', $max);
                  });
            })
            ->orderBy('d.delivery_id')
            ->get(['d.delivery_id', 'd.channel', 'd.attempts', 'n.subject', 'n.message',
                   'r.email', 'r.mobile', 'r.is_active']);

        $count = ['sent' => 0, 'failed' => 0, 'skipped' => 0];
        foreach ($todo as $d) {
            if (!$d->is_active) {
                [$status, $error] = ['skipped', 'recipient deactivated'];
            } else {
                [$status, $error] = $d->channel === 'email'
                    ? self::sendEmail($d->email, $d->subject, $d->message)
                    : self::sendSms($d->mobile, $d->message);
            }
            DB::table('notification_deliveries')->where('delivery_id', $d->delivery_id)->update([
                'status'   => $status,
                'attempts' => $d->attempts + 1,
                'error'    => $error ? substr($error, 0, 500) : null,
                'sent_at'  => $status === 'sent' ? now() : null,
            ]);
            $count[$status]++;
        }
        return $count;
    }

    /** @return array{0:string,1:?string} */
    public static function sendEmail(?string $to, string $subject, string $body): array
    {
        if (!$to || !filter_var($to, FILTER_VALIDATE_EMAIL)) {
            return ['skipped', 'no valid email address'];
        }
        try {
            Mail::raw($body . "\n\nThis is an automated message from the CESU disease surveillance system. "
                . 'It contains no patient information.', function ($m) use ($to, $subject) {
                    $m->to($to)->subject($subject);
                });
            return ['sent', null];
        } catch (\Throwable $e) {
            Log::warning('Notification email failed: ' . $e->getMessage());
            return ['failed', $e->getMessage()];
        }
    }

    /** @return array{0:string,1:?string} */
    public static function sendSms(?string $to, string $text): array
    {
        if (!SmsSender::validNumber($to)) {
            return ['skipped', 'no valid mobile number'];
        }
        return SmsSender::send($to, $text);
    }

    /** The morbidity weeks the scheduled run checks: the current one and the one before. */
    public static function weeksToCheck(?\DateTime $today = null): array
    {
        $d = $today ? clone $today : new \DateTime();
        $weeks = [[(int) $d->format('o'), (int) $d->format('W')]];
        $d->modify('-7 days');
        $weeks[] = [(int) $d->format('o'), (int) $d->format('W')];
        return $weeks;
    }
}
