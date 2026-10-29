<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\BackupsController;
use App\Http\Controllers\CaseEntryController;
use App\Http\Controllers\ClustersController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\MfaController;
use App\Http\Controllers\MlProxyController;
use App\Http\Controllers\RecommendationsController;
use App\Http\Controllers\ReportsController;
use App\Http\Middleware\HrmoSessionAuth;
use Illuminate\Support\Facades\Route;

// Public — login endpoint MUST sit outside the hrmo middleware (otherwise
// nobody could ever log in).
Route::post('/auth/login',  [AuthController::class, 'login']);
Route::post('/auth/logout', [AuthController::class, 'logout']);  // safe to invoke without a session

// Second login step: HRMO password and CESU authorization already passed,
// one-time code not yet entered. Every route below the next group needs it.
Route::middleware('hrmo:' . HrmoSessionAuth::MFA_PENDING)->prefix('auth/mfa')->group(function () {
    Route::get('/status',          [MfaController::class, 'status']);
    Route::post('/enroll',         [MfaController::class, 'enroll']);
    Route::post('/enroll/confirm', [MfaController::class, 'confirm']);
    Route::post('/verify',         [MfaController::class, 'verify']);
});

// All H-MAP API routes are HRMO-gated. The `hrmo` middleware attaches
// hmap.employee_id / hmap.employee_name / hmap.role to the request.
Route::middleware('hrmo')->group(function () {

    Route::get('/auth/me', [AuthController::class, 'me']);

    // Reference data
    Route::get('/barangays', [DashboardController::class, 'barangays']);
    Route::get('/diseases',  [DashboardController::class, 'diseases']);

    // KPI strip at top of dashboard
    Route::get('/summary', [DashboardController::class, 'summary']);

    // Surveillance data (direct MySQL reads)
    Route::get('/weekly-series', [DashboardController::class, 'weeklySeries']);
    Route::get('/thresholds',    [DashboardController::class, 'thresholds']);
    Route::get('/heatmap-week',  [DashboardController::class, 'heatmapWeek']);
    // Module 6 — rule-based barangay risk tiers (replaces the retired Random Forest)
    Route::get('/risk-tiers',    [DashboardController::class, 'riskTiers'])->middleware('hrmo:Analyst');
    // Module 6 — resource allocation recommendations from the rule table
    Route::get('/recommendations', [RecommendationsController::class, 'index'])->middleware('hrmo:Analyst');
    Route::post('/recommendations/{id}/action', [RecommendationsController::class, 'action'])
        ->whereNumber('id')->middleware('hrmo:Analyst');
    Route::get('/recommendation-rules', [RecommendationsController::class, 'rules'])->middleware('hrmo:Analyst');
    Route::post('/recommendation-rules', [RecommendationsController::class, 'storeRule'])->middleware('hrmo:Administrator');
    Route::put('/recommendation-rules/{id}', [RecommendationsController::class, 'updateRule'])
        ->whereNumber('id')->middleware('hrmo:Administrator');
    Route::post('/recommendation-rules/{id}/validate', [RecommendationsController::class, 'validateRule'])
        ->whereNumber('id')->middleware('hrmo:Administrator');

    // CESU PIDSR workbook parity views (Summary Weekly Update, PIDSRMain, SBgy)
    Route::get('/weekly-summary',  [DashboardController::class, 'weeklySummary']);
    Route::get('/dengue-detail',   [DashboardController::class, 'dengueDetail']);
    Route::get('/barangay-rates',  [DashboardController::class, 'barangayRates']);
    Route::get('/dengue-memo',     [DashboardController::class, 'dengueMemo']);

    // Identity echo (useful for the frontend to confirm session + role)
    Route::get('/whoami', [DashboardController::class, 'whoami']);

    // ML proxy → FastAPI at 127.0.0.1:5000
    Route::get('/ml/health',         [MlProxyController::class, 'health']);
    Route::get('/ml/models',         [MlProxyController::class, 'models']);
    Route::post('/ml/forecast',      [MlProxyController::class, 'forecast']);
    Route::post('/geocode',          [MlProxyController::class, 'geocode']);

    // Dengue cluster surveillance — CESU 200m / >=3 / 4-week rule.
    // Read-only; detection is offline via ml/detect_clusters.py.
    Route::get('/clusters/latest-run',  [ClustersController::class, 'latestRun']);
    Route::get('/clusters',             [ClustersController::class, 'index']);
    Route::get('/clusters/{clusterId}', [ClustersController::class, 'show'])
        ->whereNumber('clusterId');

    // Module 1 — Case data entry (Encoder+ only; `hrmo:Encoder` is implicit
    // because the bare `hrmo` middleware already admits only CESU staff with
    // an active user_roles row, and Encoder is the lowest role).
    Route::post('/cases',      [CaseEntryController::class, 'store']);
    Route::post('/cases/bulk', [CaseEntryController::class, 'bulk']);

    // Module 5 — Reports and data export. Tiered by role per Ch.3 spec.
    Route::get('/export/my-entries',      [ReportsController::class, 'myEntries']);
    Route::get('/export/disease-summary', [ReportsController::class, 'diseaseSummary'])->middleware('hrmo:Analyst');
    Route::get('/export/full-registry',   [ReportsController::class, 'fullRegistry'])->middleware('hrmo:Administrator');

    // Module 9 — backup register (read-only; backups run from cron via ml/backup_db.py)
    Route::get('/admin/backups', [BackupsController::class, 'index'])->middleware('hrmo:Administrator');
});
