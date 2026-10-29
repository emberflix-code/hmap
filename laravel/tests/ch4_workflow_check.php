<?php
// Ch.4 functional, security and end-to-end checks on test data (no patient
// data) against a THROWAWAY MariaDB on 127.0.0.1:3399 (root / migtest).
// Never point it at a real database. Setup, from the repository root:
//
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < ml/schema.sql
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < laravel/tests/fixtures/recommender_seed.sql
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest hmap_db < ml/migrations/2026_10_30_recommendations.sql
//   php laravel/tests/ch4_workflow_check.php docs/Chapter4_5/results/workflow_tests.json
//
// Level 3 (TC-E2E-01) encodes cases through the API, runs the production
// hotspot detector (ml/detect_clusters.py), and follows them through risk
// tiers, recommendations and notifications.

$root = dirname(__DIR__);
$repo = dirname($root);
$out = $argv[1] ?? 'workflow_tests.json';
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'DB_USER' => 'root', 'DB_NAME' => 'hmap_db',   // for ml/detect_clusters.py
    'CACHE_STORE' => 'array', 'MAIL_MAILER' => 'array', 'HMAP_HRMO_MODE' => 'stub',
    'HMAP_HRMO_STUB_USER_ROLE' => 'Encoder', 'HMAP_HRMO_STUB_USER_ID' => '1002',
    'HMAP_ML_URL' => 'http://127.0.0.1:59999', 'HMAP_SMS_DRIVER' => 'none',
    'HMAP_DASHBOARD_URL' => 'https://hrmo.paranaque.gov.ph/hmap',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Http;

$results = [];
function tc($id, $area, $desired, $steps, $observed, $passed) {
    global $results;
    $results[] = compact('id', 'area', 'desired', 'steps', 'observed', 'passed');
    echo ($passed ? '  ok   ' : '  FAIL ') . "$id  $observed\n";
}
function req($method, $uri, $body = [], $role = 'Encoder', $files = []) {
    global $kernel;
    config(['hmap.hrmo.stub_user_role' => $role]);
    $server = ['HTTP_ACCEPT' => 'application/json'];
    if ($files) {
        $r = Illuminate\Http\Request::create('/api' . $uri, $method, $body, [], $files, $server);
    } else {
        $server['CONTENT_TYPE'] = 'application/json';
        $r = Illuminate\Http\Request::create('/api' . $uri, $method,
            $method === 'GET' ? $body : [], [], [], $server, $method === 'GET' ? null : json_encode($body));
    }
    $resp = $kernel->handle($r);
    return [$resp->getStatusCode(), json_decode($resp->getContent(), true)];
}

DB::table('user_roles')->insert([
    ['employee_id' => 1001, 'role' => 'Administrator', 'is_active' => 1],
    ['employee_id' => 1002, 'role' => 'Encoder', 'is_active' => 1],
    ['employee_id' => 1003, 'role' => 'Analyst', 'is_active' => 1],
]);
$valid = ['disease_code' => 'DENGUE', 'case_classification' => 'Confirmed', 'date_onset' => '2025-08-05',
          'date_admitted' => '2025-08-07', 'barangay_name' => 'Vitalez', 'age' => 12, 'sex' => 'Female',
          'outcome' => 'Alive', 'morbidity_week' => 32, 'morbidity_year' => 2025,
          'street_purok' => 'Purok 3', 'case_lat' => 14.4950, 'case_lng' => 121.0010, 'geocode_source' => 'manual_pin'];

echo "case data management\n";
$before = DB::table('cases')->count();
[$s, $b] = req('POST', '/cases', $valid);
$case = DB::table('cases')->where('case_id', $b['case_id'] ?? 0)->first();
$audit = DB::table('audit_log')->where('action_type', 'INSERT')->where('target_id', $b['case_id'] ?? 0)->first();
$addr = DB::table('case_addresses')->where('case_id', $b['case_id'] ?? 0)->first();
tc('TC-CAS-01', 'Case data management', 'A complete, valid case is saved with its address and logged in the audit log',
   ['Log in as Data Encoder', 'Submit a complete dengue case with a pinned address', 'Read the saved case, address and audit rows'],
   $s === 201 ? "saved as case {$b['case_id']}, entered_by {$case->entered_by}, age group {$case->age_group}, audit row " . ($audit ? 'present' : 'missing') . ', address ' . ($addr ? $addr->geocode_source : 'missing') : "HTTP $s",
   $s === 201 && $case && $audit && $addr && (int) $case->entered_by === 1002 && $case->age_group === '10-14');

$invalid = [
    'missing disease'            => ['disease_code' => null],
    'unknown disease code'       => ['disease_code' => 'XYZ'],
    'invalid classification'     => ['case_classification' => 'Likely'],
    'missing barangay'           => ['barangay_name' => null],
    'barangay outside the city'  => ['barangay_name' => 'Pasay'],
    'morbidity week 0'           => ['morbidity_week' => 0],
    'morbidity week 54'          => ['morbidity_week' => 54],
    'year before 2010'           => ['morbidity_year' => 2009],
    'negative age'               => ['age' => -1],
    'age above 130'              => ['age' => 131],
    'sex code not in the list'   => ['sex' => 'M'],
    'impossible date'            => ['date_onset' => '2025-13-40'],
    'onset date in the future'   => ['date_onset' => date('Y-m-d', strtotime('+10 days')), 'date_admitted' => null],
    'admission before onset'     => ['date_onset' => '2025-08-05', 'date_admitted' => '2025-08-01'],
    'age group contradicts age'  => ['age' => 40, 'age_group' => '0-4'],
    'latitude out of range'      => ['case_lat' => 95],
];
$rejected = 0; $accepted = [];
foreach ($invalid as $label => $change) {
    [$s] = req('POST', '/cases', array_merge($valid, $change));
    $s === 422 ? $rejected++ : $accepted[] = "$label (HTTP $s)";
}
$after = DB::table('cases')->count();
tc('TC-CAS-02', 'Case data management', '100% of invalid records are rejected and none is saved',
   ['Submit ' . count($invalid) . ' records, each with one invalid field: ' . implode('; ', array_keys($invalid)),
    'Check each response and the number of saved cases'],
   "$rejected of " . count($invalid) . ' rejected' . ($accepted ? '; accepted: ' . implode(', ', $accepted) : '')
   . '; cases saved: ' . ($after - $before - 1),
   $rejected === count($invalid) && $after - $before === 1);

$csv = tempnam(sys_get_temp_dir(), 'bulk') . '.csv';
file_put_contents($csv, "disease_code,case_classification,date_onset,barangay_name,age,sex,outcome,morbidity_week,morbidity_year\n"
    . "DENGUE,Probable,2025-08-04,Vitalez,8,Male,Alive,32,2025\n"
    . "DENGUE,Suspect,2025-08-05,Vitalez,30,Female,Alive,32,2025\n"
    . "DENGUE,Probable,2025-08-06,Nowhere,30,Female,Alive,32,2025\n"
    . "MEA,Suspect,2025-08-06,Vitalez,4,Male,Alive,32,2025\n"
    . "DENGUE,Probable,2025-08-06,Vitalez,30,Female,Alive,99,2025\n");
$auditBefore = DB::table('audit_log')->where('action_type', 'INSERT')->count();
[$s, $b] = req('POST', '/cases/bulk', [], 'Encoder', ['csv' => new UploadedFile($csv, 'cases.csv', 'text/csv', null, true)]);
$auditAdded = DB::table('audit_log')->where('action_type', 'INSERT')->count() - $auditBefore;
$badRows = array_column($b['errors'] ?? [], 'row');
tc('TC-CAS-03', 'Case data management', 'A CSV upload saves the valid rows, reports each invalid row by number, and logs every saved row',
   ['Upload a CSV of 5 rows: 3 valid, 1 unknown barangay, 1 week 99', 'Read the response and the audit log'],
   "inserted {$b['rows_inserted']}, failed {$b['rows_failed']} (rows " . implode(', ', $badRows) . "), $auditAdded audit rows",
   $s === 200 && $b['rows_inserted'] === 3 && $badRows === [4, 6] && $auditAdded === 3);

file_put_contents($csv, "disease_code,barangay_name\nDENGUE,Merville\n");
[$s, $b] = req('POST', '/cases/bulk', [], 'Encoder', ['csv' => new UploadedFile($csv, 'cases.csv', 'text/csv', null, true)]);
tc('TC-CAS-04', 'Case data management', 'A CSV without the required columns is refused as a whole',
   ['Upload a CSV with only two columns'], "HTTP $s: " . ($b['error'] ?? ''), $s === 422);

echo "security\n";
$routes = collect(app('router')->getRoutes()->getRoutes())->filter(function ($r) {
    return strpos($r->uri(), 'api/') === 0 && collect($r->gatherMiddleware())->contains(function ($m) {
        return is_string($m) && strpos($m, 'hrmo') === 0;
    });
});
// Fill every route parameter so each route is really reached ({channel} must be email or sms)
$path = function ($r) {
    return '/' . substr(preg_replace('/\{[^}]+\}/', '1', str_replace('{channel}', 'sms', $r->uri())), 4);
};
config(['hmap.hrmo.mode' => 'jwt']);
$denied = 0; $leaks = [];
foreach ($routes as $r) {
    [$s] = req($r->methods()[0], $path($r));
    $s === 401 ? $denied++ : $leaks[] = $r->methods()[0] . ' ' . $r->uri() . " ($s)";
}
config(['hmap.hrmo.mode' => 'stub']);
tc('TC-SEC-01', 'Security', 'Every protected API route refuses a request without a login session',
   ['Switch to the production login mode (HRMO token)', 'Call every protected API route without a token'],
   "$denied of {$routes->count()} routes answered 401" . ($leaks ? '; not refused: ' . implode(', ', $leaks) : ''),
   $denied === $routes->count());

$levels = ['Encoder' => 1, 'Analyst' => 2, 'Administrator' => 3];
$checks = 0; $ok = 0; $bad = [];
foreach ($routes as $r) {
    $min = null;
    foreach ($r->gatherMiddleware() as $m) {
        if (is_string($m) && preg_match('/^hrmo:(Encoder|Analyst|Administrator)$/', $m, $mm)) $min = $mm[1];
    }
    if (!$min) continue;
    foreach ($levels as $role => $lvl) {
        if ($lvl >= $levels[$min]) continue;
        $checks++;
        [$s] = req($r->methods()[0], $path($r), [], $role);
        $s === 403 ? $ok++ : $bad[] = "$role " . $r->methods()[0] . ' ' . $r->uri() . " ($s)";
    }
}
tc('TC-SEC-02', 'Security', 'Every role-restricted route refuses users below its required role',
   ['Read the required role of every API route', 'Call each restricted route as every lower role'],
   "$ok of $checks lower-role requests refused with 403" . ($bad ? '; allowed: ' . implode(', ', $bad) : ''),
   $checks > 0 && $ok === $checks);

config(['hmap.hrmo.mode' => 'jwt', 'hmap.mfa.enabled' => false]);
Http::fake(function ($q) {
    preg_match('/tok-(\d+)/', $q->header('Authorization')[0] ?? '', $m);
    // the real HRMO /auth/me shape: top-level, user_id differs from the employee number
    $emp = (int) ($m[1] ?? 0);
    return Http::response(['user_id' => $emp + 90000, 'empid' => $emp, 'full_name' => 'Employee']);
});
$asToken = function ($id, $uri) use ($kernel) {
    $r = Illuminate\Http\Request::create('/api' . $uri, 'GET', [], [], [], ['HTTP_ACCEPT' => 'application/json', 'HTTP_AUTHORIZATION' => "Bearer tok-$id"]);
    return $kernel->handle($r)->getStatusCode();
};
$deniedBefore = DB::table('audit_log')->where('action_type', 'ACCESS_DENIED')->count();
$outsider = $asToken(5555, '/whoami');
$member = $asToken(1003, '/whoami');
DB::table('user_roles')->where('employee_id', 1003)->update(['is_active' => 0]);
$removed = $asToken(1003, '/whoami');
DB::table('user_roles')->where('employee_id', 1003)->update(['is_active' => 1]);
$deniedRows = DB::table('audit_log')->where('action_type', 'ACCESS_DENIED')->count() - $deniedBefore;
config(['hmap.hrmo.mode' => 'stub', 'hmap.mfa.enabled' => true]);
tc('TC-SEC-03', 'Security', 'Only CESU staff on the authorization list get in; removing someone cuts access at once; refusals are logged',
   ['Call the API with a valid HRMO token of an employee who is not CESU staff', 'Repeat as an authorized Health Analyst',
    'Deactivate the Analyst and repeat', 'Count ACCESS_DENIED audit rows'],
   "non-CESU employee $outsider, CESU Analyst $member, deactivated Analyst $removed, $deniedRows refusals logged",
   $outsider === 403 && $member === 200 && $removed === 403 && $deniedRows === 2);

echo "end-to-end (Level 3)\n";
$t0 = microtime(true);
// 1. A Data Encoder encodes four dengue cases close together in Tambo, week 35 of 2025
$base = [14.5140, 120.9960];
$ids = [];
foreach ([[0, 0], [40, 30], [-35, 50], [60, -20]] as $i => [$dn, $de]) {
    [$s, $b] = req('POST', '/cases', array_merge($valid, [
        'barangay_name' => 'Tambo', 'morbidity_week' => 35, 'date_onset' => '2025-08-2' . (5 + $i), 'date_admitted' => null,
        'case_classification' => 'Probable', 'street_purok' => 'Block ' . ($i + 1),
        'case_lat' => $base[0] + $dn / 111320, 'case_lng' => $base[1] + $de / (111320 * cos(deg2rad($base[0]))),
    ]), 'Encoder');
    $ids[] = $b['case_id'] ?? null;
}
// 2. Hotspot detection with the CESU rule (production script)
$py = file_exists("$repo/.venv/Scripts/python.exe") ? "$repo/.venv/Scripts/python.exe" : 'python';
exec('"' . $py . '" "' . $repo . '/ml/detect_clusters.py" --disease DENGUE --year 2025 2>&1', $pyOut, $pyCode);
$run = DB::table('detection_runs')->orderByDesc('detection_run_id')->first();
$cluster = DB::table('case_clusters as cc')->join('case_cluster_members as m', 'm.cluster_id', '=', 'cc.cluster_id')
    ->where('cc.detection_run_id', $run->detection_run_id ?? 0)->whereIn('m.case_id', $ids)
    ->select('cc.cluster_id', 'cc.case_count', 'cc.radius_m')->first();
// 3. Risk tiers, 4. recommendations
[, $tiers] = req('GET', '/risk-tiers', ['disease_code' => 'DENGUE', 'morbidity_year' => 2025, 'morbidity_week' => 35], 'Analyst');
$tambo = collect($tiers['tiers'] ?? [])->firstWhere('barangay_name', 'Tambo');
[, $recs] = req('GET', '/recommendations', ['disease_code' => 'DENGUE', 'year' => 2025, 'week' => 35], 'Analyst');
$recTambo = collect($recs['barangays'] ?? [])->firstWhere('barangay_name', 'Tambo');
// 5. Notifications
DB::table('notification_recipients')->insert(['full_name' => 'CESU Head', 'email' => 'cesu.head@example.gov.ph', 'via_email' => 1, 'via_sms' => 0, 'is_active' => 1]);
Artisan::call('hmap:notify', ['--year' => 2025, '--week' => 35]);
$notes = DB::table('notifications as n')->join('barangays as b', 'b.barangay_id', '=', 'n.barangay_id')
    ->where('n.morbidity_week', 35)->where('b.barangay_name', 'Tambo')->pluck('n.alert_type')->sort()->values()->all();
$sent = DB::table('notification_deliveries as d')->join('notifications as n', 'n.notification_id', '=', 'd.notification_id')
    ->join('barangays as b', 'b.barangay_id', '=', 'n.barangay_id')
    ->where('n.morbidity_week', 35)->where('b.barangay_name', 'Tambo')->where('d.status', 'sent')
    ->selectRaw('MAX(TIMESTAMPDIFF(SECOND, n.created_at, d.sent_at)) AS max_s, COUNT(*) AS n')->first();
$elapsed = microtime(true) - $t0;
tc('TC-E2E-01', 'Integration (Level 3)',
   'Encoded cases flow through hotspot detection, risk tiering, recommendation and notification without manual steps between modules',
   ['As Data Encoder, encode 4 probable dengue cases in Tambo within 60 m of each other, week 35 of 2025',
    'Run hotspot detection with the CESU rule (200 m, 3 cases, 4 weeks)', 'As Health Analyst, open the risk tiers and recommendations for the week',
    'Run the scheduled alert check', 'Check the alerts and their delivery'],
   sprintf('cluster of %s cases (radius %s m); Tambo tier %s (%s); %d recommendations, rank %s; alerts: %s; %d emails sent, max %s s after detection; whole flow %.1f s',
       $cluster->case_count ?? 'no', isset($cluster->radius_m) ? round($cluster->radius_m) : '-', $tambo['tier'] ?? '?',
       implode(', ', $tambo['reasons'] ?? []), count($recTambo['items'] ?? []), $recTambo['rank'] ?? '-',
       implode(' + ', $notes), $sent->n ?? 0, $sent->max_s ?? '-', $elapsed),
   $pyCode === 0 && $cluster && (int) $cluster->case_count === 4 && ($tambo['tier'] ?? '') === 'High'
   && ($recTambo['rank'] ?? 0) === 1 && $notes === ['epidemic_threshold', 'hotspot'] && (int) $sent->n === 2 && (int) $sent->max_s <= 300);

@mkdir(dirname($out), 0777, true);
file_put_contents($out, json_encode(['generated_at' => date('c'), 'tests' => $results], JSON_PRETTY_PRINT));
$failed = count(array_filter($results, function ($r) { return !$r['passed']; }));
echo $failed ? "\n$failed FAILED\n" : "\nall passed\n";
exit($failed ? 1 : 0);
