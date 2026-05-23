<?php

return [

    'ml_url' => env('HMAP_ML_URL', 'http://127.0.0.1:5000'),

    'hrmo' => [
        /*
         | Mode controls how HrmoSessionAuth resolves the current user.
         |   'stub' - reads HMAP_HRMO_STUB_* below. Dev only.
         |   'php'  - reads $_SESSION via session.save_path shared with the
         |            HRIS Portal. Same-machine deployments only. Deprecated
         |            in favor of 'jwt'.
         |   'jwt'  - calls HRMO's REST API (POST /api/v1/auth/login,
         |            GET /api/v1/auth/me). Standard architecture per Ch.3.
         */
        'mode' => env('HMAP_HRMO_MODE', 'stub'),

        // ── stub mode ──
        'stub_user_id'   => (int) env('HMAP_HRMO_STUB_USER_ID', 1),
        'stub_user_name' => env('HMAP_HRMO_STUB_USER_NAME', 'Dev User'),
        'stub_user_role' => env('HMAP_HRMO_STUB_USER_ROLE', 'Administrator'),

        // ── php mode (legacy) ──
        'session_save_path' => env('HMAP_HRMO_SESSION_PATH', '/var/lib/php/sessions'),
        'session_cookie'    => env('HMAP_HRMO_SESSION_COOKIE', 'PHPSESSID'),

        // ── jwt mode ──
        'api_base'      => rtrim(env('HRMO_API_BASE', 'https://hrmo.paranaque.gov.ph/api/v1'), '/'),
        // Name of the HttpOnly cookie H-MAP issues to the browser holding the
        // HRMO-issued JWT. Distinct from PHPSESSID to avoid collision with HRMO.
        'jwt_cookie'    => env('HMAP_JWT_COOKIE', 'hmap_jwt'),
        // /auth/me response cache TTL in seconds (per-IP+token). Reduces
        // round-trips to HRMO during a dashboard session.
        'me_cache_ttl'  => (int) env('HMAP_ME_CACHE_TTL', 300),
        // Map HRMO role strings to H-MAP's 3-tier enum.
        'role_map' => [
            'superadmin' => 'Administrator',
            'admin'      => 'Administrator',
            'hrmo'       => 'Analyst',
            'manager'    => 'Analyst',
            'employee'   => 'Encoder',
            'guest'      => 'Encoder',
        ],
        'default_role' => env('HMAP_DEFAULT_ROLE', 'Encoder'),
    ],

];
