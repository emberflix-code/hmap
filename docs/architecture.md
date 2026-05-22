# H-MAP Architecture

## Deployment topology

H-MAP runs as a **path-mounted application** inside the existing HRIS Portal nginx server. There is no separate domain, no separate certificate, no separate server VM. This is intentional and matches the thesis premise of leveraging existing DICT-provisioned infrastructure.

```
hrmo.paranaque.gov.ph (single nginx server block, single Let's Encrypt cert)
├── /hris/*           → HRIS Portal (plain PHP, /var/www/html/hrmo)
├── /hmap/*           → H-MAP frontend bundle (static) + Laravel API
│   ├── /hmap/api/*           → Laravel 11 (PHP 8.x FPM)
│   │   ├── /hmap/api/ml/*        → MlProxyController → FastAPI on localhost:5000
│   │   └── /hmap/api/geocode     → MlProxyController → FastAPI geocode endpoint
│   └── (everything else)     → Laravel serves the SPA shell (welcome.blade.php variant)
└── /                 → 301 to /hris/
```

In dev the same topology is mimicked with `php artisan serve` on 8000, `uvicorn` on 5000, and `vite` on 5173 (the Blade view's `@vite` directive points to Vite for HMR; in prod Vite produces a static bundle that Laravel serves directly).

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

Implementation: [HrmoSessionAuth.php](../laravel/app/Http/Middleware/HrmoSessionAuth.php). Has two modes:

- **`stub`** (dev) — reads `HMAP_HRMO_STUB_USER_*` from `.env` and short-circuits the session lookup. Lets you build the dashboard without standing up the HRIS portal locally.
- **`php`** (prod) — reads `$_COOKIE['PHPSESSID']`, opens the corresponding session file at `session.save_path`, reads `$_SESSION['user_id']`, then validates against `hrmo_evaluation_db.users` to confirm the employee is still ACTIVE. If yes → request continues. If no → 401 JSON (for API routes) or 302 redirect to `/hris/login`.

H-MAP NEVER writes to `hrmo_evaluation_db`. H-MAP reads only one table: `users` (id, email, full_name, status). Disease surveillance data lives in a separate database (`hmap_db`).

### Two-layer RBAC

| Layer | What it checks | Failure mode |
|---|---|---|
| **Layer 1: active employment** | The HRIS portal `users.status = 'ACTIVE'` per-request (not cached) | 401, redirect to `/hris/login` |
| **Layer 2: H-MAP role** | `hmap_db.user_roles.role ∈ {Encoder, Analyst, Administrator}` for the route-required minimum | 403, JSON `{error: "forbidden", detail: "Requires role X; you are Y"}` |

Role gates are declared per-route via middleware parameters:

```php
Route::post('/ml/risk',   [...])->middleware('hrmo:Analyst');         // Analyst+
Route::get('/export/full-registry', [...])->middleware('hrmo:Administrator'); // Admin only
```

The bare `hrmo` middleware (no parameter) only checks layer 1 — useful for Encoder-friendly routes like the dashboard data fetches.

## Database split

| Database | Owner | Purpose |
|---|---|---|
| `hrmo_evaluation_db` | HRIS Portal | Auth, users, HR data. H-MAP reads `users` only. |
| `hmap_db` | H-MAP | All disease surveillance data — cases, barangays, diseases, predictions, clusters, audit log. |
| `paranaquehris_production` | HRIS source-of-truth (read-only) | Not touched by H-MAP. |

Grants on the MySQL server enforce the boundary at the engine level:

```sql
-- The actual grants in production (see also docs/quickstart.md):
CREATE USER 'hmap_app'@'%' IDENTIFIED BY '...';
GRANT ALL PRIVILEGES ON hmap_db.* TO 'hmap_app'@'%';
GRANT SELECT ON hrmo_evaluation_db.users TO 'hmap_app'@'%';
FLUSH PRIVILEGES;
```

## `hmap_db` schema (11 tables)

Authoritative source: [ml/schema.sql](../ml/schema.sql). Ch.3 of the thesis specifies 9 tables (Figs 3–10 + threshold table). The two **new** tables added since the thesis text are flagged below; see [CHAPTERS_1_TO_3_REVISIONS.md](CHAPTERS_1_TO_3_REVISIONS.md) for the thesis patch.

| Table | Rows (current) | Purpose |
|---|---|---|
| `diseases` | 29 | PIDSR notifiable disease reference (28 spec + COVID-19) |
| `barangays` | 16 | Parañaque barangay reference with PSA-2020 population + OSM centroids |
| `facilities` | seeded as needed | Health centers / sentinel sites |
| `cases` | 35,164 | PIDSR line list — central transaction table |
| `case_addresses` | 1:1 with cases (when geocoded) | **NEW.** Street address + geocoded lat/lng + precision source. Split from `cases` so it has its own RBAC policy (Encoders write own, only Analyst+ read all). |
| `thresholds` | 340 | WHO EWARN per (disease, morbidity_week) for the alerting year |
| `ai_predictions` | growing | Audit log of Prophet forecasts + RF risk classifications |
| `detection_runs` | growing | **NEW.** One row per `ml/detect_clusters.py` invocation; stores params + summary stats for reproducibility |
| `case_clusters` | 2,234 (latest run) | **NEW.** Detected dengue clusters, fingerprinted by SHA1(sorted member case_ids) for cross-window deduplication |
| `case_cluster_members` | M:N | **NEW.** Junction table linking cases to clusters |
| `user_roles` | per active employee | RBAC role assignments |
| `audit_log` | growing | RA 10173 compliance — every INSERT/UPDATE/DELETE/EXPORT/AI_REQUEST/LOGIN |
| `excluded_cases` | 542 | Audit table for rows the ETL rejected (out-of-city, unknown barangay) |
| `geocode_cache` | growing | Address-string → (lat, lng, source) memo. **Persists across schema reloads** to avoid re-hitting Nominatim's 1 req/sec limit. |

## Module structure (functional modules, per current implementation)

| Module | Backend | Frontend | Documentation |
|---|---|---|---|
| 1. Data Digitization | [CaseEntryController.php](../laravel/app/Http/Controllers/CaseEntryController.php) | [CaseEntry.jsx](../laravel/resources/js/hmap/CaseEntry.jsx) | — |
| 2. Heat Map | [DashboardController::heatmapWeek](../laravel/app/Http/Controllers/DashboardController.php) + [/api/clusters](../laravel/app/Http/Controllers/ClustersController.php) | [HeatMapPanel.jsx](../laravel/resources/js/hmap/HeatMapPanel.jsx) | — |
| 3. Trend Monitoring + EWARN | [DashboardController::weeklySeries+thresholds](../laravel/app/Http/Controllers/DashboardController.php), [ml/compute_thresholds.py](../ml/compute_thresholds.py) | [TrendChartPanel.jsx](../laravel/resources/js/hmap/TrendChartPanel.jsx), [KpiStrip.jsx](../laravel/resources/js/hmap/KpiStrip.jsx) | [thresholds.md](thresholds.md) |
| 4. AI Prediction | [ml/main.py](../ml/main.py) (FastAPI), [ml/train_prophet.py](../ml/train_prophet.py), [ml/train_rf.py](../ml/train_rf.py) | [ForecastPanel.jsx](../laravel/resources/js/hmap/ForecastPanel.jsx) | [prophet.md](prophet.md), [random_forest.md](random_forest.md) |
| 5. Reports & Export | [ReportsController.php](../laravel/app/Http/Controllers/ReportsController.php) | [Reports.jsx](../laravel/resources/js/hmap/Reports.jsx) | — |
| **6. Cluster Detection (NEW)** | [ml/detect_clusters.py](../ml/detect_clusters.py), [ml/geocode.py](../ml/geocode.py), [ClustersController.php](../laravel/app/Http/Controllers/ClustersController.php) | (heat map overlay) | [cluster_detection.md](cluster_detection.md), [geocoding.md](geocoding.md) |

## ML layer (FastAPI on 127.0.0.1:5000)

The FastAPI service ([ml/main.py](../ml/main.py)) loads all `*.pkl` models at startup and exposes:

| Endpoint | Backed by | Notes |
|---|---|---|
| `GET /health` | n/a | Cheap liveness check |
| `GET /models` | model registry | Lists all 25 Prophet + 6 RF models with their validation MAPE/accuracy |
| `POST /predict/forecast` | Prophet | Resolves (disease, optional barangay) → per-barangay model or city-wide fallback |
| `POST /predict/risk` | Random Forest | 16-barangay risk classification with class probabilities |
| `POST /geocode` | [ml/geocode.py](../ml/geocode.py) | Nominatim cascade, cache-backed. See [geocoding.md](geocoding.md). |

The service is bound to `127.0.0.1` only. Laravel proxies authenticated requests via Guzzle in [MlProxyController.php](../laravel/app/Http/Controllers/MlProxyController.php); the frontend never talks to FastAPI directly. This means HRMO session enforcement happens once, at Laravel.

## Why this layout (defends against thesis Q&A)

| Anticipated question | Answer |
|---|---|
| "Why path-mount instead of a subdomain?" | Reuses HRIS Portal's SSL cert and DICT-provisioned server with no procurement cost. Subdomain would require additional DNS work and certificate issuance, contradicting the "cost-effective deployment" premise. |
| "How is access restricted to active employees only?" | Shared PHP session + real-time validation against HRMO's `users` table. An inactive employee's session is invalidated on next request because the `status` column is checked per-call, not cached. |
| "Why Laravel 11 when the thesis says PHP?" | Laravel is a PHP framework. The deployment is still PHP. Laravel provides routing, ORM, middleware, and dependency injection — all absent from the host HRIS Portal codebase — but it does not change the language. |
| "Why FastAPI when the thesis says Flask?" | Both are Python microframeworks. FastAPI gives us Pydantic input validation, automatic OpenAPI docs, and async I/O for the Nominatim cascade — wins that materially affect this system. The Python runtime, model pickling, and the request/response contract are identical to what a Flask implementation would produce. |
| "Why MySQL when PostGIS would be better for spatial?" | MySQL is what's already running on the DICT server. Adding PostgreSQL would mean a second DB engine to maintain. Spatial work we do (DBSCAN on coordinates, point-in-polygon for choropleth) runs in Python against `case_addresses.case_lat/lng`, not in SQL — so we don't actually need PostGIS. |
| "How does H-MAP handle the Python service in production?" | Runs as `hmap-ml.service` under systemd, bound to 127.0.0.1:5000. Not exposed externally. Laravel proxies authenticated requests via Guzzle. |
| "How is cluster detection different from the EWARN threshold?" | EWARN compares barangay-aggregated weekly counts to a baseline (`μ + 2σ`); it cannot detect clusters that straddle barangay boundaries. Cluster detection runs DBSCAN on geocoded case coordinates and identifies spatially-tight groups regardless of administrative boundaries — 12.9% of the 2,234 detected dengue clusters are cross-barangay. See [cluster_detection.md](cluster_detection.md). |

## Periodic refresh — when to re-run what

H-MAP has four offline jobs that need to run on different cadences. None of them are wired to cron yet (deferred to v2 per the open-questions table below); for now you run them manually after the relevant trigger event.

| Script | When to re-run | Why | Touches |
|---|---|---|---|
| [`python ml/etl_registry.py`](../ml/etl_registry.py) | When CESU sends a new PIDSR Registry Excel export | Replaces all data in `hmap_db.cases` from `docs/PIDSR Report YR NNNN.xlsx` (auto-picks newest by year-in-filename). Geocode cache is preserved across runs. | `cases`, `diseases`, `barangays`, `excluded_cases` |
| [`python ml/compute_thresholds.py`](../ml/compute_thresholds.py) | After every ETL run, AND once at the start of each new calendar year | WHO EWARN thresholds depend on the 5-year rolling baseline; the baseline window shifts annually and the means/SDs change as new cases land in the baseline window. | `thresholds` (TRUNCATE + recompute) |
| [`python ml/train_prophet.py`](../ml/train_prophet.py) + [`python ml/train_rf.py`](../ml/train_rf.py) | After every ETL run, OR whenever the holdout window changes | Re-fits all 25 Prophet pickles + 6 RF pickles and writes evaluation reports to `ml/reports/*_eval_*.json`. FastAPI service must restart to pick up new pickles. | `ml/models/*.pkl`, `ml/reports/*.json+csv` |
| [`python ml/detect_clusters.py`](../ml/detect_clusters.py) | After every ETL run, AND after a batch of new case entries (DBSCAN is offline, not per-case) | Re-detects clusters under CESU's 200m / ≥3 / 4-week rule. Each invocation writes a new `detection_runs` row; the Laravel `/api/clusters/latest-run` route always returns the most recent. | `detection_runs`, `case_clusters`, `case_cluster_members` |

Idempotency notes:
- `etl_registry.py` is idempotent — re-running drops + reloads `cases` cleanly. Audit-trail `excluded_cases` and `geocode_cache` survive.
- `compute_thresholds.py` `TRUNCATE`s `thresholds` before inserting, so re-runs are safe.
- The train scripts overwrite their pickle outputs but append timestamped report files (so historical evaluations can be diff'd).
- `detect_clusters.py` appends to `detection_runs` rather than overwriting, so parameter-sensitivity sweeps (different `--eps`, `--min`, `--weeks` values) accumulate side-by-side for the evaluation chapter.

A nightly cron / Laravel scheduler entry that runs all four in order after the day's PIDSR ingest is on the v2 roadmap (see "Open architectural questions" below).

## Open architectural questions — RESOLVED

The original Ch.3 left four open questions. Three are now closed; one remains.

| Question | Resolution |
|---|---|
| ~~Frontend routing — Laravel routes or pure SPA?~~ | **SPA.** Laravel serves [hmap.blade.php](../laravel/resources/views/hmap.blade.php) for `/hmap/{any?}` and the React SPA owns view state via a tiny `view` reducer in [App.jsx](../laravel/resources/js/hmap/App.jsx). No `react-router` dependency. |
| ~~Barangay GeoJSON source~~ | **OpenStreetMap admin_level=10 relations**, fetched via Overpass API by [ml/fetch_barangay_geojson.py](../ml/fetch_barangay_geojson.py). 16/16 matched, ~120KB. Stored at [laravel/public/barangays.geojson](../laravel/public/barangays.geojson). |
| ~~Historical data import~~ | **`docs/PIDSR Report YR 2026.xlsx`, sheet `Registry`**, loaded by [ml/etl_registry.py](../ml/etl_registry.py) with the normalization rules in [data_mappings.md](data_mappings.md). 35,164 rows post-normalization. |
| ML model lifecycle | Still **on-demand via CLI** (`python ml/train_prophet.py`). No cron yet. Production cron job + Administrator-panel button are deferred to v2. |
