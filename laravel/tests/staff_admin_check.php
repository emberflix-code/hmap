<?php
// Check of the CESU staff authorization list maintained by the Administrator
// (Module 9) against a THROWAWAY MariaDB on 127.0.0.1:3399 (root / migtest).
// Never point it at a real database. Setup, from the repository root:
//
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < ml/schema.sql
//   php laravel/tests/staff_admin_check.php          (exit code 0 = all passed)

$root = dirname(__DIR__);
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'CACHE_STORE' => 'array', 'HMAP_HRMO_MODE' => 'stub', 'HMAP_HRMO_STUB_USER_ROLE' => 'Administrator',
    'HMAP_HRMO_STUB_USER_ID' => '1001', 'HRMO_API_BASE' => 'https://hrmo.test/api/v1',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
if (!function_exists('str_ends_with')) {   // PHP 7.4
    function str_ends_with($h, $n) { return $n === '' || substr($h, -strlen($n)) === $n; }
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use Illuminate\Support\Facades\Crypt;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

$fail = 0;
function check($label, $ok, $extra = '') {
    global $fail;
    echo ($ok ? "  ok   " : "  FAIL ") . $label . ($ok ? '' : "  $extra") . "\n";
    if (!$ok) $fail++;
}
function call($method, $uri, $body = [], $as = 1001, $role = 'Administrator') {
    global $kernel;
    config(['hmap.hrmo.stub_user_id' => $as, 'hmap.hrmo.stub_user_role' => $role]);
    $r = Illuminate\Http\Request::create('/api' . $uri, $method, [], [], [],
        ['HTTP_ACCEPT' => 'application/json', 'CONTENT_TYPE' => 'application/json'], $body ? json_encode($body) : null);
    $resp = $kernel->handle($r);
    return [$resp->getStatusCode(), json_decode($resp->getContent(), true)];
}

// The first Administrator is added in the database, as on a new installation
DB::table('user_roles')->insert(['employee_id' => 1001, 'full_name' => 'First Admin', 'role' => 'Administrator', 'is_active' => 1]);

echo "adding and listing\n";
[$s] = call('POST', '/admin/staff', ['employee_id' => 2002, 'full_name' => 'Nurse A', 'role' => 'Encoder']);
check('Administrator adds an Encoder', $s === 201, $s);
[$s] = call('POST', '/admin/staff', ['employee_id' => 2003, 'role' => 'Analyst']);
check('name is optional', $s === 201, $s);
[$s, $b] = call('POST', '/admin/staff', ['employee_id' => 2002, 'role' => 'Analyst']);
check('an active employee cannot be added twice', $s === 422, $s);
[$s] = call('POST', '/admin/staff', ['employee_id' => 2004, 'role' => 'Superuser']);
check('unknown role rejected', $s === 422, $s);
[$s, $list] = call('GET', '/admin/staff');
check('list shows everyone with role and status', $s === 200 && count($list) === 3
      && collect($list)->firstWhere('employee_id', 2002)['role'] === 'Encoder', json_encode($list));
$row = DB::table('user_roles')->where('employee_id', 2002)->first();
check('assigned_by records the Administrator', (int) $row->assigned_by === 1001);

echo "changing roles and access\n";
[$s] = call('PUT', '/admin/staff/2002', ['role' => 'Analyst']);
check('role changed', $s === 200 && DB::table('user_roles')->where('employee_id', 2002)->value('role') === 'Analyst');
check('the new role applies at once', call('GET', '/risk-tiers', [], 2002, DB::table('user_roles')->where('employee_id', 2002)->value('role'))[0] !== 403);
[$s] = call('PUT', '/admin/staff/2003', ['is_active' => false]);
check('access removed', $s === 200 && (int) DB::table('user_roles')->where('employee_id', 2003)->value('is_active') === 0);
[$s] = call('POST', '/admin/staff', ['employee_id' => 2003, 'role' => 'Encoder']);
check('removed employee can be restored with a new role', $s === 201
      && DB::table('user_roles')->where('employee_id', 2003)->value('role') === 'Encoder'
      && (int) DB::table('user_roles')->where('employee_id', 2003)->value('is_active') === 1);

echo "lock-out protection\n";
[$s, $b] = call('PUT', '/admin/staff/1001', ['role' => 'Analyst']);
check('Administrator cannot demote themselves', $s === 422, json_encode($b));
[$s] = call('PUT', '/admin/staff/1001', ['is_active' => false]);
check('Administrator cannot deactivate themselves', $s === 422, $s);
call('PUT', '/admin/staff/2002', ['role' => 'Administrator']);
[$s] = call('PUT', '/admin/staff/1001', ['role' => 'Analyst'], 2002);
check('another Administrator can demote them', $s === 200, $s);
[$s, $b] = call('PUT', '/admin/staff/2002', ['is_active' => false], 1001, 'Analyst');
check('only Administrators manage staff', $s === 403, $s);
DB::table('user_roles')->where('employee_id', 1001)->update(['role' => 'Administrator']);
DB::table('user_roles')->where('employee_id', 2002)->update(['role' => 'Analyst']);
DB::table('user_roles')->where('employee_id', 1001)->update(['is_active' => 1]);
// the last-Administrator rule is checked even if the request comes from someone else
DB::table('user_roles')->insert(['employee_id' => 3003, 'role' => 'Administrator', 'is_active' => 0]);
[$s, $b] = call('PUT', '/admin/staff/1001', ['is_active' => false], 3003);
check('the last active Administrator cannot be removed', $s === 422 && strpos($b['message'], 'At least one') !== false, json_encode($b));

echo "removal takes effect at once (production login mode)\n";
config(['hmap.hrmo.mode' => 'jwt', 'hmap.mfa.enabled' => false]);
Http::fake(function ($q) {
    if (str_ends_with($q->url(), '/auth/login')) {
        return Http::response(['access_token' => 'tok-2002', 'expires_in' => 3600, 'user' => ['id' => 2002, 'full_name' => 'Nurse A. Santos']]);
    }
    return Http::response(['user' => ['id' => 2002, 'full_name' => 'Nurse A. Santos']]);
});
$asNurse = function ($uri) use ($kernel) {
    $r = Illuminate\Http\Request::create('/api' . $uri, 'GET', [], [], [], ['HTTP_ACCEPT' => 'application/json', 'HTTP_AUTHORIZATION' => 'Bearer tok-2002']);
    return $kernel->handle($r)->getStatusCode();
};
$r = Illuminate\Http\Request::create('/api/auth/login', 'POST', [], [], [],
    ['HTTP_ACCEPT' => 'application/json', 'CONTENT_TYPE' => 'application/json'], json_encode(['username' => 'nurse', 'password' => 'x']));
$login = $kernel->handle($r)->getStatusCode();
check('sign-in stores the HRMO name on the list', $login === 200
      && DB::table('user_roles')->where('employee_id', 2002)->value('full_name') === 'Nurse A. Santos');
$before = $asNurse('/whoami');
DB::table('user_roles')->where('employee_id', 2002)->update(['is_active' => 0]);   // as the panel does
$after = $asNurse('/whoami');
check('a removed staff member is refused on the next request', $before === 200 && $after === 403, "$before then $after");
config(['hmap.hrmo.mode' => 'stub', 'hmap.mfa.enabled' => true]);

echo "authenticator reset\n";
DB::table('user_mfa')->insert(['employee_id' => 2003, 'secret_enc' => Crypt::encryptString('JBSWY3DPEHPK3PXP'),
    'confirmed_at' => now(), 'created_at' => now()]);
[, $list] = call('GET', '/admin/staff');
check('list shows who has two-step sign-in', collect($list)->firstWhere('employee_id', 2003)['mfa_enrolled'] === true);
[$s, $b] = call('POST', '/admin/staff/2003/reset-mfa');
check('Administrator resets a lost authenticator', $s === 200 && $b['success'] === true
      && !DB::table('user_mfa')->where('employee_id', 2003)->exists());
[$s, $b] = call('POST', '/admin/staff/2003/reset-mfa');
check('a second reset reports nothing to reset', $s === 200 && $b['success'] === false);

echo "audit log\n";
$actions = DB::table('audit_log')->pluck('action_type')->countBy()->all();
echo '  ' . json_encode($actions) . "\n";
check('additions, restores, changes and the reset are logged', ($actions['STAFF_ADD'] ?? 0) === 2
      && ($actions['STAFF_REACTIVATE'] ?? 0) === 1 && ($actions['STAFF_UPDATE'] ?? 0) >= 4 && ($actions['MFA_RESET'] ?? 0) === 1);

echo $fail ? "\n$fail FAILED\n" : "\nall passed\n";
exit($fail ? 1 : 0);
