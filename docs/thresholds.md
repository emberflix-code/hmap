# H-MAP Epidemic Threshold Computation

Computed by [ml/compute_thresholds.py](../ml/compute_thresholds.py), populating `hmap_db.thresholds`.

## Method

For every (disease × morbidity_week 1–53) combination where the disease has `alert_enabled=1`:

```
mean_cases     = AVG(weekly case count) over the baseline years
std_dev        = SAMPLE STDDEV(weekly case count) over the baseline years
threshold      = mean_cases + 2 × std_dev
```

This is the standard WHO EWARN methodology (WHO, 2018), the same formula cited in Ch.2 p.15 of the thesis:

> Alert if: Current Cases > Baseline Mean + 2 × Standard Deviation

The Philippines' national PIDSR five-year-average alert tables use the same mathematical basis (DOH, 2014).

### Baseline window: rolling 5 years prior to the alerting year

For an alerting year **Y**, baseline = years **[Y−5, Y−4, Y−3, Y−2, Y−1]**.

Current run targets **alert_year = 2026** → baseline = **2021, 2022, 2023, 2024, 2025**.

The script accepts `--alert-year`; the explicit year list is stored per row in `thresholds.baseline_years` for audit traceability.

### Case filter: Confirmed + Probable only

Per PIDSR surveillance practice, the threshold computation counts only cases with `case_classification ∈ {Confirmed, Probable}`. Excluded from the baseline count:

- **Suspect** — not yet investigated
- **Discarded** — ruled out
- **Negative** — lab-negative
- **Compatible** — clinically compatible but lab-unavailable (rare)
- **Pending** — awaiting lab result

This is what makes the threshold conservative-but-defensible: alert when *confirmed activity* exceeds historical confirmed activity.

## Validation against CESU's own computation

The Registry workbook contains a sheet `5YrAve` with CESU's own pre-computed totals through the alerting week. Cross-check for Dengue, year-to-date through morbidity week 5:

| Year | CESU `5YrAve` sheet | H-MAP `hmap_db.cases` (all classifications) | H-MAP (Confirmed+Probable only) | Δ vs CESU |
|---|---|---|---|---|
| 2021 | 107 | 107 | 82 | 0 |
| 2022 | 32 | 32 | 18 | 0 |
| 2023 | 126 | 125 | 86 | −1 |
| 2024 | 105 | 105 | 94 | 0 |
| 2025 | 246 | 246 | 214 | 0 |
| 2026 (YTD) | 151 | 151 | 146 | 0 |

**Be precise about what this validates.** CESU's `5YrAve` worksheet sums every reported Dengue case regardless of classification status (Confirmed, Probable, Suspect, etc.). The middle column above compares against that same all-status filter and shows the H-MAP case loader has the same 767-record case set CESU's worksheet has. This is a **pipeline-level reconciliation** — it validates the ETL's disease/barangay/year/week mapping, not the EWARN threshold computation itself.

The EWARN threshold computation downstream applies an additional Confirmed+Probable filter (the third column above), which is a **deliberate methodological choice** matching standard PIDSR practice — Suspect cases are not yet investigated and shouldn't contribute to the baseline mean. The Confirmed+Probable totals therefore deviate from CESU's all-status totals by the count of Suspect cases each year (e.g. 2023: 39 Suspects = 125 − 86). This is the right behavior; H-MAP's thresholds are computed against the surveillance-grade subset.

5-year mean over 2021–2025 (all classifications, matching CESU's basis): CESU = 123.2 cases, H-MAP = 123.0 cases. **The case loaders agree to within one case across 767 records** — well within the noise from per-case CASECLASS interpretation differences.

## Coverage at alert_year=2026

| Disease | Weeks with computed threshold | Notes |
|---|---|---|
| Dengue | 52 / 53 | Strong signal across the whole year |
| Influenza-Like Illness | 50 | |
| COVID-19 | 50 | Limited to 2022–2025 in baseline; 2021 had zero PIDSR-tracked COVID |
| Typhoid Fever | 45 | |
| Acute Bloody Diarrhea | 42 | |
| Leptospirosis | 25 | Concentrated in wet-season weeks; off-season weeks have zero baseline |
| Hand, Foot & Mouth Disease | 19 | |
| Non-Neonatal Tetanus | 18 | |
| Acute Viral Hepatitis | 11 | |
| Measles | 9 | Sparse post-COVID; outbreak years (2019, 2024) are outside baseline window for 2026 |
| Bacterial Meningitis | 3 | |
| Pertussis | 3 | |
| Chikungunya | 3 | |
| SARS | 3 | |
| Rabies | 2 | |
| Neonatal Tetanus | 1 | |
| Meningococcal Disease | 1 | |
| Diphtheria | 1 | |
| Malaria | 1 | |
| Cholera | 1 | |
| AES, AFP, AHFS, AEFI, Rotavirus, Rubella, Zika | 0 | Zero Confirmed+Probable cases in 2021–2025 |

Diseases with zero coverage will not raise EWARN alerts in 2026 — there's no baseline to compare against. The data-entry module still accepts cases for these; they just don't trigger automated alerts until a baseline accumulates. This is consistent with PIDSR practice (rare diseases trigger individual case-level investigation rather than statistical alerting).

## Sample: Dengue weekly threshold curve

First 12 morbidity weeks of the year, alert_year = 2026 (baseline 2021–2025):

| Week | Mean cases | SD | Threshold |
|---|---|---|---|
| 1 | 17.20 | 7.85 | 32.91 |
| 2 | 19.80 | 16.18 | 52.15 |
| 3 | 22.40 | 19.35 | 61.09 |
| 4 | 21.00 | 14.54 | 50.09 |
| 5 | 18.40 | 18.60 | 55.59 |
| 6 | 17.40 | 13.97 | 45.35 |
| 7 | 13.80 | 8.58 | 30.97 |
| 8 | 13.40 | 9.29 | 31.98 |
| 9 | 14.60 | 8.96 | 32.52 |
| 10 | 14.40 | 12.12 | 38.63 |
| 11 | 10.20 | 6.02 | 22.23 |
| 12 | 8.00 | 6.20 | 20.41 |

Read this as: "An alert fires at morbidity week 3 of 2026 if the weekly Dengue case count exceeds 61." Standard EWARN interpretation.

## Known limitation: COVID-era data in the baseline window

**The 2020–2021 lockdown years sit inside the baseline window for alert years 2025 and 2026.** Case counts in those years were artificially depressed — total Registry rows: 2020 = 586, 2021 = 690, vs. roughly 3,000 in non-pandemic years. This pulls means and standard deviations down, producing **artificially low thresholds** for 2025–2026 alerts on diseases that genuinely cratered during lockdown (Measles is the clearest case: 2024 saw a small outbreak, but the 2021–2025 mean is depressed by 2020's near-zero count).

### Defending this choice in the thesis

The "rolling 5 years prior" baseline is the literal WHO EWARN specification (WHO, 2018) and matches the Philippines' national PIDSR five-year-average alerting tables (DOH, 2014). Deviating from it requires explicit justification. The current implementation follows the literal spec; the COVID distortion is documented as a **known limitation of EWARN methodology in pandemic-era data**, not a defect in our system.

### Mitigations to consider (not in v1)

- **Per-disease threshold override** in the Administrator module — for diseases CESU judges to be COVID-distorted, an analyst sets a manual threshold.
- **Comparison view** — compute a second threshold set against fixed pre-COVID baseline 2015–2019 and display alongside the rolling baseline. Lets the analyst see both and judge.
- **Years-with-data weighting** — exclude years from the baseline where total weekly cases were < some floor (e.g. exclude any baseline year whose total is < 30% of the 5-year median). Defensible but adds complexity.

## Re-running

```bash
# Default: alert_year = current calendar year
python ml/compute_thresholds.py

# Override (e.g. to back-test or recompute for a historical year)
python ml/compute_thresholds.py --alert-year 2025
```

The script TRUNCATEs `thresholds` and recomputes from scratch each run — safe to re-run after every ETL load.
