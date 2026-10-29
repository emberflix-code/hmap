<?php
// Ch.4 functional checks that need the real registry: thresholds against an
// independent recomputation, report totals against the database, the
// per-barangay alert rule of the disease summary, role restrictions, export
// audit rows, and server-side response times. Read-only apart from audit rows.
//
// Runs against a THROWAWAY MariaDB on 127.0.0.1:3399 loaded by
// ml/etl_registry.py and ml/compute_thresholds.py --alert-year 2026, on a
// City Government computer. Writes only aggregate results:
//
//   php laravel/tests/ch4_realdata_check.php docs/Chapter4_5/results/realdata_tests.json

$root = dirname(__DIR__);
$out = $argv[1] ?? 'realdata_tests.json';
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'CACHE_STORE' => 'array', 'HMAP_HRMO_MODE' => 'stub', 'HMAP_HRMO_STUB_USER_ROLE' => 'Administrator',
    'HMAP_HRMO_STUB_USER_ID' => '1001', 'HMAP_ML_URL' => 'http://127.0.0.1:59999',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use App\Services\RiskTiers;
use Illuminate\Support\Facades\DB;

$results = [];
function tc($id, $area, $desired, $steps, $observed, $passed) {
    global $results;
    $results[] = compact('id', 'area', 'desired', 'steps', 'observed', 'passed');
    echo ($passed ? '  ok   ' : '  FAIL ') . "$id  $observed\n";
}
function req($method, $uri, $query = [], $role = 'Administrator') {
    global $kernel;
    config(['hmap.hrmo.stub_user_role' => $role]);
    $r = Illuminate\Http\Request::create('/api' . $uri, $method, $query, [], [], ['HTTP_ACCEPT' => 'application/json']);
    $t0 = microtime(true);
    $resp = $kernel->handle($r);
    $body = $resp instanceof Symfony\Component\HttpFoundation\StreamedResponse
        ? (function () use ($resp) { ob_start(); $resp->sendContent(); return ob_get_clean(); })()
        : $resp->getContent();
    $ms = (microtime(true) - $t0) * 1000;
    return [$resp->getStatusCode(), $body, $ms];
}
function csvRows($body) {
    $lines = array_values(array_filter(explode("\n", trim($body)), 'strlen'));
    $head = str_getcsv(array_shift($lines));
    return array_map(function ($l) use ($head) { return array_combine($head, str_getcsv($l)); }, $lines);
}

$diseases = DB::table('diseases')->where('alert_enabled', 1)->get(['disease_id', 'disease_code', 'single_case_trigger']);
$baselineYears = range(2021, 2025);

echo "thresholds\n";
// Independent recomputation in PHP from raw counts (the stored values come from Python)
$raw = DB::table('cases')->whereBetween('morbidity_year', [2021, 2025])
    ->whereIn('case_classification', ['Confirmed', 'Probable'])->where('status_flag', 'Active')
    ->groupBy('disease_id', 'morbidity_year', 'morbidity_week')
    ->selectRaw('disease_id, morbidity_year, morbidity_week, COUNT(*) n')->get();
$counts = [];
foreach ($raw as $r) $counts[$r->disease_id][$r->morbidity_week][$r->morbidity_year] = (int) $r->n;
$checked = 0; $matched = 0; $mismatch = [];
foreach ($diseases as $d) {
    [$s, $body] = req('GET', '/thresholds', ['disease_code' => $d->disease_code], 'Analyst');
    foreach (json_decode($body, true) as $row) {
        $w = (int) $row['morbidity_week'];
        $xs = array_map(function ($y) use ($counts, $d, $w) { return $counts[$d->disease_id][$w][$y] ?? 0; }, $baselineYears);
        $mean = array_sum($xs) / 5;
        $sd = sqrt(array_sum(array_map(function ($x) use ($mean) { return ($x - $mean) ** 2; }, $xs)) / 4);
        $ok = abs($row['mean_cases'] - $mean) < 0.00006 && abs($row['std_dev'] - $sd) < 0.00006
            && abs($row['alert_threshold'] - ($mean + $sd)) < 0.0002 && abs($row['threshold_value'] - ($mean + 2 * $sd)) < 0.0002;
        $checked++;
        $ok ? $matched++ : $mismatch[] = "{$d->disease_code} w$w";
    }
}
tc('TC-THR-01', 'Threshold monitoring',
   'Mean, SD, alert (mean + 1 SD) and epidemic (mean + 2 SD) thresholds equal an independent recomputation for every disease and week',
   ['Load the 2026 registry and compute thresholds for alert year 2026 (baseline 2021-2025)',
    'Request GET /api/thresholds for every alert-enabled disease',
    'Recompute each value independently from raw Confirmed + Probable weekly counts',
    'Compare to 4 decimal places'],
   "$matched of $checked disease-weeks match" . ($mismatch ? ' (first mismatch: ' . $mismatch[0] . ')' : ''),
   $checked > 0 && $matched === $checked);

[$s, $body] = req('GET', '/thresholds', ['disease_code' => 'MEA'], 'Analyst');
$mea = json_decode($body, true)[0]['single_case_trigger'] ?? null;
[$s, $body] = req('GET', '/thresholds', ['disease_code' => 'DENGUE'], 'Analyst');
$den = json_decode($body, true)[0]['single_case_trigger'] ?? null;
tc('TC-THR-02', 'Threshold monitoring', 'Measles is flagged as a single-case alert disease and dengue is not (DOH, 2014, p. 58)',
   ['Request GET /api/thresholds for MEA and DENGUE', 'Read single_case_trigger'],
   "MEA single_case_trigger = $mea, DENGUE = $den", (int) $mea === 1 && (int) $den === 0);

echo "reports and export\n";
// 2022 is the latest baseline year with cases of unknown barangay, so it exercises that path too
[$s, $body] = req('GET', '/export/disease-summary', ['year' => 2022], 'Analyst');
$rows = csvRows($body);
$csvTotal = array_sum(array_map(function ($r) { return (int) $r['total_cases']; }, $rows));
$dbTotal = DB::table('cases')->where('morbidity_year', 2022)->where('status_flag', 'Active')->count();
$unknown = array_sum(array_map(function ($r) { return $r['barangay'] === 'Unknown' ? (int) $r['total_cases'] : 0; }, $rows));
$dbUnknown = DB::table('cases')->where('morbidity_year', 2022)->where('status_flag', 'Active')->whereNull('barangay_id')->count();
tc('TC-RPT-01', 'Reports and export', 'Disease summary totals equal the database count, including cases with no barangay',
   ['As a Health Analyst, export the disease summary for 2022', 'Sum total_cases over all rows and over the Unknown barangay rows',
    'Count active 2022 cases in the database, in total and with no barangay'],
   "export $csvTotal = database $dbTotal; Unknown barangay $unknown = database $dbUnknown",
   $s === 200 && $csvTotal === $dbTotal && $unknown === $dbUnknown && $dbUnknown > 0);

// Defect 3 retest: export EPIDEMIC flags == risk-tier above-epidemic barangays
$byWeek = [];
foreach (csvRows(req('GET', '/export/disease-summary', ['year' => 2025, 'disease_code' => 'DENGUE'], 'Analyst')[1]) as $r) {
    if ($r['alert'] === 'EPIDEMIC') $byWeek[(int) $r['morbidity_week']][] = $r['barangay'];
}
$weeksSame = 0; $flags = 0; $diffWeeks = [];
for ($w = 1; $w <= 52; $w++) {
    $tiers = RiskTiers::compute('DENGUE', 2025, $w, false)['tiers'];
    $expected = array_values(array_map(function ($t) { return $t['barangay_name']; },
        array_filter($tiers, function ($t) { return $t['above_epidemic']; })));
    $got = $byWeek[$w] ?? [];
    sort($expected); sort($got);
    $flags += count($got);
    $expected === $got ? $weeksSame++ : $diffWeeks[] = $w;
}
tc('TC-RPT-02', 'Reports and export',
   'Each barangay row of the disease summary is flagged EPIDEMIC exactly when the dashboard risk tiers find that barangay above its own epidemic threshold',
   ['Export the 2025 dengue disease summary', 'For each week 1-52, compute the risk tiers for the same week',
    'Compare the EPIDEMIC barangays with the barangays above their epidemic threshold'],
   "$weeksSame of 52 weeks identical ($flags EPIDEMIC barangay-weeks)" . ($diffWeeks ? '; differ in week ' . implode(',', $diffWeeks) : ''),
   $weeksSame === 52);

[$s, $body] = req('GET', '/export/full-registry', [], 'Administrator');
$regRows = count(csvRows($body));
$active = DB::table('cases')->where('status_flag', 'Active')->count();
tc('TC-RPT-03', 'Reports and export', 'The full registry export contains every active case',
   ['As Administrator, export the full case registry', 'Count data rows', 'Count active cases in the database'],
   "export $regRows rows = database $active", $s === 200 && $regRows === $active);

$matrix = [
    ['/export/my-entries', 'Encoder', 200], ['/export/disease-summary', 'Encoder', 403], ['/export/full-registry', 'Encoder', 403],
    ['/export/disease-summary', 'Analyst', 200], ['/export/full-registry', 'Analyst', 403],
    ['/export/full-registry', 'Administrator', 200],
];
$okRoles = 0; $seen = [];
foreach ($matrix as [$uri, $role, $want]) {
    $q = $uri === '/export/disease-summary' ? ['year' => 2025, 'disease_code' => 'ABD'] : [];
    [$s] = req('GET', $uri, $q, $role);
    $seen[] = "$role $uri -> $s";
    if ($s === $want) $okRoles++;
}
tc('TC-RPT-04', 'Reports and export', 'Each export is available only to its role or higher (Encoder < Analyst < Administrator)',
   ['Request each export as Encoder, Health Analyst and Administrator', 'Compare the HTTP status with the role rule'],
   "$okRoles of " . count($matrix) . ' role checks as expected', $okRoles === count($matrix));

$exports = DB::table('audit_log')->where('action_type', 'EXPORT')->get();
$withCount = $exports->filter(function ($e) { return isset(json_decode($e->new_values, true)['rows']); })->count();
tc('TC-RPT-05', 'Security', 'Every completed export is recorded in the audit log with the employee and row count',
   ['Run the exports above', 'Read EXPORT rows from audit_log'],
   "{$exports->count()} EXPORT audit rows, $withCount with a row count", $exports->count() >= 5 && $withCount === $exports->count());

echo "response times (server-side, in-process, 5 runs each, median)\n";
$calls = [
    'App start: diseases' => ['/diseases', []], 'App start: barangays' => ['/barangays', []],
    'KPI strip' => ['/summary', ['disease_code' => 'DENGUE', 'morbidity_year' => 2025, 'morbidity_week' => 30]],
    'Trend chart: weekly series' => ['/weekly-series', ['disease_code' => 'DENGUE', 'year_start' => 2025, 'year_end' => 2025]],
    'Trend chart: thresholds' => ['/thresholds', ['disease_code' => 'DENGUE']],
    'Map: cases per barangay' => ['/heatmap-week', ['disease_code' => 'DENGUE', 'morbidity_year' => 2025, 'morbidity_week' => 30]],
    'Map: risk tiers' => ['/risk-tiers', ['disease_code' => 'DENGUE', 'morbidity_year' => 2025, 'morbidity_week' => 30]],
    'Recommendations' => ['/recommendations', ['disease_code' => 'DENGUE', 'year' => 2025, 'week' => 30]],
    'Weekly Report (all diseases)' => ['/weekly-summary', ['morbidity_year' => 2025, 'morbidity_week' => 30]],
];
$timings = [];
foreach ($calls as $label => [$uri, $q]) {
    $ms = [];
    for ($i = 0; $i < 5; $i++) {
        [$s, , $t] = req('GET', $uri, $q, 'Administrator');
        $ms[] = $t;
    }
    sort($ms);
    $timings[$label] = ['status' => $s, 'median_ms' => round($ms[2], 1), 'max_ms' => round(max($ms), 1)];
    printf("  %-32s %4d  median %7.1f ms  max %7.1f ms\n", $label, $s, $ms[2], max($ms));
}
$dash = array_sum(array_map(function ($k) use ($timings) { return $timings[$k]['median_ms']; },
    ['App start: diseases', 'App start: barangays', 'KPI strip', 'Trend chart: weekly series', 'Trend chart: thresholds']));
$map = $timings['Map: cases per barangay']['median_ms'] + $timings['Map: risk tiers']['median_ms'];
tc('TC-PRF-01', 'Performance', 'Dashboard data within 3 seconds and map data within 5 seconds (server-side share)',
   ['Load the full registry (35,681 cases)', 'Time each API request the dashboard and map make on opening, 5 runs, median',
    'Sum the requests of each screen'],
   sprintf('dashboard requests %.0f ms in total, map requests %.0f ms (server side, development computer)', $dash, $map),
   $dash < 3000 && $map < 5000);

$summary = ['generated_at' => date('c'), 'cases_loaded' => $active, 'tests' => $results, 'timings' => $timings];
@mkdir(dirname($out), 0777, true);
file_put_contents($out, json_encode($summary, JSON_PRETTY_PRINT));
$failed = count(array_filter($results, function ($r) { return !$r['passed']; }));
echo $failed ? "\n$failed FAILED\n" : "\nall passed\n";
exit($failed ? 1 : 0);
