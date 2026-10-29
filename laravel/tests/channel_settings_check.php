<?php
// Check of the Administrator-maintained email/SMS settings and the Paranaque
// SMS API flow (faked; nothing is sent), against a THROWAWAY MariaDB on
// 127.0.0.1:3399 (root / migtest). Never point it at a real database.
//
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < ml/schema.sql
//   php laravel/tests/channel_settings_check.php     (exit code 0 = all passed)

$root = dirname(__DIR__);
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'CACHE_STORE' => 'array', 'MAIL_MAILER' => 'array', 'HMAP_HRMO_MODE' => 'stub',
    'HMAP_HRMO_STUB_USER_ROLE' => 'Administrator', 'HMAP_HRMO_STUB_USER_ID' => '1001', 'HMAP_SMS_DRIVER' => 'none',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Services\ChannelSettings;
use App\Services\SmsSender;
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
    return [$resp->getStatusCode(), json_decode($resp->getContent(), true), $resp->getContent()];
}

const SECRET = 'test-client-secret-9f8e7d';
$base = 'https://sms.test/sms-api/public';

// Fake Paranaque SMS API. $mode controls the send-sms answer.
$mode = 'ok';
$oauthCalls = 0;
Http::fake(function ($req) use (&$mode, &$oauthCalls) {
    if (str_ends_with($req->url(), '/oauth/token')) {
        $oauthCalls++;
        if ($req['client_secret'] !== SECRET) {
            return Http::response(['error' => 'invalid_client', 'error_description' => 'Client authentication failed'], 401);
        }
        return Http::response(['token_type' => 'Bearer', 'expires_in' => 2592000, 'access_token' => "tok$oauthCalls"]);
    }
    if (str_ends_with($req->url(), '/api/v1/send-sms')) {
        if ($mode === 'reject_first_token' && $req->header('Authorization')[0] === 'Bearer tok1') {
            return Http::response(['message' => 'Unauthenticated.'], 401);
        }
        if ($mode === 'api_error') {
            return Http::response(['error' => true, 'message' => 'Invalid mobile number'], 200);
        }
        return Http::response(['error' => false, 'message' => 'SMS sent']);
    }
    return Http::response([], 404);
});
if (!function_exists('str_ends_with')) {
    function str_ends_with($h, $n) { return $n === '' || substr($h, -strlen($n)) === $n; }
}
function lastSend() {
    return Http::recorded()->filter(function ($p) { return str_ends_with($p[0]->url(), '/send-sms'); })->last()[0];
}

echo "settings storage\n";
[$s, $d] = call('GET', '/admin/channel-settings');
check('defaults shown, nothing enabled', $s === 200 && $d['sms']['is_active'] === false
      && $d['sms']['base_url'] === 'https://app.paranaque.gov.ph/sms-api/public' && $d['sms']['client_secret_set'] === false);
[$s, $d, $raw] = call('PUT', '/admin/channel-settings/sms', ['base_url' => $base, 'client_id' => '7',
    'client_secret' => SECRET, 'department_code' => 'CHO', 'is_active' => true]);
check('SMS settings saved', $s === 200 && $d['client_secret_set'] === true && $d['department_code'] === 'CHO', $raw);
check('secret never returned by the API', strpos($raw, SECRET) === false && !array_key_exists('client_secret', $d));
$stored = DB::table('channel_settings')->where('channel', 'sms')->value('settings_enc');
check('secret encrypted at rest', strpos($stored, SECRET) === false && strpos($stored, 'CHO') === false);
$auditRaw = DB::table('audit_log')->where('action_type', 'CHANNEL_SETTINGS_UPDATE')->value('new_values');
check('audit lists changed fields, not values', strpos($auditRaw, 'client_secret') !== false && strpos($auditRaw, SECRET) === false, $auditRaw);
[$s] = call('PUT', '/admin/channel-settings/sms', ['base_url' => $base, 'client_id' => '7', 'client_secret' => '',
    'department_code' => 'CHO', 'is_active' => true]);
check('blank secret keeps the stored one', $s === 200 && ChannelSettings::active('sms')['client_secret'] === SECRET);

echo "Paranaque SMS API\n";
[$st, $err] = SmsSender::send('+639171234567', 'CESU ALERT test');
check('sent', $st === 'sent', "$st $err");
$req = lastSend();
check('payload: 09 number, message, department_code, requestor = client secret',
      $req['mobile'] === '09171234567' && $req['message'] === 'CESU ALERT test'
      && $req['department_code'] === 'CHO' && $req['requestor'] === SECRET, json_encode($req->data()));
check('bearer token from OAuth client credentials', $req->header('Authorization')[0] === 'Bearer tok1');
$oauth = Http::recorded()->first(function ($p) { return str_ends_with($p[0]->url(), '/oauth/token'); })[0];
check('OAuth request is form-encoded client_credentials', $oauth['grant_type'] === 'client_credentials'
      && $oauth['client_id'] === '7' && strpos($oauth->header('Content-Type')[0], 'application/x-www-form-urlencoded') === 0);
SmsSender::send('09171234567', 'second');
check('token cached (no second OAuth call)', $oauthCalls === 1, $oauthCalls);
$mode = 'reject_first_token';
[$st] = SmsSender::send('09171234567', 'after token revoked');
check('401 refreshes the token and retries once', $st === 'sent' && $oauthCalls === 2 && lastSend()->header('Authorization')[0] === 'Bearer tok2');
$mode = 'api_error';
[$st, $err] = SmsSender::send('09171234567', 'bad');
check('API "error": true recorded as failed with its message', $st === 'failed' && strpos($err, 'Invalid mobile number') !== false, $err);
$mode = 'ok';

DB::table('channel_settings')->where('channel', 'sms')->update(['settings_enc' =>
    Illuminate\Support\Facades\Crypt::encryptString(json_encode(['base_url' => $base, 'client_id' => '7',
        'client_secret' => 'wrong', 'department_code' => 'CHO']))]);
app('cache')->flush();
[$st, $err] = SmsSender::send('09171234567', 'x');
check('wrong secret: failed with the API reason', $st === 'failed' && strpos($err, 'Client authentication failed') !== false, $err);
call('PUT', '/admin/channel-settings/sms', ['base_url' => $base, 'client_id' => '7', 'client_secret' => SECRET,
    'department_code' => 'CHO', 'is_active' => false]);
[$st, $err] = SmsSender::send('09171234567', 'x');
check('disabled settings fall back to the .env driver (none = skipped)', $st === 'skipped', "$st $err");

echo "email\n";
[$s] = call('PUT', '/admin/channel-settings/email', ['host' => 'smtp.example', 'port' => 587, 'encryption' => 'tls',
    'from_email' => 'not-an-email', 'is_active' => true]);
check('invalid sender address rejected', $s === 422, $s);
[$s, $r] = call('POST', '/admin/channel-settings/email/test', ['to' => 'cesu@example.gov.ph']);
check('no SMTP settings: .env mailer used (array, sent)', $s === 200 && $r['status'] === 'sent', json_encode($r));
[$s, $d, $raw] = call('PUT', '/admin/channel-settings/email', ['host' => '127.0.0.1', 'port' => 1, 'encryption' => 'none',
    'username' => 'noreply.cesu@example.gov.ph', 'password' => 'smtp-pass-123', 'from_email' => 'noreply.cesu@example.gov.ph',
    'from_name' => 'CESU', 'is_active' => true]);
check('SMTP settings saved, password hidden', $s === 200 && $d['password_set'] === true && strpos($raw, 'smtp-pass-123') === false);
[$s, $r] = call('POST', '/admin/channel-settings/email/test', ['to' => 'cesu@example.gov.ph']);
check('Administrator SMTP server is used (unreachable here: failed with reason)',
      $s === 200 && $r['status'] === 'failed' && $r['error'] !== '', json_encode($r));
check('runtime mailer built from the saved settings', config('mail.mailers.cesu_smtp.host') === '127.0.0.1'
      && config('mail.mailers.cesu_smtp.password') === 'smtp-pass-123' && config('mail.from.address') === 'noreply.cesu@example.gov.ph');

echo "access and robustness\n";
check('unknown channel is 404', call('PUT', '/admin/channel-settings/fax', ['is_active' => true])[0] === 404);
DB::table('channel_settings')->where('channel', 'email')->update(['settings_enc' => 'not-decryptable']);
check('undecryptable settings (APP_KEY changed) treated as not configured', ChannelSettings::active('email') === []
      || ChannelSettings::active('email') === null);
config(['hmap.hrmo.stub_user_role' => 'Analyst']);
check('Analyst cannot see settings', call('GET', '/admin/channel-settings')[0] === 403);
$tests = DB::table('audit_log')->where('action_type', 'CHANNEL_TEST')->count();
check('test sends audited', $tests === 2, $tests);

echo $fail ? "\n$fail FAILED\n" : "\nall passed\n";
exit($fail ? 1 : 0);
