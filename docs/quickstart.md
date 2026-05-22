# H-MAP Quickstart

End-to-end dev environment setup on Windows. Linux/macOS equivalents are noted where they differ.

If you just want to **run** the system after someone else set it up, jump to [§Daily run](#daily-run). If anything errors, see [§Troubleshooting](#troubleshooting) at the bottom.

## Prerequisites

| Tool | Version | How to install on Windows | Why |
|---|---|---|---|
| PHP | 8.2+ | XAMPP 8.2.12 ships it at `C:\xampp\php\php.exe` | Laravel runtime |
| Composer | 2.x | One-time setup, see below | Laravel dependency manager |
| Node.js | 20+ | https://nodejs.org/ (LTS) | Vite + React |
| npm | 10+ | Ships with Node | Frontend deps |
| Python | 3.10+ | https://python.org/ | ML / ETL |
| MySQL | 8.0+ | Remote server (Parañaque DICT) or local XAMPP | `hmap_db` |
| RTools42 | latest | https://cran.r-project.org/bin/windows/Rtools/rtools42/rtools.html | **Only required to train Prophet locally.** Skip if you have pre-trained `ml/models/*.pkl` already. |

PowerShell users: if `npm` errors with "running scripts is disabled":

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## One-time setup

### 1. Install Composer

XAMPP doesn't ship Composer. Drop it next to `php.exe` so it's reusable:

```powershell
cd $env:TEMP
C:\xampp\php\php.exe -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
C:\xampp\php\php.exe composer-setup.php --install-dir=C:\xampp\php --filename=composer
del composer-setup.php
```

### 2. Configure environment files

Two `.env` files, both gitignored. Copy the examples and fill in real values:

```powershell
cd C:\xampp\htdocs\hmap
copy ml\.env.example ml\.env
copy laravel\.env.example laravel\.env   # if it exists; otherwise Laravel will create one on install
```

Required in **`ml/.env`** (also read by all ml/*.py scripts):

```
DB_HOST=103.5.62.166        # or whatever your MySQL host is
DB_PORT=3306
DB_NAME=hmap_db
DB_USER=hmap_app
DB_PASSWORD=...
```

Required in **`laravel/.env`** (same DB credentials + ML service URL + HRMO bridge mode):

```
DB_HOST=103.5.62.166
DB_PORT=3306
DB_DATABASE=hmap_db
DB_USERNAME=hmap_app
DB_PASSWORD=...

HMAP_ML_URL=http://127.0.0.1:5000
HMAP_HRMO_MODE=stub                    # 'stub' for dev, 'php' for prod
HMAP_HRMO_STUB_USER_ID=1
HMAP_HRMO_STUB_USER_NAME="Dev User"
HMAP_HRMO_STUB_USER_ROLE=Administrator # Encoder | Analyst | Administrator
```

### 3. Install dependencies

```powershell
# Python
cd C:\xampp\htdocs\hmap\ml
pip install -r requirements.txt

# Laravel
cd ..\laravel
C:\xampp\php\php.exe C:\xampp\php\composer install

# Frontend (React + Leaflet + Chart.js)
npm install
```

### 4. Load data into `hmap_db`

This is the expensive step. Each script is idempotent (you can re-run any of them if you change config).

```powershell
cd C:\xampp\htdocs\hmap

# 1. Create schema + load 35,164 cases from the PIDSR Excel registry
python ml\etl_registry.py

# 2. Seed real lat/lng centroids and PSA-2020 populations for the 16 barangays
python ml\seed_barangay_centroids.py

# 3. Fetch real OSM barangay boundary polygons → laravel/public/barangays.geojson
python ml\fetch_barangay_geojson.py

# 4. Compute WHO EWARN thresholds per disease × week (340 thresholds)
python ml\compute_thresholds.py
```

### 5. (Optional) Train the ML models

Only needed if you don't already have `ml/models/*.pkl` — the trained models are gitignored (~50MB total).

**Prophet on Windows** needs the cmdstan toolchain. Once-only:

```powershell
# After installing RTools42 from the link in the Prerequisites table
copy C:\rtools42\usr\bin\make.exe C:\rtools42\usr\bin\mingw32-make.exe
$env:PATH = "C:\rtools42\x86_64-w64-mingw32.static.posix\bin;C:\rtools42\usr\bin;" + $env:PATH
python -c "from cmdstanpy import install_cmdstan; install_cmdstan(version='2.33.1', dir='C:/Users/' + $env:USERNAME + '/AppData/Local/Programs/Python/Python312/Lib/site-packages/prophet/stan_model', overwrite=True)"
```

Then train:

```powershell
cd C:\xampp\htdocs\hmap
python ml\train_prophet.py   # ~30s for 25 models
python ml\train_rf.py        # ~10s for 6 models
```

See [docs/prophet.md](prophet.md) and [docs/random_forest.md](random_forest.md) for the validation MAPE / F1 numbers per model.

### 6. (Optional) Run cluster detection

The DBSCAN cluster detection is offline — re-run after every fresh ETL load or after a batch of new case entries:

```powershell
python ml\detect_clusters.py
```

See [docs/cluster_detection.md](cluster_detection.md). Detected clusters are queryable via `GET /api/clusters` and visualized on the dashboard.

## Daily run

Three PowerShell terminals:

```powershell
# Terminal 1 — FastAPI ML service
cd C:\xampp\htdocs\hmap\ml
python -m uvicorn main:app --host 127.0.0.1 --port 5000

# Terminal 2 — Laravel API
cd C:\xampp\htdocs\hmap\laravel
C:\xampp\php\php.exe artisan serve --host 127.0.0.1 --port 8000

# Terminal 3 — Vite dev server (React HMR)
cd C:\xampp\htdocs\hmap\laravel
npm run dev
```

Visit **http://localhost:8000/hmap**. You should see:

1. A role badge ("Administrator") in the top-right header
2. A disease/year/week picker bar
3. A KPI strip (4 numbers: EWARN alerts, cases this week, cases YTD, prior year same week)
4. A Leaflet heat map (polygons + circles, real Parañaque barangays)
5. A Chart.js trend chart with the EWARN threshold overlay
6. A Prophet 4-week forecast panel

Click "Case Entry" in the top nav to test the data digitization module, "Reports" to test CSV export.

## Verifying the install

Quick health-check requests:

```powershell
curl http://localhost:8000/api/whoami
# → {"employee_id":1,"employee_name":"Dev User","role":"Administrator"}

curl http://localhost:8000/api/ml/health
# → {"status":"ok","service":"hmap-ml","models_loaded":25,"diseases":[...]}

curl "http://localhost:8000/api/summary?disease_code=DENGUE&morbidity_year=2024&morbidity_week=45"
# → {"cases_this_week":91,"cases_ytd":1156,"cases_prior_year":21,"alerts_this_week":7}
```

If all three return real data, the stack is healthy end-to-end.

## Troubleshooting

### `npm` errors with "running scripts is disabled"

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Restart PowerShell.

### Laravel: "Could not open input file: artisan"

You're running from the wrong directory. `cd` into `laravel/` first, or use the full path:

```powershell
C:\xampp\php\php.exe C:\xampp\htdocs\hmap\laravel\artisan serve --host 127.0.0.1 --port 8000
```

### MySQL: "Plugin caching_sha2_password could not be loaded"

The XAMPP `mysql.exe` client is too old for MySQL 8's default auth plugin. This only affects the XAMPP CLI client; Python's `mysql.connector` and Laravel's PDO driver both work fine. Use those instead, or update your client.

### MySQL: "Access denied for user 'hmap_app'@'YOUR.IP'"

The DBA's grant is scoped to a different IP than yours. Either ask for a grant for your current public IP, or use a wildcard host:

```sql
GRANT ALL PRIVILEGES ON hmap_db.* TO 'hmap_app'@'%';
FLUSH PRIVILEGES;
```

### Prophet: "Error during optimization!" with no detail

The `prophet_model.bin` couldn't find Intel TBB at runtime. The fix is already baked into `ml/main.py` and `ml/train_prophet.py` (both prepend `~/.cmdstan/.../tbb` to PATH at import). But if you're calling Prophet from a custom script, do the same:

```python
import os, sys
from pathlib import Path
if sys.platform == "win32":
    tbb = Path.home() / ".cmdstan" / "cmdstan-2.39.0" / "stan" / "lib" / "stan_math" / "lib" / "tbb"
    if (tbb / "tbb.dll").exists():
        os.environ["PATH"] = f"{tbb};{os.environ['PATH']}"
```

### Vite: "Cannot find module @vitejs/plugin-react"

Laravel ships Vite 6; the latest `@vitejs/plugin-react` (v6+) requires Vite 8. Pin to v4:

```powershell
cd C:\xampp\htdocs\hmap\laravel
npm install --save-dev "@vitejs/plugin-react@^4.3.4"
```

### "VITE v6.4.2 ready" but the page is blank

Make sure all three services are running and the Blade view in `laravel/resources/views/hmap.blade.php` includes `@viteReactRefresh @vite(['resources/css/app.css', 'resources/js/app.jsx'])`. Open browser devtools → Network → check that `app.jsx` returns 200 from `localhost:5173`.

### Nominatim geocoding returns 406 Not Acceptable

You forgot the User-Agent. Already handled in `ml/geocode.py` and `ml/fetch_barangay_geojson.py`, but if you're writing a new script that hits Overpass or Nominatim:

```python
headers = {"User-Agent": "H-MAP/1.0 (CESU Parañaque)"}
```

## Stopping everything

`Ctrl-C` in each terminal. Or kill by port:

```powershell
Get-NetTCPConnection -LocalPort 5000,8000,5173 -State Listen | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```
