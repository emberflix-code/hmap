"""H-MAP threshold computation: multi-method weekly baselines → hmap_db.thresholds.

For every (disease × morbidity_week) where the disease has alert_enabled=1,
this script computes THREE thresholds and stores them side-by-side:

    ewarn_mu2sigma  — WHO EWARN (WHO, 2018): threshold = μ + 2·σ over the prior
                      5 years' weekly counts, COUNTING ONLY Confirmed + Probable
                      classifications. This is H-MAP's active alert threshold.
                      Cited in thesis Ch.2 p.15.

    cesu_mean       — Simple mean of weekly counts over the same 5-year baseline,
                      counting ALL classifications (Suspect + Probable + Confirmed +
                      Discarded + Negative + Compatible + Pending). This mirrors
                      the "Average" column in the workbook's `5YrAve` sheet that
                      CESU's existing memo template references. threshold_value
                      is set equal to mean_cases (no σ inflation) — it's a
                      *reference value*, not a control limit.

    cesu_median     — Median of the same all-classifications counts; matches
                      `5YrAve`'s "Median" column. Useful when the 5-year window
                      contains an outlier year (e.g. 2019 outbreak).

Storing all three lets the Laravel dashboard show H-MAP's statistical alert
beside CESU's existing reference numbers, and lets Ch.4 quantify where the
two diverge.

Baseline window choice:
    "Rolling 5 years prior to the alerting year" — the literal EWARN spec.
    For an alerting year Y, baseline = years [Y-5, Y-4, Y-3, Y-2, Y-1].
    The script reads --alert-year (default: current calendar year) and stores
    the explicit year list in `thresholds.baseline_years` for audit.

KNOWN LIMITATION (document in thesis Ch.4):
    2020 and 2021 case counts were depressed by COVID-19 lockdowns
    (586 and 690 rows total vs. ~3000 in surrounding years). For alerting
    years 2025–2026, those years sit inside the baseline window and pull
    thresholds down. This may produce over-sensitive alerts on diseases
    that genuinely cratered during lockdown (especially Measles, ILI).
    Mitigations to consider:
      - Manual threshold override per disease for COVID-affected windows
      - Re-run with a fixed pre-COVID baseline (2015–2019) as a comparison
      - Cite this as a methodological limitation of EWARN in pandemic-era data

Usage:
    python ml/compute_thresholds.py                  # alert_year = current year
    python ml/compute_thresholds.py --alert-year 2026
"""

from __future__ import annotations

import argparse
import logging
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.thresholds")

EWARN_CLASSIFICATIONS = ("Confirmed", "Probable")


def connect():
    load_dotenv(HERE / ".env")
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "hmap_db"),
        charset="utf8mb4",
    )


def _fetch_weekly_counts(cur, baseline_years: list[int], conf_prob_only: bool) -> dict:
    """Pull weekly case counts per (disease, year, week) over the baseline window.

    Returns {(disease_id, week): [count_y1, count_y2, ...]} with one entry per
    baseline year that has cases for that disease-week combo. Years with zero
    cases are inserted explicitly so the mean isn't biased by missing zeros.

    conf_prob_only:
        True  → EWARN: filter to Confirmed+Probable
        False → CESU: count all classifications (matches CESU's 5YrAve sheet)
    """
    classification_clause = ""
    if conf_prob_only:
        placeholders = ",".join(["%s"] * len(EWARN_CLASSIFICATIONS))
        classification_clause = f"AND c.case_classification IN ({placeholders})"
    sql = f"""
        SELECT d.disease_id, c.morbidity_year, c.morbidity_week, COUNT(*)
          FROM cases c
          JOIN diseases d ON d.disease_id = c.disease_id
         WHERE d.alert_enabled = 1
           AND c.morbidity_year BETWEEN %s AND %s
           AND c.status_flag = 'Active'
           {classification_clause}
         GROUP BY d.disease_id, c.morbidity_year, c.morbidity_week
    """
    params: list = [baseline_years[0], baseline_years[-1]]
    if conf_prob_only:
        params.extend(EWARN_CLASSIFICATIONS)
    cur.execute(sql, tuple(params))

    # Group by (disease_id, week); fill missing years with 0 so 5-year window
    # always has 5 data points per cell.
    bucket: dict = defaultdict(lambda: {y: 0 for y in baseline_years})
    for did, year, week, n in cur.fetchall():
        bucket[(did, week)][year] = n

    # Also need to make sure diseases with NO cases in the entire window still
    # produce zero-valued rows (so the thresholds table is dense per week).
    # Pull the alert-enabled disease list and seed (disease, week) for weeks 1..53.
    cur.execute("SELECT disease_id FROM diseases WHERE alert_enabled = 1")
    all_did = [r[0] for r in cur.fetchall()]
    for did in all_did:
        for week in range(1, 54):  # PIDSR uses weeks 1..53
            bucket.setdefault((did, week), {y: 0 for y in baseline_years})

    # Collapse year-dict to list for the stats functions
    return {k: list(v.values()) for k, v in bucket.items()}


def compute_and_load(conn, alert_year: int) -> dict:
    baseline_years = list(range(alert_year - 5, alert_year))  # 5 years prior, exclusive
    baseline_str = ",".join(str(y) for y in baseline_years)
    log.info("alert_year=%d baseline=%s", alert_year, baseline_str)

    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE thresholds")

    # ── Pull two sets of weekly counts ─────────────────────────────────────
    log.info("aggregating weekly counts (EWARN: Confirmed+Probable only)")
    ewarn_counts = _fetch_weekly_counts(cur, baseline_years, conf_prob_only=True)
    log.info("aggregating weekly counts (CESU: all classifications)")
    cesu_counts = _fetch_weekly_counts(cur, baseline_years, conf_prob_only=False)

    # ── Compute the three methods ──────────────────────────────────────────
    insert_rows: list[tuple] = []
    for (did, week), counts in ewarn_counts.items():
        mean = statistics.mean(counts)
        # statistics.stdev requires ≥2 data points; with our 5-year window we
        # always have 5, but be defensive in case of future window changes
        sd = statistics.stdev(counts) if len(counts) > 1 else 0.0
        insert_rows.append((did, week, "ewarn_mu2sigma", baseline_str,
                            mean, sd, mean + 2 * sd))
    for (did, week), counts in cesu_counts.items():
        mean = statistics.mean(counts)
        median = statistics.median(counts)
        sd = statistics.stdev(counts) if len(counts) > 1 else 0.0
        # For CESU methods, threshold_value = the reference statistic itself
        # (no σ inflation) — these mirror CESU's existing display values.
        insert_rows.append((did, week, "cesu_mean", baseline_str,
                            mean, sd, mean))
        insert_rows.append((did, week, "cesu_median", baseline_str,
                            median, sd, median))

    cur.executemany(
        """INSERT INTO thresholds
               (disease_id, morbidity_week, method, baseline_years,
                mean_cases, std_dev, threshold_value)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        insert_rows,
    )
    conn.commit()
    rows_inserted = len(insert_rows)
    log.info("inserted %d threshold rows (3 methods × %d disease-week combos)",
             rows_inserted, rows_inserted // 3)

    # ── Coverage report ────────────────────────────────────────────────────
    cur.execute("""
        SELECT d.disease_code, d.disease_name,
               COUNT(DISTINCT t.morbidity_week) AS weeks_with_threshold,
               COALESCE(SUM(CASE WHEN t.method='ewarn_mu2sigma' THEN t.mean_cases END), 0) AS sum_mean_ewarn
          FROM diseases d
          LEFT JOIN thresholds t ON t.disease_id = d.disease_id
         WHERE d.alert_enabled = 1
         GROUP BY d.disease_id, d.disease_code, d.disease_name
         ORDER BY weeks_with_threshold DESC, d.display_order
    """)
    coverage = cur.fetchall()

    # ── Side-by-side Dengue curve: all 3 methods for first 12 weeks ───────
    cur.execute("""
        SELECT t.morbidity_week, t.method, t.mean_cases, t.std_dev, t.threshold_value
          FROM thresholds t
          JOIN diseases d ON d.disease_id = t.disease_id
         WHERE d.disease_code = 'DENGUE'
         ORDER BY t.morbidity_week, t.method
    """)
    dengue_rows = cur.fetchall()
    # Pivot to {week: {method: (mean, sd, threshold)}}
    dengue_curve: dict[int, dict[str, tuple]] = defaultdict(dict)
    for week, method, mean, sd, thresh in dengue_rows:
        dengue_curve[week][method] = (float(mean), float(sd), float(thresh))

    return {
        "alert_year": alert_year,
        "baseline_years": baseline_str,
        "rows_inserted": rows_inserted,
        "coverage": coverage,
        "dengue_curve": dict(dengue_curve),
    }


def report(result: dict) -> None:
    bar = "=" * 86
    print()
    print(bar)
    print("  Multi-method Threshold Computation (EWARN μ+2σ • CESU mean • CESU median)")
    print(bar)
    print(f"  Alert year:        {result['alert_year']}")
    print(f"  Baseline years:    {result['baseline_years']}")
    print(f"  Rows inserted:     {result['rows_inserted']:,}  "
          f"(3 methods × {result['rows_inserted'] // 3} disease-week combos)")
    print()
    print("  Coverage per alert-enabled disease (distinct weeks with any method):")
    print(f"    {'Code':<8} {'Disease':<40} {'Weeks':>6} {'Σ EWARN mean':>14}")
    for code, name, weeks, sum_mean in result["coverage"]:
        safe = name.encode("ascii", "replace").decode("ascii")
        print(f"    {code:<8} {safe:<40} {weeks:>6} {float(sum_mean):>14.2f}")
    print()
    print("  Dengue weekly comparison (first 12 weeks):")
    print(f"    {'Wk':>3} | {'EWARN μ':>8} {'EWARN σ':>8} {'EWARN μ+2σ':>10} | "
          f"{'CESU mean':>9} {'CESU med':>8} | {'flag?':>5}")
    print(f"    {'-'*3}-+-{'-'*8}-{'-'*8}-{'-'*10}-+-{'-'*9}-{'-'*8}-+-{'-'*5}")
    weeks_sorted = sorted(result["dengue_curve"].keys())
    for week in weeks_sorted[:12]:
        m = result["dengue_curve"][week]
        ew = m.get("ewarn_mu2sigma", (0, 0, 0))
        cm = m.get("cesu_mean", (0, 0, 0))
        cmed = m.get("cesu_median", (0, 0, 0))
        # Flag weeks where EWARN threshold differs notably from CESU mean
        diff = ew[2] - cm[0]
        marker = "↑" if diff > 5 else ("↓" if diff < -5 else " ")
        print(f"    {week:>3} | {ew[0]:>8.2f} {ew[1]:>8.2f} {ew[2]:>10.2f} | "
              f"{cm[0]:>9.2f} {cmed[0]:>8.2f} | {marker:>5}")
    if len(weeks_sorted) > 12:
        print(f"    ... {len(weeks_sorted) - 12} more weeks")
    print()
    print("  Interpretation:")
    print("    EWARN μ+2σ  is H-MAP's alert threshold (Confirmed+Probable, μ+2σ)")
    print("    CESU mean   matches the 5YrAve sheet's 'Average' column (all classes)")
    print("    CESU median matches the 5YrAve sheet's 'Median' column (all classes)")
    print("    ↑ = EWARN threshold > CESU mean + 5; ↓ = EWARN threshold < CESU mean - 5")
    print(bar)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--alert-year", type=int, default=datetime.now().year,
                   help="Year being alerted against; baseline = 5 years prior")
    args = p.parse_args()

    conn = connect()
    try:
        result = compute_and_load(conn, args.alert_year)
        report(result)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
