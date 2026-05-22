<?php

use Illuminate\Support\Facades\Route;

// In dev we serve the SPA shell at both / and /hmap/* so the React Router
// behaves the same as it will in prod (mounted under /hmap on the HRIS portal).
Route::get('/', fn () => redirect('/hmap'));
Route::get('/hmap/{any?}', fn () => view('hmap'))->where('any', '.*');
