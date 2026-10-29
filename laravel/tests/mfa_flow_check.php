<?php
// End-to-end check of multi-factor authentication (Module 9): boots the real
// app on in-memory SQLite with a faked HRMO API and walks enrollment, login,
// replay, recovery codes, the attempt limit, logout, reset, and the audit log.
// phpunit is not installed on the LGU server, so this runs as a plain script:
//
//   php tests/mfa_flow_check.php            (from laravel/; exit code 0 = all passed)

$root = dirname(__DIR__);
if (!function_exists('str_ends_with')) {   // PHP 7.4
    function str_ends_with($h, $n) { return $n === '' || substr($h, -strlen($n)) === $n; }
}
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'sqlite', 'DB_DATABASE' => ':memory:',
    'CACHE_STORE' => 'array', 'HMAP_HRMO_MODE' => 'jwt', 'HMAP_MFA_ENABLED' => 'true',
    'HRMO_API_BASE' => 'https://hrmo.test/api/v1',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Services\Mfa;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Schema;

$fail = 0;
function check($label, $ok, $extra = '') {
    global $fail;
    echo ($ok ? "  ok   " : "  FAIL ") . $label . ($ok ? '' : "  $extra") . "\n";
    if (!$ok) $fail++;
}

// ── RFC 6238 Appendix B vectors (SHA-1), truncated to 6 digits ──
$k = '12345678901234567890';
check('RFC 6238 T=59',         Mfa::totp($k, intdiv(59, 30)) === '287082');
check('RFC 6238 T=1111111109', Mfa::totp($k, intdiv(1111111109, 30)) === '081804');
check('RFC 6238 T=1234567890', Mfa::totp($k, intdiv(1234567890, 30)) === '005924');
check('RFC 6238 T=2000000000', Mfa::totp($k, intdiv(2000000000, 30)) === '279037');
check('base32 round trip', Mfa::base32Decode(Mfa::base32Encode($k)) === $k);
check('base32 RFC 4648 "foobar"', Mfa::base32Encode('foobar') === 'MZXW6YTBOI');

// ── schema ──
Schema::create('user_roles', function ($t) {
    $t->increments('role_id'); $t->unsignedInteger('employee_id'); $t->string('role');
    $t->boolean('is_active')->default(1);
});
Schema::create('audit_log', function ($t) {
    $t->increments('log_id'); $t->unsignedInteger('employee_id'); $t->string('action_type', 30);
    $t->string('target_table')->nullable(); $t->unsignedInteger('target_id')->nullable();
    $t->text('old_values')->nullable(); $t->text('new_values')->nullable();
    $t->string('ip_address')->nullable(); $t->timestamp('action_at')->useCurrent();
});
DB::statement('CREATE TABLE user_mfa (employee_id INTEGER PRIMARY KEY, secret_enc TEXT NOT NULL,
    confirmed_at DATETIME NULL, last_used_step INTEGER NULL, recovery_codes TEXT NULL,
    created_at DATETIME NOT NULL)');
DB::table('user_roles')->insert([
    ['employee_id' => 1001, 'role' => 'Administrator', 'is_active' => 1],
    ['employee_id' => 1002, 'role' => 'Encoder', 'is_active' => 1],
]);

// ── fake HRMO: any password works; token "tok-<id>-<n>" identifies the user ──
$users = ['nurse' => 1002, 'admin' => 1001, 'clerk' => 2001];
Http::fake(function ($req) use ($users) {
    if (str_ends_with($req->url(), '/auth/login')) {
        $id = $users[$req['username']] ?? null;
        return $id ? Http::response(['access_token' => "tok-$id-" . uniqid(), 'expires_in' => 3600,
                                     'user' => ['id' => $id, 'full_name' => "User $id"]])
                   : Http::response(['message' => 'bad'], 401);
    }
    if (str_ends_with($req->url(), '/auth/me')) {
        preg_match('/tok-(\d+)-/', $req->header('Authorization')[0] ?? '', $m);
        return $m ? Http::response(['user' => ['id' => (int) $m[1], 'full_name' => "User {$m[1]}"]])
                  : Http::response([], 401);
    }
    if (str_ends_with($req->url(), '/auth/logout')) return Http::response([]);
    return Http::response([], 404);
});

function call($method, $uri, $token = null, $body = []) {
    global $kernel;
    $server = ['HTTP_ACCEPT' => 'application/json', 'CONTENT_TYPE' => 'application/json',
               'REMOTE_ADDR' => '10.0.0.' . rand(1, 250)];
    if ($token) $server['HTTP_AUTHORIZATION'] = "Bearer $token";
    $req = Illuminate\Http\Request::create('/api' . $uri, $method, [], [], [], $server,
                                           $body ? json_encode($body) : null);
    $resp = $kernel->handle($req);
    return [$resp->getStatusCode(), json_decode($resp->getContent(), true)];
}
// A fresh HRMO token = a new login session for that user.
function token($user) {
    global $users;
    return 'tok-' . $users[$user] . '-' . uniqid();
}
function codeFor($id, $offset = 0) {
    $row = DB::table('user_mfa')->where('employee_id', $id)->first();
    $secret = Mfa::base32Decode(Illuminate\Support\Facades\Crypt::decryptString($row->secret_enc));
    return Mfa::totp($secret, intdiv(time(), 30) + $offset);
}

echo "login gate\n";
[$s] = call('POST', '/auth/login', null, ['username' => 'clerk', 'password' => 'x']);
check('non-CESU employee refused at login', $s === 403, $s);
[$s, $b] = call('POST', '/auth/login', null, ['username' => 'nurse', 'password' => 'x']);
check('CESU nurse password accepted', $s === 200 && $b['role'] === 'Encoder', $s);

echo "first login: enrollment\n";
$t1 = token('nurse');
[$s, $b] = call('GET', '/auth/me', $t1);
check('protected route needs MFA, not enrolled', $s === 401 && $b['error'] === 'mfa_required' && $b['enrolled'] === false, json_encode($b));
[$s, $b] = call('GET', '/whoami', $t1);
check('other routes also blocked', $s === 401 && $b['error'] === 'mfa_required');
[$s, $b] = call('POST', '/auth/mfa/enroll', $t1);
check('enroll returns secret + otpauth URI', $s === 200 && strlen($b['secret']) === 32
      && strpos($b['otpauth_uri'], 'otpauth://totp/CESU%20Outbreak%20System:User%201002?secret=') === 0, json_encode($b));
$secret1 = $b['secret'];
[, $b] = call('POST', '/auth/mfa/enroll', $t1);
check('repeated enroll reuses the pending secret', $b['secret'] === $secret1);
[$s] = call('POST', '/auth/mfa/enroll/confirm', $t1, ['code' => '000000']);
check('wrong confirm code rejected', $s === 422, $s);
$used = codeFor(1002);
[$s, $b] = call('POST', '/auth/mfa/enroll/confirm', $t1, ['code' => $used]);
check('right code confirms, 8 recovery codes', $s === 200 && count($b['recovery_codes']) === 8, json_encode($b));
$recovery = $b['recovery_codes'];
[$s, $b] = call('GET', '/auth/me', $t1);
check('session now verified', $s === 200 && $b['employee_id'] === 1002, json_encode($b));
[$s] = call('POST', '/auth/mfa/enroll', $t1);
check('cannot re-enroll once confirmed', $s === 409, $s);

echo "later login: verification\n";
$t2 = token('nurse');
[$s, $b] = call('GET', '/auth/me', $t2);
check('new session needs MFA, enrolled', $s === 401 && $b['enrolled'] === true);
[$s] = call('POST', '/auth/mfa/verify', $t2, ['code' => $used]);
check('replayed code rejected', $s === 422, $s);
[$s, $b] = call('POST', '/auth/mfa/verify', $t2, ['code' => codeFor(1002, 1)]);
check('next code accepted (clock drift window)', $s === 200 && $b['method'] === 'totp', json_encode($b));
check('verified session works', call('GET', '/auth/me', $t2)[0] === 200);
check('first session unaffected', call('GET', '/auth/me', $t1)[0] === 200);

echo "recovery codes\n";
$t3 = token('nurse');
[$s, $b] = call('POST', '/auth/mfa/verify', $t3, ['code' => strtolower($recovery[0])]);
check('recovery code accepted (case-insensitive)', $s === 200 && $b['method'] === 'recovery' && $b['recovery_codes_left'] === 7, json_encode($b));
$t4 = token('nurse');
[$s] = call('POST', '/auth/mfa/verify', $t4, ['code' => $recovery[0]]);
check('recovery code works only once', $s === 422, $s);

echo "attempt limit\n";
$t5 = token('nurse');
Mfa::clearFailures(1002);   // the reused recovery code above already counted once
for ($i = 1; $i <= 4; $i++) { [$s] = call('POST', '/auth/mfa/verify', $t5, ['code' => '111111']); }
check('4th wrong code: 422', $s === 422, $s);
[$s] = call('POST', '/auth/mfa/verify', $t5, ['code' => '111111']);
check('5th wrong code locks: 429', $s === 429, $s);
[$s] = call('POST', '/auth/mfa/verify', $t5, ['code' => codeFor(1002, 0)]);
check('even a right code refused while locked', $s === 429, $s);
Mfa::clearFailures(1002);

echo "logout and reset\n";
// logout reads the hmap_jwt cookie, as the browser sends it
$r =Illuminate\Http\Request::create('/api/auth/logout', 'POST', [], ['hmap_jwt' => $t2], [], ['HTTP_ACCEPT' => 'application/json']);
$kernel->handle($r);
[$s, $b] = call('GET', '/auth/me', $t2);
check('logout ends the verified session', $s === 401 && $b['error'] === 'mfa_required', json_encode($b));
check('reset refused without an Administrator', Artisan::call('hmap:mfa-reset', ['employee_id' => 1002, '--by' => 1002]) === 1);
check('reset by Administrator', Artisan::call('hmap:mfa-reset', ['employee_id' => 1002, '--by' => 1001]) === 0);
[$s, $b] = call('GET', '/auth/me', $t1);
check('reset ends verified sessions, asks to enroll', $s === 401 && $b['enrolled'] === false, json_encode($b));

echo "audit log\n";
$actions = DB::table('audit_log')->pluck('action_type')->countBy()->all();
ksort($actions);
echo '  ' . json_encode($actions) . "\n";
foreach (['ACCESS_DENIED', 'MFA_ENROLLED', 'MFA_VERIFIED', 'MFA_RECOVERY_USED', 'MFA_FAILED', 'MFA_LOCKED', 'MFA_RESET'] as $a) {
    check("audit has $a", isset($actions[$a]));
}
$row = DB::table('user_mfa')->first();
check('no user_mfa row left after reset', $row === null);

echo $fail ? "\n$fail FAILED\n" : "\nall passed\n";
exit($fail ? 1 : 0);
