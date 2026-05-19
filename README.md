# H-MAP

**Heat Map Disease Surveillance and Outbreak Prediction System**
City Epidemiology Section Unit, Parañaque City Government

A web-based, AI-assisted disease surveillance platform that turns raw PIDSR weekly case data into interactive barangay-level heat maps, automated outbreak alerts, and machine-learning-based forecasts.

---

## Architecture (deployment)

```
                       hrmo.paranaque.gov.ph/hmap
                                 │
                          ┌──────┴──────┐
                          │   nginx     │
                          └──┬───────┬──┘
                /hmap/api/*  │       │  /hmap/ml/*
                             ▼       ▼
                     ┌─────────┐  ┌──────────────┐
                     │ Laravel │  │ FastAPI (ML) │
                     │ PHP 8.3 │  │ Python 3.12  │
                     └────┬────┘  └──────┬───────┘
                          │              │
                          ▼              ▼
                     ┌─────────┐    ┌────────────┐
                     │ hmap_db │    │ model.pkl  │
                     │ (MySQL) │    │ Prophet RF │
                     └─────────┘    └────────────┘

  Frontend bundle (React + Vite) is built to static files
  and served by Laravel under /hmap/*.
```

H-MAP is hosted *inside* the existing HRIS Portal infrastructure and reuses the portal's session-based authentication. Only employees with an active HRMO session can reach `/hmap/*`. See `docs/architecture.md` for details.

---

## Repo layout (monorepo)

| Folder | What lives here |
|---|---|
| `laravel/` | Laravel 11 API + thin server-render layer. Reads MySQL. Bridges HRIS Portal auth. |
| `frontend/` | React + Vite SPA. Leaflet maps, Chart.js charts. Builds to static assets. |
| `ml/` | Python FastAPI microservice. scikit-learn Random Forest + Prophet. |
| `docs/` | Thesis chapters, architecture notes, screenshots. |
| `docker-compose.yml` | One-command local dev. Brings up MySQL + Laravel + Vite dev server + FastAPI. |

---

## Local development

### Prerequisites

- **PHP 8.3+** (Composer 2.x) — for Laravel
- **Node 20+** (npm 10+) — for the React frontend
- **Python 3.12+** — for the ML service
- **MySQL 8.0+** (XAMPP works fine on Windows) — for development data

### Initial setup

```bash
# 1. Scaffold Laravel (one-time only)
cd laravel
composer create-project laravel/laravel . "^11.0"
php artisan key:generate

# 2. Scaffold React + Vite (one-time only)
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install
npm install leaflet chart.js react-leaflet react-chartjs-2

# 3. Set up Python ML service (one-time only)
cd ../ml
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### Daily run (three terminals)

```bash
# Terminal 1 — Laravel API
cd laravel && php artisan serve --port=8000

# Terminal 2 — React frontend (dev server with HMR)
cd frontend && npm run dev

# Terminal 3 — Python ML service (activate venv first)
cd ml && .venv\Scripts\activate && uvicorn main:app --reload --port 5000
```

MySQL runs out of your XAMPP install — start MySQL from the XAMPP control panel.

### URLs (local dev)

| Service | URL |
|---|---|
| React frontend (Vite dev) | http://localhost:5173 |
| Laravel API | http://localhost:8000/api |
| ML service | http://localhost:5000 |
| MySQL | localhost:3306 |

---

## Production deployment

Deployed to `https://hrmo.paranaque.gov.ph/hmap` on the same DICT-provisioned server that hosts HRIS Portal. nginx routes `/hmap/*` to a PHP 8.3 FPM pool. See `docs/architecture.md` and the deployment runbook (TBD).

---

## Status

🚧 **Pre-development scaffolding.** No application code yet. Setting up the workspace.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Related

- HRIS Portal — host application providing authentication and shared infrastructure
- PIDSR — Philippine Integrated Disease Surveillance and Response framework (DOH 2014)
