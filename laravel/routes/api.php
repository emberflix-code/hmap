<?php

use App\Http\Controllers\AuthController;
use App\Http\Controllers\CaseEntryController;
use App\Http\Controllers\ClustersController;
use App\Http\Controllers\DashboardController;
use App\Http\Controllers\MlProxyController;
use App\Http\Controllers\ReportsController;
use Illuminate\Support\Facades\Route;

// Public — login endpoint MUST sit outside the hrmo middleware (otherwise
// nobody could ever log in).
Route::post('/auth/login',  [AuthController::class, 'login']);
Route::post('/auth/logout', [AuthController::class, 'logout']);  // safe to invoke without a session

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
    Route::post('/ml/risk', [MlProxyController::class, 'risk'])->middleware('hrmo:Analyst');
    Route::post('/geocode',          [MlProxyController::class, 'geocode']);

    // Dengue cluster surveillance — CESU 200m / >=3 / 4-week rule.
    // Read-only; detection is offline via ml/detect_clusters.py.
    Route::get('/clusters/latest-run',  [ClustersController::class, 'latestRun']);
    Route::get('/clusters',             [ClustersController::class, 'index']);
    Route::get('/clusters/{clusterId}', [ClustersController::class, 'show'])
        ->whereNumber('clusterId');

    // Module 1 — Case data entry (Encoder+ only; the middleware echo `hrmo:Encoder`
    // is implicit because the bare `hrmo` middleware already validates an active
    // employee, and any active employee defaults to Encoder).
    Route::post('/cases',      [CaseEntryController::class, 'store']);
    Route::post('/cases/bulk', [CaseEntryController::class, 'bulk']);

    // Module 5 — Reports and data export. Tiered by role per Ch.3 spec.
    Route::get('/export/my-entries',      [ReportsController::class, 'myEntries']);
    Route::get('/export/disease-summary', [ReportsController::class, 'diseaseSummary'])->middleware('hrmo:Analyst');
    Route::get('/export/full-registry',   [ReportsController::class, 'fullRegistry'])->middleware('hrmo:Administrator');
});
