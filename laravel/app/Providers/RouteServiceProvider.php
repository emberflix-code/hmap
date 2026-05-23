<?php

namespace App\Providers;

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Foundation\Support\Providers\RouteServiceProvider as ServiceProvider;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\Facades\Route;

class RouteServiceProvider extends ServiceProvider
{
    public const HOME = '/hmap';

    public function boot()
    {
        $this->configureRateLimiting();

        $this->routes(function () {
            Route::prefix('api')
                ->middleware('api')
                ->namespace($this->namespace)
                ->group(base_path('routes/api.php'));

            Route::middleware('web')
                ->namespace($this->namespace)
                ->group(base_path('routes/web.php'));
        });
    }

    protected function configureRateLimiting()
    {
        // 600/min/IP — a single tab switch can fire 6+ endpoints (summary,
        // weekly-series, thresholds, heatmap-week, ml/forecast, ml/risk).
        // The default of 60 was tripping the dashboard's normal use.
        RateLimiter::for('api', function (Request $request) {
            return Limit::perMinute(600)->by($request->ip());
        });
    }
}
