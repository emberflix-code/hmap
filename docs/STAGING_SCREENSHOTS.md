# Staging update and Ch.4 screenshots

Puts the current code (`feat/panel-revisions`) on the staging site
(`https://hrmo.paranaque.gov.ph:8080/hmap/`, anonymized demo data, stub login)
and lists the screenshots for Chapter 4, Figures 5 to 11.

---

## 1. Update staging (on the server)

```bash
cd /var/www/html/hmap_staging
git fetch origin
git checkout feat/panel-revisions
git pull

# Web app: no new PHP packages; one new npm package (qrcode)
cd laravel
npm ci && npm run build
php artisan config:clear && php artisan route:clear && php artisan view:clear

# Database: the four pending migrations (user_mfa, recommendations,
# notifications, channel_settings). Safe to re-run; done ones are skipped.
cd ../ml
.venv/bin/python run_migrations.py --db hmap_db_demo

# Hotspots again with the fixed detector (the demo database from ml/.env)
.venv/bin/python detect_clusters.py --disease DENGUE

# Forecast service picks up the fixed-seed change
sudo systemctl restart hmap-ml-staging

# Fill the Alerts menu for the screenshot week WITHOUT sending any email or SMS
cd ../laravel
php artisan hmap:notify --year 2025 --week 5 --no-send
```

Check: open `https://hrmo.paranaque.gov.ph:8080/hmap/`. The header now has
**Alerts**, and the Dashboard has a **Recommended response** panel.

**To undo:** `git checkout develop && cd laravel && npm run build`. The new
tables can stay; the old code ignores them.

Staging stays on stub login, so the MFA screen does not appear there.
Capture it on production (see the table below).

---

## 2. Screenshots

**Setup:**
- Use Chrome on an office computer, window maximized, browser zoom 100%.
- Crop out the browser's tabs and address bar; keep the system's own header.
- Save each screenshot as PNG, using the file name in the table, into
  `docs/final_manuscript/figures/ch4/screens/`.
- Then rebuild Chapter 4: `python docs/final_manuscript/build_chapter4.py`.
  Each real screenshot replaces its placeholder automatically.

**Week to show:** set Disease = Dengue, Year = **2025**, Morbidity week = **5**.
If no barangay is High or Moderate there, try weeks 2 to 6 or week 42.

| Figure | File | What to show |
|---|---|---|
| 5 Main Dashboard | `dashboard.png` | Dashboard tab, Dengue 2025 week 5: KPI strip, map, trend chart with alert and epidemic lines, forecast |
| 6 Case Entry Form | `case_entry.png` | Case Entry tab with the form filled with **made-up** values (no real patient), before saving |
| 7 Weekly Report | `weekly_report.png` | Weekly Report tab, 2025 week 5, Summary table (Category I and II) |
| 8 Hotspot Map | `cluster_map.png` | Clusters tab, year 2025, a cluster selected so its members show |
| 9 Risk Tiers and Recommended Response | `recommendations.png` | Dashboard, scrolled to **Recommended response** for 2025 week 5, with the draft-rules note visible |
| 10 Alerts and Notification Settings | `alerts.png` | **Alerts** menu open over Reports. Add a demo recipient first (e.g. "CESU Head (demo)", `demo@example.gov.ph`) and show **Email and SMS settings** with no real passwords |
| 11 Two-Step Sign-In | `mfa.png` | Taken on **production** (HTTPS): the screen that asks for the 6-digit code at a later sign-in. **Not the first-time QR code screen**: the QR code is the account's secret |

All staging data is anonymized, so the screenshots contain no patient
information. Check each one before saving anyway: no real names, addresses,
passwords or QR codes.
