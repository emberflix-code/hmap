<?php

namespace App\Providers;

use Illuminate\Support\Facades\URL;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register()
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot()
    {
        // Production is served only over HTTPS (Ch.3 Security; nginx redirects
        // http to https). Generate https URLs even if a request reaches PHP
        // without the HTTPS flag, so links and assets never fall back to http.
        if ($this->app->environment('production')) {
            URL::forceScheme('https');
        }
    }
}
