# H-MAP Architecture

## Deployment topology

H-MAP runs as a **path-mounted application** inside the existing HRIS Portal nginx server. There is no separate domain, no separate certificate, no separate server VM. This is intentional and matches the thesis premise of leveraging existing DICT-provisioned infrastructure.

```
hrmo.paranaque.gov.ph (single nginx server block, single Let's Encrypt cert)
├── /hris/*           → HRIS Portal (plain PHP, /var/www/html/hrmo)
├── /hmap/*           → H-MAP frontend bundle (static) + Laravel API
│   ├── /hmap/api/*   → Laravel 11 (PHP 8.3 FPM)
│   └── /hmap/ml/*    → FastAPI proxy (uvicorn on 127.0.0.1:5000, systemd service)
└── /                 → 301 to /hris/
```

## Cross-app authentication (the load-bearing piece)

The thesis's RA 10173 compliance argument hinges on H-MAP reusing HRIS Portal's authentication. That means H-MAP itself does NOT have a login screen — if you're not already logged into HRIS Portal as an active employee, you get bounced to `/hris/login`.

**Mechanism: shared PHP session storage.**

| Setting | HRIS Portal | H-MAP (Laravel) |
|---|---|---|
| Session driver | PHP native (`session.save_handler=files`) | Override Laravel's default; use PHP native sessions to align |
| `session.save_path` | `/var/lib/php/sessions/` (system default) | Same path |
| Cookie name | `PHPSESSID` (PHP default) | Same |
| Cookie path | `/` | `/` |
| Cookie domain | `hrmo.paranaque.gov.ph` | Same |

When a request hits `/hmap/api/*`, Laravel's first middleware reads `$_COOKIE['PHPSESSID']`, opens the corresponding session file, and reads `$_SESSION['user_id']`. It then validates against `hrmo_evaluation_db.users` (the HRIS Portal DB, **read-only** from H-MAP's perspective) to confirm the user still has an active session. If yes → user is authenticated. If no → 401, frontend redirects to `/hris/login`.

H-MAP NEVER writes to `hrmo_evaluation_db`. H-MAP reads only one table: `users` (id, email, full_name, status). Disease surveillance data lives in a separate database (`hmap_db`).

## Database split

| Database | Owner | Purpose |
|---|---|---|
| `hrmo_evaluation_db` | HRIS Portal | Auth, users, HR data. H-MAP reads `users` only. |
| `hmap_db` | H-MAP | All disease surveillance data — cases, barangays, diseases, predictions, audit log. |
| `paranaquehris_production` | HRIS source-of-truth (read-only) | Not touched by H-MAP. |

Two separate MySQL users so the DB engine enforces the boundary:
- `hmap_app` — full access to `hmap_db.*`, SELECT-only on `hrmo_evaluation_db.users`
- `hris_app` — full access to `hrmo_evaluation_db.*`, no access to `hmap_db`

## Module structure (thesis Functional Modules)

| Module | Where it lives |
|---|---|
| 1. HRMO-integrated authentication | `laravel/app/Http/Middleware/HrmoSessionAuth.php` |
| 2. Weekly case data ingestion | `laravel/app/Http/Controllers/IngestController.php` + CSV upload form |
| 3. Heat map visualization (Leaflet + barangay GeoJSON) | `frontend/src/pages/HeatMap.tsx` |
| 4. AI forecasting (Prophet) + barangay risk classification (Random Forest) | `ml/main.py` (FastAPI) |
| 5. Threshold alerting + dashboard reports (Chart.js) | `frontend/src/pages/Dashboard.tsx` + cron job in Laravel |

## Why this layout (defends against thesis Q&A)

| Anticipated question | Answer |
|---|---|
| "Why path-mount instead of a subdomain?" | Reuses HRIS Portal's SSL cert and DICT-provisioned server with no procurement cost. Subdomain would require additional DNS work and certificate issuance, contradicting the "cost-effective deployment" premise. |
| "How is access restricted to active employees only?" | Shared PHP session + real-time validation against HRMO's `users` table. An inactive employee's session is invalidated on next request because the `status` column is checked per-call, not cached. |
| "Why Laravel 11 when the thesis says PHP?" | Laravel is a PHP framework. The deployment is still PHP. Laravel provides routing, ORM, and dependency injection, all of which are absent from the host HRIS Portal codebase, but it does not change the language. |
| "Why MySQL when PostGIS would be better for spatial?" | MySQL is what's already running on the DICT server. Adding PostgreSQL would mean a second DB engine to maintain. MySQL's `ST_Within` and `ST_Distance_Sphere` are sufficient for barangay-level point-in-polygon queries (16 polygons, ~30K points). |
| "How does H-MAP handle the Python service?" | Runs as `hmap-ml.service` under systemd, bound to 127.0.0.1:5000. Not exposed externally. Laravel proxies authenticated requests via Guzzle. |

## Open architectural questions (decide before coding)

- [ ] **Frontend routing**: should `/hmap/dashboard`, `/hmap/heatmap` be Laravel routes that render a React shell, or pure client-side routes inside a single `/hmap` SPA entry point? (Recommendation: SPA, with Laravel only serving `/hmap/api/*` and a single `index.html` for everything else.)
- [ ] **Barangay GeoJSON source**: OpenStreetMap export, PSA shapefile, or hand-traced? Need to decide before the heat-map module is built.
- [ ] **Historical data import**: thesis says "PIDSR data dating back to 2007, ~30K patient-level records." Where is this dataset? CSV from CESU? Direct DB export? Manual entry?
- [ ] **ML model lifecycle**: trained on every ingest? Daily cron? On-demand? (Recommendation: nightly cron after the day's ingest is complete.)
