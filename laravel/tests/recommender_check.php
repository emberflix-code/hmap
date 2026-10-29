<?php
// End-to-end check of the resource allocation recommender (Module 6) against a
// THROWAWAY MariaDB on 127.0.0.1:3399 (root / migtest). Never point it at a
// real database: it rewrites hmap_db there. Setup, from the repository root:
//
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < ml/schema.sql
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < laravel/tests/fixtures/recommender_seed.sql
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest hmap_db < ml/migrations/2026_10_30_recommendations.sql
//   php laravel/tests/recommender_check.php          (exit code 0 = all passed)
//
// The fixture is built so every expected result is known in advance: dengue
// in Baclaran above threshold with a hotspot (High), Tambo above threshold
// only (Moderate), Vitalez quiet (Low); one measles case; a disease without
// rules (fallback).

$root = dirname(__DIR__);
foreach ([
    'APP_ENV' => 'testing', 'DB_CONNECTION' => 'mysql', 'DB_HOST' => '127.0.0.1', 'DB_PORT' => '3399',
    'DB_DATABASE' => 'hmap_db', 'DB_USERNAME' => 'root', 'DB_PASSWORD' => 'migtest',
    'CACHE_STORE' => 'array', 'HMAP_HRMO_MODE' => 'stub', 'HMAP_HRMO_STUB_USER_ROLE' => 'Administrator',
    'HMAP_HRMO_STUB_USER_ID' => '1001',
] as $k => $v) {
    putenv("$k=$v"); $_ENV[$k] = $v; $_SERVER[$k] = $v;
}
require $root . '/vendor/autoload.php';
$app = require $root . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Http\Kernel::class);
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

use Illuminate\Support\Facades\DB;

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
function recs($code) {
    return call('GET', "/recommendations?disease_code=$code&year=2025&week=30");
}
function byName($r, $name) {
    foreach ($r['barangays'] as $b) if ($b['barangay_name'] === $name) return $b;
    return null;
}
function item($b, $needle) {
    foreach ($b['items'] as $i) if (strpos($i['item'], $needle) !== false) return $i;
    return null;
}

echo "seeded rule table\n";
$counts = DB::table('recommendation_rules')->count();
// only DENGUE (7), MEA (5) and the 2 fallback rules exist in this test database
check('draft rules seeded for diseases present (14)', $counts === 14, $counts);
check('all seeded rules are Draft', DB::table('recommendation_rules')->where('status', '!=', 'Draft')->count() === 0);

echo "dengue, 2025 week 30\n";
[$s, $r] = recs('DENGUE');
check('200 OK', $s === 200, json_encode($r));
$names = array_column($r['barangays'], 'barangay_name');
check('only flagged barangays, ranked High first', $names === ['Baclaran', 'Tambo'], json_encode($names));
$bac = byName($r, 'Baclaran'); $tam = byName($r, 'Tambo');
check('Baclaran High (above threshold + hotspot)', $bac['tier'] === 'High' && $bac['rank'] === 1, json_encode($bac['reasons']));
check('Tambo Moderate (above threshold only)', $tam['tier'] === 'Moderate' && $tam['rank'] === 2);
check('Baclaran gets 5 Moderate + 2 High rules', count($bac['items']) === 7, count($bac['items']));
check('Tambo gets the 5 Moderate rules only', count($tam['items']) === 5, count($tam['items']));
check('active cases = 4-week window, Confirmed+Probable', $bac['active_cases'] === 7 && $tam['active_cases'] === 3,
      $bac['active_cases'] . '/' . $tam['active_cases']);
check('NS1 kits scale per case (7 and 3)', item($bac, 'NS1')['quantity'] === 7 && item($tam, 'NS1')['quantity'] === 3);
check('as-assessed items have no quantity', item($bac, 'Oral rehydration')['quantity'] === null);
check('fogging only for the High barangay', item($bac, 'fogging') !== null && item($tam, 'fogging') === null);
check('items carry source and Draft status', item($bac, 'fogging')['source'] !== '' && item($bac, 'fogging')['rule_status'] === 'Draft');
check('uses disease rules, not fallback', $r['uses_fallback_rules'] === false);
[$s, $again] = recs('DENGUE');
check('regenerating is idempotent', DB::table('recommendations')->where('disease_id', 1)->count() === 12
      && array_column($again['barangays'], 'barangay_name') === $names);

echo "measles (single-case trigger) and fallback rules\n";
[, $m] = recs('MEA');
$vit = byName($m, 'Vitalez');
check('one measles case flags Vitalez Moderate', $vit && $vit['tier'] === 'Moderate' && count($m['barangays']) === 1);
check('vitamin A: 2 doses per case', item($vit, 'Vitamin A')['quantity'] === 2);
[, $a] = recs('ABD');
check('disease without rules uses fallback rules', $a['uses_fallback_rules'] === true
      && count(byName($a, 'Tambo')['items']) === 1, json_encode($a));

echo "recording actions\n";
$fog = item($bac, 'fogging'); $adv = item($bac, 'Advise hospitals');
[$s] = call('POST', "/recommendations/{$fog['recommendation_id']}/action", ['action_status' => 'Acted', 'action_note' => 'Fogging done 2025-07-25']);
check('action recorded', $s === 200 && DB::table('recommendations')->where('recommendation_id', $fog['recommendation_id'])->value('action_by') == 1001);
[$s] = call('POST', "/recommendations/{$fog['recommendation_id']}/action", ['action_status' => 'Done']);
check('invalid status rejected', $s === 422, $s);

echo "hotspot ends: Baclaran drops to Moderate\n";
DB::table('case_clusters')->delete();
[, $r2] = recs('DENGUE');
$bac2 = byName($r2, 'Baclaran');
check('Baclaran now Moderate', $bac2['tier'] === 'Moderate');
$fog2 = item($bac2, 'fogging');
check('acted High item kept, marked no longer applying', $fog2 && $fog2['action_status'] === 'Acted' && $fog2['still_applies'] === false);
check('pending High item removed', item($bac2, 'Advise hospitals') === null
      && !DB::table('recommendations')->where('recommendation_id', $adv['recommendation_id'])->exists());

echo "rule maintenance\n";
$ns1 = DB::table('recommendation_rules')->where('item', 'like', '%NS1%')->value('rule_id');
[$s, $v] = call('POST', "/recommendation-rules/$ns1/validate");
check('Administrator validates a rule', $s === 200 && $v['status'] === 'Validated' && $v['validated_by'] == 1001);
[$s, $v] = call('PUT', "/recommendation-rules/$ns1", ['notes' => 'Stock at all 16 health centers']);
check('notes-only edit keeps Validated', $s === 200 && $v['status'] === 'Validated');
[$s, $v] = call('PUT', "/recommendation-rules/$ns1", ['quantity_factor' => 1.5]);
check('content edit returns rule to Draft', $s === 200 && $v['status'] === 'Draft' && $v['validated_by'] === null);
[, $r3] = recs('DENGUE');
check('new factor applied (ceil 1.5 x 7 = 11)', item(byName($r3, 'Baclaran'), 'NS1')['quantity'] === 11);
[$s] = call('POST', '/recommendation-rules', ['disease_id' => 1, 'risk_tier' => 'Moderate', 'category' => 'IEC',
    'item' => 'Flyers', 'scaling_basis' => 'per_1000_pop', 'source' => 'test']);
check('rule with a scaling basis needs a factor', $s === 422, $s);
[$s, $new] = call('POST', '/recommendation-rules', ['disease_id' => 1, 'risk_tier' => 'Moderate', 'category' => 'IEC',
    'item' => 'Dengue flyers per household', 'scaling_basis' => 'per_1000_pop', 'quantity_factor' => 0.5,
    'unit' => 'bundles', 'source' => 'test']);
check('rule created as Draft', $s === 201 && $new['status'] === 'Draft');
[, $r4] = recs('DENGUE');
check('per 1,000 residents: Tambo ceil(0.5 x 28.251) = 15', item(byName($r4, 'Tambo'), 'flyers')['quantity'] === 15);
[$s] = call('PUT', "/recommendation-rules/{$new['rule_id']}", ['is_active' => false]);
[, $r5] = recs('DENGUE');
check('deactivated rule disappears (pending items removed)', $s === 200 && item(byName($r5, 'Tambo'), 'flyers') === null);
[$s, $list] = call('GET', '/recommendation-rules');
check('rule table lists all rules', $s === 200 && count($list) === 15, count($list));

echo "roles\n";
config(['hmap.hrmo.stub_user_role' => 'Analyst']);
check('Analyst can view recommendations', recs('DENGUE')[0] === 200);
check('Analyst cannot edit rules', call('PUT', "/recommendation-rules/$ns1", ['notes' => 'x'])[0] === 403);
config(['hmap.hrmo.stub_user_role' => 'Encoder']);
check('Encoder cannot view recommendations', recs('DENGUE')[0] === 403);

echo "audit log\n";
$actions = DB::table('audit_log')->pluck('action_type')->countBy()->all();
echo '  ' . json_encode($actions) . "\n";
foreach (['RECOMMENDATION_ACTION', 'RULE_VALIDATE', 'RULE_UPDATE', 'RULE_CREATE'] as $act) {
    check("audit has $act", isset($actions[$act]));
}

echo $fail ? "\n$fail FAILED\n" : "\nall passed\n";
exit($fail ? 1 : 0);
