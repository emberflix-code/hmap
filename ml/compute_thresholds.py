"""H-MAP threshold computation: WHO EWARN epidemic thresholds → hmap_db.thresholds.

For every (disease × morbidity_week) where the disease has alert_enabled=1, compute:

    threshold = mean + 2 * std_dev

over the prior 5 calendar years' weekly case counts, counting only PIDSR
Confirmed and Probable cases (Suspect / Discarded / Negative / Compatible /
Pending are excluded per PIDSR surveillance practice).

The thesis quotes WHO EWARN (WHO, 2018) as the methodology — see Ch.2 p.15.

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
    python ml/compute_thresholds.py               # alert_year = current year
    python ml/compute_thresholds.py --alert-year 2026
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
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

CONFIRMED_PROBABLE = ("Confirmed", "Probable")


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


def compute_and_load(conn, alert_year: int) -> dict:
    baseline_years = list(range(alert_year - 5, alert_year))  # 5 years prior, exclusive of alert year
    baseline_str = ",".join(str(y) for y in baseline_years)
    log.info("alert_year=%d baseline=%s", alert_year, baseline_str)

    cur = conn.cursor()

    # Reset thresholds table — full recompute on each run.
    cur.execute("TRUNCATE TABLE thresholds")

    # For each alert-enabled disease, compute weekly mean+SD over the baseline window.
    # We aggregate at (disease, year, week) first, then over years for each week.
    sql = """
        INSERT INTO thresholds
            (disease_id, morbidity_week, baseline_years, mean_cases, std_dev, threshold_value)
        SELECT
            yearly.disease_id,
            yearly.morbidity_week,
            %s AS baseline_years,
            AVG(yearly.weekly_count) AS mean_cases,
            COALESCE(STDDEV_SAMP(yearly.weekly_count), 0) AS std_dev,
            AVG(yearly.weekly_count) + 2 * COALESCE(STDDEV_SAMP(yearly.weekly_count), 0) AS threshold_value
        FROM (
            -- weekly case counts per disease × year × week, over the baseline window
            SELECT
                d.disease_id,
                c.morbidity_year,
                c.morbidity_week,
                COUNT(*) AS weekly_count
            FROM cases c
            JOIN diseases d ON d.disease_id = c.disease_id
            WHERE d.alert_enabled = 1
              AND c.case_classification IN ('Confirmed','Probable')
              AND c.morbidity_year BETWEEN %s AND %s
              AND c.status_flag = 'Active'
            GROUP BY d.disease_id, c.morbidity_year, c.morbidity_week
        ) AS yearly
        GROUP BY yearly.disease_id, yearly.morbidity_week
    """
    cur.execute(sql, (baseline_str, baseline_years[0], baseline_years[-1]))
    rows_inserted = cur.rowcount
    conn.commit()

    # Coverage report
    cur.execute("""
        SELECT d.disease_code, d.disease_name, COUNT(t.threshold_id) AS weeks_with_threshold,
               COALESCE(SUM(t.mean_cases), 0) AS sum_mean
          FROM diseases d
          LEFT JOIN thresholds t ON t.disease_id = d.disease_id
         WHERE d.alert_enabled = 1
         GROUP BY d.disease_id, d.disease_code, d.disease_name
         ORDER BY weeks_with_threshold DESC, d.display_order
    """)
    coverage = cur.fetchall()

    cur.execute("""
        SELECT d.disease_name, t.morbidity_week, t.mean_cases, t.std_dev, t.threshold_value
          FROM thresholds t
          JOIN diseases d ON d.disease_id = t.disease_id
         WHERE d.disease_code = 'DENGUE'
         ORDER BY t.morbidity_week
    """)
    dengue_curve = cur.fetchall()

    return {
        "alert_year": alert_year,
        "baseline_years": baseline_str,
        "rows_inserted": rows_inserted,
        "coverage": coverage,
        "dengue_curve": dengue_curve,
    }


def report(result: dict) -> None:
    bar = "=" * 67
    print()
    print(bar)
    print(f"  WHO EWARN Threshold Computation")
    print(bar)
    print(f"  Alert year:        {result['alert_year']}")
    print(f"  Baseline years:    {result['baseline_years']}")
    print(f"  Rows inserted:     {result['rows_inserted']:,}")
    print()
    print("  Coverage per alert-enabled disease (weeks with computed threshold):")
    print(f"    {'Code':<8} {'Disease':<40} {'Weeks':>6} {'Total mean':>12}")
    for code, name, weeks, sum_mean in result["coverage"]:
        safe = name.encode("ascii", "replace").decode("ascii")
        print(f"    {code:<8} {safe:<40} {weeks:>6} {float(sum_mean):>12.2f}")
    print()
    print("  Sample: Dengue weekly threshold curve (first 12 weeks shown)")
    print(f"    {'Wk':>3} {'mean':>8} {'sd':>8} {'thresh':>8}")
    for name, week, mean, sd, thresh in result["dengue_curve"][:12]:
        print(f"    {week:>3} {float(mean):>8.2f} {float(sd):>8.2f} {float(thresh):>8.2f}")
    if len(result["dengue_curve"]) > 12:
        print(f"    ... {len(result['dengue_curve']) - 12} more weeks")
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
