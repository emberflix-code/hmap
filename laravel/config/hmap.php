<?php

return [

    'ml_url' => env('HMAP_ML_URL', 'http://127.0.0.1:5000'),

    'hrmo' => [
        /*
         | Mode controls how HrmoSessionAuth resolves the current user.
         |   'stub' - reads HMAP_HRMO_STUB_* below. Dev only.
         |   'php'  - reads $_SESSION via session.save_path shared with the
         |            HRIS Portal (see docs/architecture.md). Production.
         */
        'mode' => env('HMAP_HRMO_MODE', 'stub'),

        // ── stub mode ──
        'stub_user_id'   => (int) env('HMAP_HRMO_STUB_USER_ID', 1),
        'stub_user_name' => env('HMAP_HRMO_STUB_USER_NAME', 'Dev User'),
        'stub_user_role' => env('HMAP_HRMO_STUB_USER_ROLE', 'Administrator'),

        // ── php mode ──
        // The HRIS Portal's PHP session.save_path. Defaults align with
        // architecture.md but are overridable per host.
        'session_save_path' => env('HMAP_HRMO_SESSION_PATH', '/var/lib/php/sessions'),
        'session_cookie'    => env('HMAP_HRMO_SESSION_COOKIE', 'PHPSESSID'),
    ],

];
