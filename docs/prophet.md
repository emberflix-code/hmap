# H-MAP Prophet Forecasting

Trained by [ml/train_prophet.py](../ml/train_prophet.py) → 25 model pickles in `ml/models/`.
Served by [ml/main.py](../ml/main.py) at `POST /predict/forecast`.

## What we built

| Tier | Count | Why |
|---|---|---|
| **City-wide models** | 6 | One per `forecast_enabled=1` disease: DENGUE, ILI, MEA, TYP, LEP, HFMD. Trained on weekly Confirmed+Probable case totals across all 16 barangays. |
| **Per-barangay models** | 19 | Trained only for (disease, barangay) pairs with ≥200 Confirmed+Probable cases in the training window. 15 of 16 barangays qualify for Dengue; 4 for Measles. Lower-volume pairs fall back to the city-wide model at serving time. |

**Volume floor of 200 cases** was chosen so each per-barangay model sees roughly 12+ cases/year — enough for Prophet to find weekly seasonality without overfitting noise.

## Methodology

For each (disease, optional barangay):

1. **Aggregate** Confirmed+Probable cases from `hmap_db.cases` by ISO morbidity week, 2010–2025. Zero-case weeks are explicitly filled in so Prophet sees a continuous index — this matters for the yearly seasonality component to converge.
2. **Train/holdout split.** Train on 2010–2023, hold out 2024–2025 for validation. 2026 is excluded because it's a year-to-date partial.
3. **Fit Prophet** with:
   - `yearly_seasonality=True` (the dominant signal in tropical communicable disease)
   - `weekly_seasonality=False`, `daily_seasonality=False` (we have weekly grain)
   - `seasonality_mode="multiplicative"` — case counts scale with the trend baseline, which matches outbreak-year amplification (2019 Dengue went 5× the 2016 baseline)
   - `interval_width=0.80` — 80% confidence band per WHO/CESU convention
4. **Validate** by predicting the held-out 2024–2025 weeks and computing **smoothed MAPE** (`|actual − predicted| / (actual + 1) × 100`). The `+1` denominator prevents the metric blowing up on zero-case weeks, which dominate sparse-disease series. Same trick used by Olana et al. (2025).
5. **Refit on the full window** 2010–2025 for the serving model, then pickle to `ml/models/prophet_<CODE>[_bgy<ID>].pkl`.

This pipeline matches the methodology validated by Olana et al. (2025) for national-scale Philippine dengue forecasting and Chakraborty et al. (2019) for tropical urban dengue.

## Validation results

| Model | Train weeks | Holdout weeks | MAPE % | Read |
|---|---|---|---|---|
| **DENGUE** city-wide | 720 | 104 | **50.1** | Acceptable. The 2019 outbreak (4,296 cases) is a structural break Prophet's smooth trend underfits. |
| DENGUE / San Isidro | 694 | 103 | 57.8 | |
| DENGUE / San Dionisio | 693 | 103 | 51.1 | |
| DENGUE / Don Bosco | 715 | 102 | 56.0 | |
| DENGUE / San Antonio | 697 | 104 | 40.8 | |
| DENGUE / B.F. Homes | 718 | 103 | 49.1 | |
| DENGUE / Moonwalk | 699 | 104 | 60.9 | |
| DENGUE / Sun Valley | 696 | 102 | 46.4 | |
| DENGUE / Santo Niño | 682 | 103 | 44.1 | |
| DENGUE / Tambo | 717 | 103 | 38.5 | |
| DENGUE / Marcelo Green Village | 699 | 102 | 38.8 | |
| DENGUE / Merville | 696 | 99 | 31.2 | |
| DENGUE / Baclaran | 696 | 103 | 33.1 | |
| DENGUE / La Huerta | 678 | 103 | **30.5** | Best per-barangay performance |
| DENGUE / Don Galo | 698 | 103 | **22.9** | Best per-barangay performance |
| DENGUE / San Martin de Porres | 704 | 99 | 32.6 | |
| **ILI** city-wide | 701 | 96 | **101.1** | Bad. ILI is clinical-encounter noise; not lab-confirmed. Needs meteorological regressors. Treat as v1 limitation. |
| **MEA** city-wide | 730 | 104 | 25.1 | Captures the 2019 surge well. |
| MEA / San Dionisio | 729 | 83 | 4.0 | Suspiciously low — see "MAPE caveat" below |
| MEA / Moonwalk | 730 | 69 | 4.3 | Same caveat |
| MEA / B.F. Homes | 730 | 89 | 1.6 | Same caveat |
| MEA / San Antonio | 481 | 0 | n/a | Holdout was empty for this barangay (no 2024–2025 Confirmed+Probable Measles cases there) |
| **TYP** city-wide | 691 | 90 | 35.4 | |
| **LEP** city-wide | 614 | 92 | **19.7** | Best city-wide performance. Leptospirosis has clean wet-season signal. |
| **HFMD** city-wide | 597 | 83 | **149.8** | Bad. Irregular outbreak years (2018 spike). Same caveat as ILI. |

### MAPE caveat for sparse diseases

The per-barangay Measles MAPE values (1.6%, 4.0%, 4.3%) look great but are misleading. Measles weekly counts at barangay level are mostly zero — the model learns "predict near-zero everywhere" and is right >95% of the time. Smoothed MAPE rewards this. **Don't oversell these numbers in the thesis.** The honest framing: "Per-barangay measles forecasting performs well on the baseline-zero majority of weeks but cannot anticipate sporadic spikes."

### Thesis framing recommendation

In Ch.4 (Evaluation), present the results in three tiers:

1. **Primary operational target — Dengue.** 17 years of data, strong seasonal signal, 22.9–60.9% MAPE per barangay (median ~44%), 50.1% city-wide. Operationally useful for 4-week early warning: at a typical weekly baseline of 5–20 cases, MAPE in this range translates to absolute errors of 2–10 cases, which is below CESU's intervention threshold.
2. **Generalization demonstrated — MEA, TYP, LEP.** Reasonable MAPE (20–35%), confirms the pipeline works on diseases beyond Dengue. Acknowledge that MEA per-barangay MAPE is artificially low due to data sparsity.
3. **Future work — ILI, HFMD.** Both exceed 100% MAPE. Cite Carvajal et al. (2018) as already in your Ch.2: meteorological covariates (temperature, humidity, rainfall) are needed for these noisier diseases. This is a defensible v2 scope, not a v1 failure.

### Lift over a naive baseline

Raw MAPE is hard to interpret in isolation — is 50% MAPE good or bad for weekly dengue counts? `ml/train_prophet.py` now computes a **seasonal-naive baseline** (`y_hat(t) = y(t - 52)` — predict each week as the same week one year ago) and reports Prophet's lift over it. Results land in `ml/reports/prophet_eval_*.json` and `prophet_eval_*.csv` (with a `_latest` mirror for the most recent run).

**Actual lift numbers (latest run, 2024–2025 holdout):**

| Model | Prophet MAPE | Baseline MAPE | **Lift (pp)** | Verdict |
|---|---|---|---|---|
| **DENGUE** city-wide | 50.1 | 69.6 | **+19.5** | Prophet wins, comfortably |
| DENGUE / 15 per-barangay models | 22.9–60.9 | 42.2–145.4 | **+7.4 to +89.3** (median ~+20) | Prophet wins all 15 |
| TYP city-wide | 35.4 | 43.9 | **+8.4** | Prophet wins |
| LEP city-wide | 19.7 | 35.0 | **+15.4** | Prophet wins, strongly |
| ILI city-wide | 101.1 | 90.0 | **−11.0** | **Baseline wins** — already-flagged ILI weakness |
| MEA city-wide | 25.1 | 5.5 | **−19.6** | **Baseline wins** — measles is so sparse that "predict last year" trivially wins |
| MEA / 3 per-barangay models | 1.6–4.3 | 0.6–3.3 | **−1.0 to −2.8** | Baseline wins (sparse) |
| HFMD city-wide | 149.8 | 10.1 | **−139.6** | **Baseline wins catastrophically** — HFMD has multi-year zero stretches that seasonal-naive nails |

**The honest read:** Prophet is the right model **for Dengue, Typhoid, and Leptospirosis**. For Measles, ILI, and HFMD, **a seasonal-naive baseline beats it** — the disease either lacks enough non-zero weeks for Prophet's trend/seasonality decomposition to find signal, or its dynamics aren't seasonal in the way Prophet assumes.

This is the **right** way to evaluate these models for the thesis: instead of *"Prophet works for these 6 diseases (MAPE varies)"*, the defensible claim is *"Prophet improves over a seasonal-naive baseline for Dengue, Typhoid, and Leptospirosis. For Measles, ILI, and HFMD, the seasonal-naive baseline is the operationally appropriate choice and these diseases should use it directly until meteorological covariates (Carvajal et al., 2018) are available."* This sharpens the v1 scope rather than weakening it.

Re-run `python ml/train_prophet.py` to refresh the report; the JSON shape is:

```json
{
  "generated_at_utc": "20260520T083000Z",
  "training_window": [2010, 2025],
  "validation_holdout": [2024, 2025],
  "baseline_strategy": "seasonal_naive_lag52",
  "models": [
    {
      "disease_code": "DENGUE",
      "barangay_id": null,
      "barangay_name": null,
      "n_weeks_total": 824, "n_weeks_train": 720, "n_weeks_holdout": 104,
      "mape_prophet": 50.1, "rmse_prophet": ...,
      "mape_baseline": ..., "rmse_baseline": ...,
      "mape_lift_vs_baseline": ...
    }
    // 24 more entries — one per (disease, optional barangay) model
  ]
}
```

`mape_lift_vs_baseline` is positive when Prophet's MAPE is lower than the seasonal-naive baseline's MAPE. **The thesis evaluation should report MAPE + lift, not MAPE alone.** RMSE is also reported because it doesn't blow up on zero-case weeks the way MAPE can (relevant for sparse diseases like Measles per-barangay).

## Serving

`POST /predict/forecast` accepts:

```json
{ "disease_code": "DENGUE", "barangay_id": 1, "weeks_ahead": 4 }
```

`barangay_id` is optional. Returns:

```json
{
  "disease_code": "DENGUE",
  "barangay_id": 1,
  "barangay_name": "Baclaran",
  "model": "prophet",
  "resolution": "per_barangay",
  "validation_mape": 33.1,
  "points": [
    {"week_start": "2025-12-22", "predicted_cases": 1.38, "lower_bound": 0.18, "upper_bound": 2.57},
    ...
  ]
}
```

### Model resolution logic

| Request | Behavior |
|---|---|
| `disease_code` + `barangay_id` where a per-barangay model exists | Uses per-barangay model; `resolution: "per_barangay"` |
| `disease_code` + `barangay_id` where no per-barangay model exists | Falls back to city-wide model; `resolution: "city_wide_fallback"` |
| `disease_code` only (no barangay) | Uses city-wide model; `resolution: "city_wide"` |
| Unknown `disease_code` | 404 with explanatory `detail` |

`predicted_cases`, `lower_bound`, `upper_bound` are clamped to ≥0 — Prophet's additive components can produce small negative forecasts, which are meaningless for case counts.

### Operational notes

- **Models load once at FastAPI startup** (`load_models()` in [ml/main.py](../ml/main.py)) — no per-request pickle deserialization.
- **TBB DLL** path is prepended at module import time so prophet_model.bin can find Intel TBB at runtime. Required only on Windows; harmless on Linux.
- **Retraining cadence.** Models should retrain after each weekly PIDSR data refresh. Trigger via `python ml/train_prophet.py` or an Administrator-panel button (per Ch.3 — "Administrators may trigger model retraining"). Allow ~30 seconds for the full 25-model retrain on this hardware.
- **Service binding.** Per [docs/architecture.md](architecture.md), the service binds to `127.0.0.1:5000` (or `:5001` in some Ch.3 references — pick one before deployment). Not exposed externally. Laravel proxies authenticated requests.

## Re-running

```bash
# Full retrain (6 city-wide + 19 per-barangay)
python ml/train_prophet.py

# Single disease, no per-barangay tier
python ml/train_prophet.py --disease DENGUE --no-barangay

# Different holdout window
python ml/train_prophet.py --holdout-start 2023 --holdout-end 2025
```

Models are written to `ml/models/`. The FastAPI service must be restarted to pick up new pickles (or you can add a `/reload` admin endpoint later).

## Known limitations (for thesis Ch.4)

1. **COVID-era trend break.** 2020–2021 case counts collapsed (586 + 690 rows total across all diseases) due to lockdown reporting changes. Prophet's smooth trend underfits this break. The 2019 → 2020 transition is the biggest source of residual error across the Dengue models.
2. **No meteorological covariates.** Carvajal et al. (2018) showed temperature and humidity materially improve Philippine dengue forecasting. We don't have a clean local weather time series joined to the case data — future work.
3. **No outbreak-year regularization.** A single extreme year (2019) dominates the additive seasonality fit. A robust alternative is to fit on year-relative scaled counts; out of scope for v1.
4. **Per-barangay measles MAPE is optimistic.** See "MAPE caveat" above — measles weekly counts at barangay level are mostly zero and trivially predicted by always saying zero.
5. **ILI and HFMD models are not operationally useful.** MAPE > 100% means the model is regularly wronger than just saying "use last week's count." Don't surface their forecasts in the dashboard without additional regressors.
