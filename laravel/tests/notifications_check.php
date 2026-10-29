<?php
// End-to-end check of outbreak notifications (Module 7) against a THROWAWAY
// MariaDB on 127.0.0.1:3399 (root / migtest). Never point it at a real
// database. Setup, from the repository root:
//
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < ml/schema.sql
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < laravel/tests/fixtures/recommender_seed.sql
//   php laravel/tests/notifications_check.php        (exit code 0 = all passed)
//
// The shared fixture gives known alerts for morbidity week 30 of 2025:
// dengue above threshold in Baclaran (also a hotspot) and Tambo, one measles
// case in Vitalez, and acute bloody diarrhea above a zero baseline in Tambo.

$root = dirname(__DIR__);
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'CACHE_STORE' => 'array', 'MAIL_MAILER' => 'array', 'HMAP_HRMO_MODE' => 'stub',
    'HMAP_HRMO_STUB_USER_ROLE' => 'Administrator', 'HMAP_HRMO_STUB_USER_ID' => '1001',
    'HMAP_DASHBOARD_URL' => 'https://hrmo.paranaque.gov.ph/hmap', 'HMAP_SMS_DRIVER' => 'none',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Services\Notifier;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

$fail = 0;
function check($label, $ok, $extra = '') {
    global $fail;
    echo ($ok ? "  ok   " : "  FAIL ") . $label . ($ok ? '' : "  $extra") . "\n";
    if (!$ok) $fail++;
}
function call($method, $uri, $body = []) {
    global $kernel;
    $server = ['HTTP_ACCEPT' => 'application/json', 'CONTENT_TYPE' => 'application/json'];
    $req = Illuminate\Http\Request::create('/api' . $uri, $method, [], [], [], $server, $body ? json_encode($body) : null);
    $resp = $kernel->handle($req);
    return [$resp->getStatusCode(), json_decode($resp->getContent(), true)];
}
function sentEmails() {
    return app('mail.manager')->mailer('array')->getSwiftMailer()->getTransport()->messages();
}
function deliveries($status, $channel = null) {
    $q = DB::table('notification_deliveries')->where('status', $status);
    if ($channel) $q->where('channel', $channel);
    return $q->count();
}

echo "recipients (Administrator)\n";
[$s] = call('POST', '/notification-recipients', ['full_name' => 'No Phone', 'via_sms' => true, 'via_email' => false]);
check('SMS without a mobile number rejected', $s === 422, $s);
[$s] = call('POST', '/notification-recipients', ['full_name' => 'Bad', 'mobile' => '12345', 'via_sms' => true]);
check('malformed mobile number rejected', $s === 422, $s);
[$s, $a] = call('POST', '/notification-recipients', ['full_name' => 'CESU Head', 'position' => 'Nurse III',
    'email' => 'cesu.head@example.gov.ph', 'mobile' => '09171234567', 'via_email' => true, 'via_sms' => true]);
check('recipient with email and SMS created', $s === 201, json_encode($a));
[, $b] = call('POST', '/notification-recipients', ['full_name' => 'City Health Officer', 'email' => 'cho@example.gov.ph']);
[, $c] = call('POST', '/notification-recipients', ['full_name' => 'Former Staff', 'email' => 'former@example.gov.ph']);
[$s] = call('PUT', "/notification-recipients/{$c['recipient_id']}", ['is_active' => false]);
check('recipient deactivated', $s === 200);

echo "detection, MW 30 2025\n";
Artisan::call('hmap:notify', ['--year' => 2025, '--week' => 30, '--no-send' => true]);
$n = DB::table('notifications as n')->join('diseases as d', 'd.disease_id', '=', 'n.disease_id')
    ->join('barangays as b', 'b.barangay_id', '=', 'n.barangay_id')
    ->orderBy('d.disease_code')->orderBy('b.barangay_name')->orderBy('n.alert_type')
    ->get(['d.disease_code', 'b.barangay_name', 'n.alert_type', 'n.case_count', 'n.message']);
$got = $n->map(function ($r) { return "{$r->disease_code}/{$r->barangay_name}/{$r->alert_type}"; })->all();
$want = ['ABD/Tambo/epidemic_threshold', 'DENGUE/Baclaran/epidemic_threshold', 'DENGUE/Baclaran/hotspot',
         'DENGUE/Tambo/epidemic_threshold', 'MEA/Vitalez/single_case'];
check('exactly the 5 expected alerts', $got === $want, json_encode($got));
check('Suspect-only barangay not alerted', !in_array('DENGUE/Vitalez/epidemic_threshold', $got, true));
check('one delivery per active recipient and channel (5 x 3)', DB::table('notification_deliveries')->count() === 15,
      DB::table('notification_deliveries')->count());
check('deactivated recipient gets nothing',
      DB::table('notification_deliveries')->where('recipient_id', $c['recipient_id'])->count() === 0);
$msg = $n->firstWhere('alert_type', 'hotspot')->message;
echo "  sample: $msg\n";
check('every message fits one SMS (160 chars)', $n->every(function ($r) { return strlen($r->message) <= 160; }),
      json_encode($n->pluck('message')));
check('message has disease, barangay, type and link', strpos($msg, 'Dengue') !== false
      && strpos($msg, 'Baclaran') !== false && strpos($msg, 'hotspot') !== false
      && strpos($msg, 'https://hrmo.paranaque.gov.ph/hmap') !== false);
$caseCols = ['case_id', 'age', 'sex', 'date_onset'];
check('notification rows hold no patient fields', !array_intersect($caseCols,
      array_keys((array) DB::table('notifications')->first())));

echo "de-duplication\n";
Artisan::call('hmap:notify', ['--year' => 2025, '--week' => 30, '--no-send' => true]);
check('second run creates no new alerts', DB::table('notifications')->count() === 5);
check('second run adds no deliveries', DB::table('notification_deliveries')->count() === 15);

echo "delivery: email sent, SMS skipped without a gateway\n";
$t0 = microtime(true);
$r = Notifier::deliver();
$elapsed = microtime(true) - $t0;
check('10 emails sent, 5 SMS skipped', $r === ['sent' => 10, 'failed' => 0, 'skipped' => 5], json_encode($r));
// getTo() is [address => display name], and the name is null here, so isset() would miss it
$toCho = sentEmails()->filter(function ($m) { return array_key_exists('cho@example.gov.ph', $m->getTo()); })->count();
check('emails reached the right addresses', sentEmails()->count() === 10 && $toCho === 5,
      sentEmails()->count() . ' captured, ' . $toCho . ' to the CHO');
check('skipped SMS says why', DB::table('notification_deliveries')->where('channel', 'sms')->value('error') === 'No SMS gateway configured');
check('sent deliveries have sent_at', DB::table('notification_deliveries')->where('status', 'sent')->whereNull('sent_at')->count() === 0);
printf("  delivery run took %.2f s for 15 deliveries\n", $elapsed);
check('nothing left to deliver', Notifier::deliver() === ['sent' => 0, 'failed' => 0, 'skipped' => 0]);

echo "SMS gateway (http driver): failure, retry, success\n";
config(['hmap.notifications.sms.driver' => 'http', 'hmap.notifications.sms.http_url' => 'https://sms.example/send',
        'hmap.notifications.sms.http_token' => 'tok', 'hmap.notifications.sms.sender' => 'CESU']);
DB::table('notification_deliveries')->where('channel', 'sms')->update(['status' => 'pending', 'attempts' => 0, 'error' => null]);
$fakeStatus = 500;
Http::fake(function ($req) use (&$fakeStatus) {
    return Http::response(['ok' => $fakeStatus === 200], $fakeStatus);
});
Notifier::deliver();
check('gateway error recorded as failed', deliveries('failed', 'sms') === 5);
Notifier::deliver();
check('failed SMS retried (attempt 2)', DB::table('notification_deliveries')->where('channel', 'sms')->max('attempts') == 2);
$fakeStatus = 200;
Notifier::deliver();
check('retry succeeds once the gateway answers', deliveries('sent', 'sms') === 5);
$sentReq = Http::recorded()->last()[0];   // assertSent needs PHPUnit, which is not installed
check('gateway got number, message, sender, token', $sentReq['number'] === '09171234567'
      && strpos($sentReq['message'], 'CESU ALERT') === 0 && $sentReq['sendername'] === 'CESU'
      && $sentReq->header('Authorization')[0] === 'Bearer tok');
DB::table('notification_deliveries')->where('channel', 'sms')->update(['status' => 'failed', 'attempts' => 3]);
$fakeStatus = 500;
Notifier::deliver();
check('no retry after 3 attempts', DB::table('notification_deliveries')->where('channel', 'sms')->max('attempts') == 3);

echo "API\n";
[$s, $list] = call('GET', '/notifications');
check('recent alerts with delivery summary', $s === 200 && count($list) === 5
      && $list[0]['deliveries']['sent'] === 2, json_encode($list[0] ?? null));
config(['hmap.notifications.sms.driver' => 'none']);
[$s, $test] = call('POST', "/notification-recipients/{$a['recipient_id']}/test");
check('test send reports each channel', $s === 200 && $test['email']['status'] === 'sent'
      && $test['sms']['status'] === 'skipped', json_encode($test));
config(['hmap.hrmo.stub_user_role' => 'Encoder']);
check('Encoder sees alerts', call('GET', '/notifications')[0] === 200);
check('Encoder cannot manage recipients', call('GET', '/notification-recipients')[0] === 403);

echo "scheduled weeks\n";
check('current and previous week, across the new year',
      Notifier::weeksToCheck(new DateTime('2026-01-02')) === [[2026, 1], [2025, 52]],
      json_encode(Notifier::weeksToCheck(new DateTime('2026-01-02'))));

echo "audit log\n";
$actions = DB::table('audit_log')->pluck('action_type')->countBy()->all();
echo '  ' . json_encode($actions) . "\n";
check('5 NOTIFICATION_CREATED', ($actions['NOTIFICATION_CREATED'] ?? 0) === 5);
check('recipient changes audited', ($actions['RECIPIENT_CREATE'] ?? 0) === 3 && isset($actions['RECIPIENT_UPDATE'])
      && isset($actions['RECIPIENT_TEST']));

echo $fail ? "\n$fail FAILED\n" : "\nall passed\n";
exit($fail ? 1 : 0);
