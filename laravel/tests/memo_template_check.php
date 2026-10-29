<?php
// Check of the Administrator-editable weekly dengue memo template, against a
// THROWAWAY MariaDB on 127.0.0.1:3399 (root / migtest). Never point it at a
// real database. Setup, from the repository root:
//
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < ml/schema.sql
//   mysql -h127.0.0.1 -P3399 -uroot -pmigtest < laravel/tests/fixtures/recommender_seed.sql
//   php laravel/tests/memo_template_check.php        (exit code 0 = all passed)

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
function call($method, $uri, $body = [], $role = 'Administrator') {
    global $kernel;
    config(['hmap.hrmo.stub_user_role' => $role]);
    $r = Illuminate\Http\Request::create('/api' . $uri, $method, $method === 'GET' ? $body : [], [], [],
        ['HTTP_ACCEPT' => 'application/json', 'CONTENT_TYPE' => 'application/json'],
        $method === 'GET' || !$body ? null : json_encode($body));
    $resp = $kernel->handle($r);
    return [$resp->getStatusCode(), json_decode($resp->getContent(), true)];
}
function memo() {
    return call('GET', '/dengue-memo', ['morbidity_year' => 2025, 'morbidity_week' => 30], 'Analyst')[1]['memo'] ?? '';
}

echo "default template\n";
$m = memo();
check('memo is addressed to the City Health Office OIC', strpos($m, 'DARIUS J. SEBASTIAN, MD, PHSAE, MPH — Medical Officer V, OIC, City Health Office') !== false);
check('no short name in the memo', strpos($m, 'H-MAP') === false && strpos($m, 'CESU Disease Outbreak Management System') !== false);
check("the week's figures are filled in (11 dengue cases to week 30)", strpos($m, 'There were 11 cases reported') !== false
      && strpos($m, 'Morbidity Week 30') !== false && strpos($m, '{') === false, substr($m, 0, 400));
[$s, $t] = call('GET', '/admin/memo-template');
check('Administrator sees the template, its placeholders and the default', $s === 200 && $t['is_default'] === true
      && count($t['placeholders']) === 17 && $t['body'] === $t['default']);

echo "preview and save\n";
[$s, $p] = call('POST', '/admin/memo-template/preview', ['body' => "Cases: {cases}, week {week}. {bogus}", 'year' => 2025, 'week' => 30]);
check('preview fills a draft template without saving it', $s === 200 && $p['memo'] === 'Cases: 11, week 30. {bogus}'
      && $p['unknown'] === ['bogus'] && DB::table('memo_templates')->count() === 0, json_encode($p));
$new = str_replace("FROM:   DARIUS J. SEBASTIAN, MD, PHSAE, MPH\n        City Epidemiologist",
                   "FROM:   JUANA DELA CRUZ, MD\n        City Epidemiologist", $t['body']);
[$s] = call('PUT', '/admin/memo-template', ['body' => $new]);
check('template saved', $s === 200 && DB::table('memo_templates')->count() === 1);
$m = memo();
check('new drafts use the saved template', strpos($m, 'FROM:   JUANA DELA CRUZ, MD') !== false && strpos($m, 'There were 11 cases') !== false);
[, $t2] = call('GET', '/admin/memo-template');
check('editor shows it is no longer the default', $t2['is_default'] === false && (int) $t2['updated_by'] === 1001);

echo "roles\n";
check('Analysts still generate memos', call('GET', '/dengue-memo', ['morbidity_year' => 2025, 'morbidity_week' => 30], 'Analyst')[0] === 200);
check('Analysts cannot read the template editor', call('GET', '/admin/memo-template', [], 'Analyst')[0] === 403);
check('Encoders cannot change the template', call('PUT', '/admin/memo-template', ['body' => 'x'], 'Encoder')[0] === 403);
check('an empty template is rejected', call('PUT', '/admin/memo-template', ['body' => ''])[0] === 422);

echo "reset and audit\n";
[$s] = call('POST', '/admin/memo-template/reset');
check('restore default', $s === 200 && DB::table('memo_templates')->count() === 0 && strpos(memo(), 'JUANA') === false);
$a = DB::table('audit_log')->where('target_table', 'memo_templates')->get();
check('save and reset logged with old and new text', $a->pluck('action_type')->sort()->values()->all() === ['MEMO_TEMPLATE_RESET', 'MEMO_TEMPLATE_UPDATE']
      && strpos($a->firstWhere('action_type', 'MEMO_TEMPLATE_UPDATE')->new_values, 'JUANA') !== false);

echo $fail ? "\n$fail FAILED\n" : "\nall passed\n";
exit($fail ? 1 : 0);
