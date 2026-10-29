<?php
// Writes the system's Weekly Report (GET /api/weekly-summary) for every
// morbidity week of one year to a JSON file, for the Ch.4 Level 2
// reconciliation against the CESU PIDSR workbook (ml/validation/reconcile_5yrave.py).
// Runs against a THROWAWAY MariaDB on 127.0.0.1:3399 loaded by ml/etl_registry.py.
//
//   php laravel/tests/dump_weekly_summary.php 2026 out.json

$root = dirname(__DIR__);
[$year, $out] = [(int) ($argv[1] ?? 2026), $argv[2] ?? 'weekly_summary.json'];
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'CACHE_STORE' => 'array', 'HMAP_HRMO_MODE' => 'stub', 'HMAP_HRMO_STUB_USER_ROLE' => 'Analyst',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);

$weeks = [];
for ($w = 1; $w <= 52; $w++) {
    $req = Illuminate\Http\Request::create('/api/weekly-summary', 'GET',
        ['morbidity_year' => $year, 'morbidity_week' => $w], [], [], ['HTTP_ACCEPT' => 'application/json']);
    $t0 = microtime(true);
    $resp = $kernel->handle($req);
    $ms = (microtime(true) - $t0) * 1000;
    if ($resp->getStatusCode() !== 200) {
        fwrite(STDERR, "week $w: HTTP {$resp->getStatusCode()} {$resp->getContent()}\n");
        exit(1);
    }
    $weeks[$w] = json_decode($resp->getContent(), true) + ['response_ms' => round($ms, 1)];
}
file_put_contents($out, json_encode(['year' => $year, 'weeks' => $weeks], JSON_PRETTY_PRINT));
echo "wrote weeks 1-52 of $year to $out\n";
