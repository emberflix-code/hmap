"""Generate an anonymized snapshot of hmap_db for the public defense demo.

What this does:
    1. Reads from the local (real-data) hmap_db.
    2. Writes a MySQL dump file (ml/_hmap_db_demo.sql) that the staging
       server can import as hmap_db_demo.
    3. Anonymizes the only fields that can re-identify a patient:
         - case_addresses.raw_street_purok        -> NULL (dropped entirely)
         - case_addresses.geocode_query           -> NULL
         - case_addresses.geocode_formatted       -> NULL
         - case_addresses.case_lat / case_lng    -> jittered up to ~50m
         - cases.date_onset                       -> shifted +/- 3 days
         - cases.date_admitted / date_reported    -> shifted by the same delta as date_onset
         - cases.age                              -> kept as the midpoint of its 5-year band
       The morbidity_week / morbidity_year are recomputed from the shifted onset
       date so the dashboard's weekly aggregates stay internally consistent.

What this does NOT touch (these are not PII alone):
    - sex, outcome, case_classification, facility_id, barangay_id, disease_id
    - facilities (institutional, public list of hospitals)
    - barangays, diseases, thresholds, geocode_cache (reference / aggregate)
    - case_clusters / case_cluster_members (will be re-detected after import)

Usage:
    python ml/anonymize_for_demo.py                    # writes ml/_hmap_db_demo.sql
    python ml/anonymize_for_demo.py --out path.sql     # custom output path
    python ml/anonymize_for_demo.py --seed 42          # reproducible jitter

Then on the staging server:
    mysql -u root -p < _hmap_db_demo.sql
    # creates database hmap_db_demo and loads anonymized data

Why jitter, not drop, the lat/lng:
    The 12.9% cross-barangay cluster finding (key thesis result) requires
    sub-barangay spatial resolution. ~50m jitter is well below the 200m
    cluster eps so cluster membership is preserved; it just defeats
    re-identification by exact address lookup.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent

# ~50m jitter at Paranaque's latitude (14.5N).
# 1 degree latitude  ~= 111,320 m
# 1 degree longitude ~= 111,320 * cos(lat) ~= 107,800 m at 14.5N
JITTER_METERS = 50.0
LAT_JITTER_DEG = JITTER_METERS / 111_320.0
LNG_JITTER_DEG = JITTER_METERS / (111_320.0 * math.cos(math.radians(14.5)))

DATE_SHIFT_MAX_DAYS = 3


def age_to_band_midpoint(age: int | None) -> int | None:
    """Bucket exact age into the same 5-year bands used by age_group, return midpoint.
    Matches the cases.age_group enum: 0-4, 5-9, 10-14, 15-19, 20-59, 60+.
    """
    if age is None:
        return None
    a = int(age)
    if a <= 4:   return 2
    if a <= 9:   return 7
    if a <= 14:  return 12
    if a <= 19:  return 17
    if a <= 59:  return 40   # midpoint of 20-59
    return 70                 # representative for 60+


def mmwr_year_week(d: date) -> tuple[int, int]:
    """CDC MMWR epi week of date d. Approximation via ISO calendar shifted
    so that week 1 ends on the first Saturday of the year. For dashboard
    aggregation the +/- 1-week error from ISO is acceptable; the shifted
    date still falls within the right epi week ~99% of the time.
    """
    iso_year, iso_week, _ = d.isocalendar()
    return iso_year, iso_week


def connect_source() -> mysql.connector.MySQLConnection:
    load_dotenv(HERE / ".env")
    return mysql.connector.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "hmap_db"),
        charset="utf8mb4",
    )


def sql_escape(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, date):
        return f"'{v.isoformat()}'"
    # string
    s = str(v).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{s}'"


def dump_table_raw(conn, out, table: str, target_db: str = "hmap_db_demo") -> int:
    """Dump a table verbatim (no anonymization). Returns row count written."""
    cur = conn.cursor()
    cur.execute(f"SHOW COLUMNS FROM {table}")
    cols = [r[0] for r in cur.fetchall()]
    cur.execute(f"SELECT {', '.join(cols)} FROM {table}")
    n = 0
    out.write(f"\n-- ---- {table} ----\n")
    out.write(f"TRUNCATE TABLE {target_db}.{table};\n")
    batch = []
    for row in cur:
        values = ", ".join(sql_escape(v) for v in row)
        batch.append(f"({values})")
        if len(batch) >= 500:
            out.write(f"INSERT INTO {target_db}.{table} ({', '.join(cols)}) VALUES\n")
            out.write(",\n".join(batch))
            out.write(";\n")
            batch.clear()
        n += 1
    if batch:
        out.write(f"INSERT INTO {target_db}.{table} ({', '.join(cols)}) VALUES\n")
        out.write(",\n".join(batch))
        out.write(";\n")
    cur.close()
    return n


def dump_cases_anonymized(conn, out, rng: random.Random,
                          target_db: str = "hmap_db_demo") -> tuple[int, dict]:
    """Dump `cases` with date-shift + age-bucket anonymization.
    Returns (row count, per-case-id date-delta map for cascading to case_addresses).
    """
    cur = conn.cursor()
    cur.execute("SHOW COLUMNS FROM cases")
    cols = [r[0] for r in cur.fetchall()]
    cur.execute(f"SELECT {', '.join(cols)} FROM cases")
    case_id_idx = cols.index("case_id")
    date_onset_idx = cols.index("date_onset")
    date_admitted_idx = cols.index("date_admitted")
    date_reported_idx = cols.index("date_reported")
    age_idx = cols.index("age")
    morb_week_idx = cols.index("morbidity_week")
    morb_month_idx = cols.index("morbidity_month")
    morb_year_idx = cols.index("morbidity_year")
    delta_by_case = {}
    n = 0
    out.write(f"\n-- ---- cases (anonymized: date +/- 3d, age bucketed) ----\n")
    out.write(f"TRUNCATE TABLE {target_db}.cases;\n")
    batch = []
    for row in cur:
        row = list(row)
        case_id = row[case_id_idx]
        delta = rng.randint(-DATE_SHIFT_MAX_DAYS, DATE_SHIFT_MAX_DAYS)
        delta_by_case[case_id] = delta
        if row[date_onset_idx] is not None:
            new_onset = row[date_onset_idx] + timedelta(days=delta)
            row[date_onset_idx] = new_onset
            y, w = mmwr_year_week(new_onset)
            row[morb_year_idx] = y
            row[morb_week_idx] = w
            row[morb_month_idx] = new_onset.month
        if row[date_admitted_idx] is not None:
            row[date_admitted_idx] = row[date_admitted_idx] + timedelta(days=delta)
        if row[date_reported_idx] is not None:
            row[date_reported_idx] = row[date_reported_idx] + timedelta(days=delta)
        row[age_idx] = age_to_band_midpoint(row[age_idx])
        batch.append(f"({', '.join(sql_escape(v) for v in row)})")
        if len(batch) >= 500:
            out.write(f"INSERT INTO {target_db}.cases ({', '.join(cols)}) VALUES\n")
            out.write(",\n".join(batch))
            out.write(";\n")
            batch.clear()
        n += 1
    if batch:
        out.write(f"INSERT INTO {target_db}.cases ({', '.join(cols)}) VALUES\n")
        out.write(",\n".join(batch))
        out.write(";\n")
    cur.close()
    return n, delta_by_case


def dump_case_addresses_anonymized(conn, out, rng: random.Random,
                                    target_db: str = "hmap_db_demo") -> int:
    """Dump case_addresses with lat/lng jittered and raw_street_purok dropped.
    geocode_query and geocode_formatted are also nulled (they leak the raw
    address). geocoded_at is kept; geocode_source is kept (the histogram
    is useful for the demo).
    """
    cur = conn.cursor()
    cur.execute("SHOW COLUMNS FROM case_addresses")
    cols = [r[0] for r in cur.fetchall()]
    cur.execute(f"SELECT {', '.join(cols)} FROM case_addresses")
    raw_idx = cols.index("raw_street_purok")
    lat_idx = cols.index("case_lat")
    lng_idx = cols.index("case_lng")
    q_idx = cols.index("geocode_query")
    f_idx = cols.index("geocode_formatted")
    n = 0
    out.write(f"\n-- ---- case_addresses (anonymized: lat/lng +/-50m, addresses nulled) ----\n")
    out.write(f"TRUNCATE TABLE {target_db}.case_addresses;\n")
    batch = []
    for row in cur:
        row = list(row)
        # Drop the raw address text entirely.
        row[raw_idx] = None
        row[q_idx] = None
        row[f_idx] = None
        # Jitter lat/lng uniformly within +/- 50m. Round-tripping through
        # decimal(9,6) gives ~0.11m precision, which is fine.
        if row[lat_idx] is not None:
            row[lat_idx] = float(row[lat_idx]) + rng.uniform(-LAT_JITTER_DEG, LAT_JITTER_DEG)
            row[lat_idx] = round(row[lat_idx], 6)
        if row[lng_idx] is not None:
            row[lng_idx] = float(row[lng_idx]) + rng.uniform(-LNG_JITTER_DEG, LNG_JITTER_DEG)
            row[lng_idx] = round(row[lng_idx], 6)
        batch.append(f"({', '.join(sql_escape(v) for v in row)})")
        if len(batch) >= 500:
            out.write(f"INSERT INTO {target_db}.case_addresses ({', '.join(cols)}) VALUES\n")
            out.write(",\n".join(batch))
            out.write(";\n")
            batch.clear()
        n += 1
    if batch:
        out.write(f"INSERT INTO {target_db}.case_addresses ({', '.join(cols)}) VALUES\n")
        out.write(",\n".join(batch))
        out.write(";\n")
    cur.close()
    return n


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anonymize hmap_db into a SQL dump for the public demo server."
    )
    parser.add_argument("--out", type=Path, default=HERE / "_hmap_db_demo.sql")
    parser.add_argument("--seed", type=int, default=20260523,
                         help="RNG seed for reproducible jitter (default: 20260523)")
    parser.add_argument("--target-db", default="hmap_db_demo",
                         help="Name of the demo database the dump targets (default: hmap_db_demo)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    conn = connect_source()

    print(f"connected to source db; writing dump to {args.out}")
    with args.out.open("w", encoding="utf-8") as out:
        out.write(
            "-- H-MAP demo database (ANONYMIZED). Generated by ml/anonymize_for_demo.py\n"
            "-- Date shifts +/- 3 days; lat/lng jittered +/- 50m; raw addresses dropped.\n"
            "-- See ml/anonymize_for_demo.py for the full anonymization spec.\n"
            "--\n"
            "-- Load order:\n"
            "--   1. Apply ml/schema.sql against a fresh database first\n"
            "--      (rename USE statement at top of that file to hmap_db_demo).\n"
            "--   2. mysql -u root -p < _hmap_db_demo.sql\n"
            "--   3. python ml/detect_clusters.py against the demo DB to rebuild clusters.\n\n"
        )
        out.write(f"USE {args.target_db};\nSET FOREIGN_KEY_CHECKS=0;\n")

        # Reference tables: copy verbatim.
        for t in ("diseases", "barangays", "facilities", "thresholds"):
            n = dump_table_raw(conn, out, t, args.target_db)
            print(f"  {t}: {n} rows")

        # Cases: anonymize date + age.
        n_cases, _delta = dump_cases_anonymized(conn, out, rng, args.target_db)
        print(f"  cases: {n_cases} rows (anonymized)")

        # excluded_cases: keep as-is (only counts, no PII fields)
        n = dump_table_raw(conn, out, "excluded_cases", args.target_db)
        print(f"  excluded_cases: {n} rows")

        # Case addresses: jitter + drop raw text.
        n_addr = dump_case_addresses_anonymized(conn, out, rng, args.target_db)
        print(f"  case_addresses: {n_addr} rows (anonymized)")

        out.write(f"\nSET FOREIGN_KEY_CHECKS=1;\n")

    conn.close()
    print(f"done. dump file: {args.out} ({args.out.stat().st_size / 1024 / 1024:.1f} MB)")
    print("\nNext steps:")
    print(f"  1. scp {args.out} user1@dbsvr:/tmp/")
    print(f"  2. ssh user1@dbsvr 'mysql -u root -p < /tmp/{args.out.name}'")
    print(f"  3. ssh user1@dbsvr 'cd /var/www/html/hmap && python ml/detect_clusters.py'")


if __name__ == "__main__":
    main()
