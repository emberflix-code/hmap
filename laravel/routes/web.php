<?php

use Illuminate\Support\Facades\Route;

// In dev we serve the SPA shell at both / and /hmap/* so the React Router
// behaves the same as it will in prod (mounted under /hmap on the HRIS portal).
// Nginx is responsible for stripping the /hmap prefix from REQUEST_URI on
// the deployed server so Laravel sees clean paths (/api/whoami, not
// /hmap/api/whoami). See docs/DEPLOYMENT.md.
Route::get('/', function () { return redirect('/hmap'); });
Route::get('/hmap/{any?}', function () { return view('hmap'); })
    ->where('any', '.*');
