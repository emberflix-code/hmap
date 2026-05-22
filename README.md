# H-MAP

**Heat Map Disease Surveillance and Outbreak Prediction System**
City Epidemiology Section Unit (CESU), Parañaque City Government

A web-based, AI-assisted disease surveillance platform that turns raw PIDSR weekly case data into interactive barangay-level heat maps, automated WHO EWARN alerts, household-level dengue cluster detection, and machine-learning-based forecasts.

---

## What's built

All six functional modules from Ch.3 of the thesis are implemented and serving real Parañaque CESU data (35,164 cases, 2010–2026 from the PIDSR Registry).

| Module | Status | Lives in |
|---|---|---|
| **Module 1 — Data Digitization** (single-case form + CSV bulk upload, audit-logged) | ✅ | [laravel/app/Http/Controllers/CaseEntryController.php](laravel/app/Http/Controllers/CaseEntryController.php), [CaseEntry.jsx](laravel/resources/js/hmap/CaseEntry.jsx) |
| **Module 2 — Heat Map Visualization** (Leaflet + OSM, real barangay GeoJSON, choropleth + circle overlay) | ✅ | [HeatMapPanel.jsx](laravel/resources/js/hmap/HeatMapPanel.jsx) |
| **Module 3 — Trend Monitoring + EWARN** (Chart.js, 5-yr baseline + 2σ threshold per disease × week) | ✅ | [TrendChartPanel.jsx](laravel/resources/js/hmap/TrendChartPanel.jsx), [ml/compute_thresholds.py](ml/compute_thresholds.py) |
| **Module 4 — AI Prediction** (25 Prophet models + 6 Random Forest classifiers) | ✅ | [ForecastPanel.jsx](laravel/resources/js/hmap/ForecastPanel.jsx), [ml/train_prophet.py](ml/train_prophet.py), [ml/train_rf.py](ml/train_rf.py), [ml/main.py](ml/main.py) |
| **Module 5 — Reports & Export** (CSV streaming, three role-tiered exports, audit-logged) | ✅ | [ReportsController.php](laravel/app/Http/Controllers/ReportsController.php), [Reports.jsx](laravel/resources/js/hmap/Reports.jsx) |
| **Module 6 — Dengue Cluster Detection** (DBSCAN, CESU 200m / ≥3 / 4-week rule, cross-barangay) | ✅ | [ml/detect_clusters.py](ml/detect_clusters.py), [ml/geocode.py](ml/geocode.py), [ClustersController.php](laravel/app/Http/Controllers/ClustersController.php) |
| **HRMO Authentication** (stub mode for dev, PHP-session mode for prod) | ✅ | [HrmoSessionAuth.php](laravel/app/Http/Middleware/HrmoSessionAuth.php) |
| **RA 10173 audit trail** (every INSERT / EXPORT / AI request logged with employee_id, IP, payload) | ✅ | `hmap_db.audit_log` |

The cluster detection module (Module 6) is the **thesis's headline novelty contribution** and is not in the original Ch.3 text — see [docs/CHAPTERS_1_TO_3_REVISIONS.md](docs/CHAPTERS_1_TO_3_REVISIONS.md) for the thesis copy patches and [docs/cluster_detection.md](docs/cluster_detection.md) for the methodology.

---

## Architecture (deployment)

```
                       hrmo.paranaque.gov.ph/hmap
                                 │
                          ┌──────┴──────┐
                          │   nginx     │
                          └──┬───────┬──┘
                /hmap/api/*  │       │  /hmap/api/ml/*, /hmap/api/geocode
                             ▼       ▼
                     ┌─────────┐  ┌──────────────┐
                     │ Laravel │  │   FastAPI    │
                     │ PHP 8.2 │  │  Python 3.12 │
                     │   11.x  │  │ Prophet + RF │
                     └────┬────┘  │ + Nominatim  │
                          │       │   cascade    │
                          ▼       └──────┬───────┘
                     ┌─────────┐         │
                     │ hmap_db │◄────────┘
                     │ (MySQL) │  (cases, thresholds, ai_predictions,
                     └─────────┘   case_addresses, case_clusters,
                                   detection_runs, geocode_cache, …)
```

H-MAP is hosted **inside** the existing HRIS Portal infrastructure and reuses the portal's session-based authentication. Only employees with an active HRMO session reach `/hmap/*`. See [docs/architecture.md](docs/architecture.md) for the full topology including cross-schema DB grants and the two-layer RBAC design.

---

## Repo layout

| Folder | What lives here |
|---|---|
| [`laravel/`](laravel/) | Laravel 11 API + Vite-bundled React SPA shell. The full frontend lives at `laravel/resources/js/hmap/`. |
| [`ml/`](ml/) | Python FastAPI microservice + training scripts + the ETL pipeline. Evaluation reports for Ch.4 land in `ml/reports/`. |
| [`docs/`](docs/) | Thesis chapters (PDF + extracted text), revision list, methodology docs per module. |

---

## Local development

### Prerequisites

- **PHP 8.2+** with Composer 2.x — XAMPP 8.2.12 works on Windows
- **Node 20+** with npm 10+
- **Python 3.10+** (3.12 recommended) — for the ML / ETL scripts
- **MySQL 8.0+** — H-MAP uses a remote MySQL by default; see `ml/.env.example` and `laravel/.env`
- **Windows-only**: RTools42 + cmdstan (only required to train Prophet locally; see [docs/prophet.md](docs/prophet.md) for the one-time install)

### One-time setup

```powershell
# Install Python deps
cd C:\xampp\htdocs\hmap\ml
pip install -r requirements.txt
cp .env.example .env             # then fill in DB creds

# Install Composer if missing (XAMPP doesn't ship it)
C:\xampp\php\php.exe -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
C:\xampp\php\php.exe composer-setup.php --install-dir=C:\xampp\php --filename=composer
del composer-setup.php

# Install Laravel deps
cd ..\laravel
C:\xampp\php\php.exe C:\xampp\php\composer install
npm install
```

### One-time data load

```powershell
cd C:\xampp\htdocs\hmap
python ml\etl_registry.py              # → hmap_db.cases (~35,000 rows from docs/PIDSR Report YR 2026.xlsx)
python ml\seed_barangay_centroids.py   # → fills barangays.centroid_lat/lng + populations
python ml\fetch_barangay_geojson.py    # → laravel/public/barangays.geojson (real OSM polygons)
python ml\compute_thresholds.py        # → hmap_db.thresholds (WHO EWARN per disease × week)
python ml\train_prophet.py             # → ml/models/prophet_*.pkl (25 models)
python ml\train_rf.py                  # → ml/models/rf_*.pkl (6 models)
```

### Daily run (three PowerShell terminals)

```powershell
# Terminal 1 — FastAPI ML service
cd C:\xampp\htdocs\hmap\ml
python -m uvicorn main:app --host 127.0.0.1 --port 5000

# Terminal 2 — Laravel API
cd C:\xampp\htdocs\hmap\laravel
C:\xampp\php\php.exe artisan serve --host 127.0.0.1 --port 8000

# Terminal 3 — Vite dev server (HMR for React)
cd C:\xampp\htdocs\hmap\laravel
npm run dev
```

Then visit **http://localhost:8000/hmap** in a browser.

See [docs/quickstart.md](docs/quickstart.md) for a more detailed setup including troubleshooting.

### URLs (local dev)

| Service | URL | Notes |
|---|---|---|
| H-MAP dashboard | http://localhost:8000/hmap | The user-facing SPA |
| Laravel API | http://localhost:8000/api/* | All routes HRMO-gated; stub user = Administrator in dev |
| ML service | http://localhost:5000 | NOT exposed externally in prod (bound to 127.0.0.1) |
| Vite HMR | http://localhost:5173 | Used by Laravel's `@vite()` directive in dev only |

---

## Production deployment

Deployed to `https://hrmo.paranaque.gov.ph/hmap` on the same DICT-provisioned server that hosts the HRIS Portal. nginx routes `/hmap/*` to a PHP 8.x FPM pool; the FastAPI service runs as `hmap-ml.service` under systemd on `127.0.0.1:5000`. See [docs/architecture.md](docs/architecture.md). Deployment runbook is TBD.

---

## Status

**Functional.** All six modules serve real CESU data and pass smoke tests. The thesis defense materials in [docs/](docs/) describe methodology, validation, and known limitations per module.

**What's not yet production-ready:**
- HrmoSessionAuth `php` mode is implemented but untested against a live HRIS portal (only stub mode has end-to-end testing).
- No nginx config or systemd unit file checked in — these are deployment-day artifacts.
- ILI and HFMD Prophet models have MAPE > 100% (need meteorological covariates per Carvajal et al. 2018; documented in [docs/prophet.md](docs/prophet.md) as future work).

---

## Documentation index

| Document | What's in it |
|---|---|
| [docs/CHAPTERS_1_TO_3_REVISIONS.md](docs/CHAPTERS_1_TO_3_REVISIONS.md) | Patch list against the thesis Ch.1–3 PDF: cluster detection sub-objective, FastAPI vs Flask, 5 new tables, geocoding pipeline |
| [docs/architecture.md](docs/architecture.md) | Deployment topology, cross-schema DB grants, RBAC layers |
| [docs/data_mappings.md](docs/data_mappings.md) | 63 raw disease strings → 21 PIDSR canonical; 24 raw barangay strings → 16 official; reconciliation to 35,706 source rows |
| [docs/quickstart.md](docs/quickstart.md) | Step-by-step dev environment setup with troubleshooting |
| [docs/thresholds.md](docs/thresholds.md) | WHO EWARN methodology, COVID-era caveat, validation against CESU's `5YrAve` sheet |
| [docs/prophet.md](docs/prophet.md) | 25 Prophet models, per-model MAPE, thesis framing recommendation |
| [docs/random_forest.md](docs/random_forest.md) | RF risk classifier, feature importance, honest read on the "100% accuracy" diseases |
| [docs/geocoding.md](docs/geocoding.md) | Nominatim cascade, 195-row benchmark, cache strategy |
| [docs/cluster_detection.md](docs/cluster_detection.md) | DBSCAN params, *Ae. aegypti* 200m biology, cross-barangay finding |

---

## License

MIT — see [LICENSE](LICENSE).

---

## Related

- **HRIS Portal** — host application providing authentication and shared infrastructure
- **PIDSR** — Philippine Integrated Disease Surveillance and Response framework (DOH 2014)
- **Republic Act No. 10173** — Data Privacy Act of 2012, governing the audit log and RBAC design
