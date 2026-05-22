"""H-MAP dengue cluster detection — CESU's 200m / ≥3 cases / 4-week rule.

Implements the operational clustering directive specified by Parañaque CESU:

    "200-meter radius of more than 2 cases in a 4-week period, basis is
     street address."

Approach:
    1. Load all eligible dengue cases from hmap_db: case_classification
       ∈ {Confirmed, Probable}, geocode precision usable for the 200m rule
       (street_level or subdivision_level — barangay centroids are too
       coarse).
    2. Sweep a rolling 4-morbidity-week window across the case onset dates
       (1-week stride).
    3. In each window, run DBSCAN with eps=200m (converted to radians via
       haversine) and min_samples=3 to find all spatially-tight clusters.
    4. Deduplicate across overlapping windows using a fingerprint of the
       sorted member case_ids — the same physical cluster typically appears
       in several consecutive windows; we keep its FIRST appearance.
    5. Write detected clusters + members to hmap_db (case_clusters,
       case_cluster_members, detection_runs).

Cite Harrington et al. (2005) on Aedes aegypti flight range (~100-200m
typical dispersal) as the biological basis for the 200m threshold.

Usage:
    python ml/detect_clusters.py                       # full historical sweep
    python ml/detect_clusters.py --year 2024           # only 2024 cases
    python ml/detect_clusters.py --eps 200 --min 3 --weeks 4   # explicit params
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import math
import os
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import mysql.connector
import numpy as np
from dotenv import load_dotenv
from sklearn.cluster import DBSCAN

HERE = Path(__file__).resolve().parent

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.cluster")


EARTH_RADIUS_M = 6_371_000.0
USABLE_GEOCODE_SOURCES = ("nominatim_street", "nominatim_subd", "manual_pin")
SURVEILLANCE_CLASSIFICATIONS = ("Confirmed", "Probable")


# ─── DB ─────────────────────────────────────────────────────────────────────

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


def ensure_cluster_tables(conn) -> None:
    """Create the three cluster tables if the canonical schema.sql hasn't
    been re-applied yet. Mirrors the CREATE TABLE statements in schema.sql."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS detection_runs (
            detection_run_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
            run_at             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            disease_code       VARCHAR(20) NOT NULL,
            eps_meters         DECIMAL(6,1) NOT NULL,
            min_samples        TINYINT UNSIGNED NOT NULL,
            window_weeks       TINYINT UNSIGNED NOT NULL,
            date_range_start   DATE NULL,
            date_range_end     DATE NULL,
            cases_evaluated    INT UNSIGNED NOT NULL,
            clusters_detected  INT UNSIGNED NOT NULL,
            PRIMARY KEY (detection_run_id),
            INDEX idx_run_disease (disease_code, run_at)
        ) ENGINE=InnoDB
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS case_clusters (
            cluster_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
            detection_run_id   INT UNSIGNED NOT NULL,
            fingerprint        CHAR(40) NOT NULL,
            window_start       DATE NOT NULL,
            window_end         DATE NOT NULL,
            centroid_lat       DECIMAL(9,6) NOT NULL,
            centroid_lng       DECIMAL(9,6) NOT NULL,
            case_count         SMALLINT UNSIGNED NOT NULL,
            radius_m           DECIMAL(8,2) NOT NULL,
            barangays_involved VARCHAR(255) NULL,
            PRIMARY KEY (cluster_id),
            UNIQUE KEY uq_cluster_fingerprint (detection_run_id, fingerprint),
            INDEX idx_cluster_window (window_start, window_end),
            INDEX idx_cluster_run (detection_run_id),
            CONSTRAINT fk_cluster_run
                FOREIGN KEY (detection_run_id) REFERENCES detection_runs(detection_run_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS case_cluster_members (
            cluster_id  INT UNSIGNED NOT NULL,
            case_id     INT UNSIGNED NOT NULL,
            PRIMARY KEY (cluster_id, case_id),
            INDEX idx_ccm_case (case_id),
            CONSTRAINT fk_ccm_cluster
                FOREIGN KEY (cluster_id) REFERENCES case_clusters(cluster_id)
                ON DELETE CASCADE ON UPDATE CASCADE,
            CONSTRAINT fk_ccm_case
                FOREIGN KEY (case_id) REFERENCES cases(case_id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB
    """)
    conn.commit()
    cur.close()


def load_eligible_cases(conn, disease_code: str, year: int | None) -> list[dict]:
    """Pull dengue cases with usable geocode precision + a usable case date.

    A case is usable for cluster detection iff:
        - disease matches disease_code
        - case_classification ∈ {Confirmed, Probable}
        - case_addresses.geocode_source ∈ USABLE_GEOCODE_SOURCES
        - status_flag = 'Active'
        - has a usable onset date: prefer date_onset, fall back to a
          synthetic date computed from morbidity_year + morbidity_week (ISO
          Thursday of that ISO week — a 1-3 day approximation of MMWR week
          midpoint, sufficient for 4-week window analysis)
    """
    placeholders = ",".join(["%s"] * len(USABLE_GEOCODE_SOURCES))
    sql = f"""
        SELECT
            c.case_id,
            c.date_onset,
            c.morbidity_year,
            c.morbidity_week,
            c.barangay_id,
            b.barangay_name,
            a.case_lat,
            a.case_lng,
            a.geocode_source
        FROM cases c
        JOIN diseases d  ON d.disease_id = c.disease_id
        JOIN case_addresses a ON a.case_id = c.case_id
        JOIN barangays b ON b.barangay_id = c.barangay_id
        WHERE d.disease_code = %s
          AND c.case_classification IN ('Confirmed','Probable')
          AND c.status_flag = 'Active'
          AND a.geocode_source IN ({placeholders})
          AND a.case_lat IS NOT NULL AND a.case_lng IS NOT NULL
    """
    params: list = [disease_code, *USABLE_GEOCODE_SOURCES]
    if year is not None:
        sql += " AND c.morbidity_year = %s"
        params.append(year)
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    cur.close()

    # Resolve a "case date" per row: prefer date_onset, fall back to ISO
    # Thursday of (morbidity_year, morbidity_week). The ISO calendar disagrees
    # with MMWR by 1-3 days but that's small relative to the 4-week window.
    out: list[dict] = []
    for r in rows:
        case_date = r["date_onset"]
        if case_date is None:
            try:
                case_date = date.fromisocalendar(
                    int(r["morbidity_year"]), int(r["morbidity_week"]), 4
                )
            except (TypeError, ValueError):
                continue  # unusable date; drop
        out.append({
            "case_id":      int(r["case_id"]),
            "case_date":    case_date,
            "lat":          float(r["case_lat"]),
            "lng":          float(r["case_lng"]),
            "barangay":     r["barangay_name"],
        })
    out.sort(key=lambda r: r["case_date"])
    return out


# ─── Cluster math ───────────────────────────────────────────────────────────

def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two lat/lng pairs, in meters."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def fingerprint_members(case_ids: list[int]) -> str:
    """SHA1 of sorted case_ids; used to dedupe the same cluster appearing in
    multiple overlapping windows."""
    h = hashlib.sha1()
    for cid in sorted(case_ids):
        h.update(f"{cid},".encode())
    return h.hexdigest()


def run_detection(cases: list[dict], eps_m: float, min_samples: int,
                   window_weeks: int) -> list[dict]:
    """Sweep a sliding window over cases and DBSCAN within each window.

    Returns a list of unique clusters (deduplicated by member fingerprint),
    each with the EARLIEST window in which the full member set appeared.
    """
    if not cases:
        return []

    eps_rad = eps_m / EARTH_RADIUS_M
    window_days = window_weeks * 7

    first_date = cases[0]["case_date"]
    last_date = cases[-1]["case_date"]
    log.info("scanning %s → %s, %d eligible cases, window=%dw, eps=%dm, min=%d",
             first_date, last_date, len(cases), window_weeks, int(eps_m), min_samples)

    # Pre-bucket cases by date so each window slice is fast
    by_date: dict[date, list[dict]] = defaultdict(list)
    for c in cases:
        by_date[c["case_date"]].append(c)

    detected: dict[str, dict] = {}   # fingerprint → cluster record

    cursor_date = first_date
    while cursor_date <= last_date:
        window_start = cursor_date - timedelta(days=window_days - 1)
        window_end = cursor_date
        # Collect cases falling in [window_start, window_end]
        slice_cases: list[dict] = []
        d = window_start
        while d <= window_end:
            if d in by_date:
                slice_cases.extend(by_date[d])
            d += timedelta(days=1)

        if len(slice_cases) >= min_samples:
            # DBSCAN expects RADIANS for haversine
            coords = np.array(
                [[math.radians(c["lat"]), math.radians(c["lng"])] for c in slice_cases]
            )
            labels = DBSCAN(
                eps=eps_rad,
                min_samples=min_samples,
                metric="haversine",
            ).fit_predict(coords)

            for cluster_label in set(labels):
                if cluster_label == -1:
                    continue  # noise
                members = [slice_cases[i] for i, lbl in enumerate(labels) if lbl == cluster_label]
                case_ids = [m["case_id"] for m in members]
                fp = fingerprint_members(case_ids)
                if fp in detected:
                    continue  # already recorded an earlier window for this cluster
                lat_mean = float(np.mean([m["lat"] for m in members]))
                lng_mean = float(np.mean([m["lng"] for m in members]))
                radius = max(
                    haversine_m(m["lat"], m["lng"], lat_mean, lng_mean) for m in members
                )
                bgys = sorted({m["barangay"] for m in members})
                detected[fp] = {
                    "fingerprint":   fp,
                    "window_start":  window_start,
                    "window_end":    window_end,
                    "centroid_lat":  lat_mean,
                    "centroid_lng":  lng_mean,
                    "case_count":    len(members),
                    "radius_m":      radius,
                    "barangays":     bgys,
                    "case_ids":      case_ids,
                }

        cursor_date += timedelta(days=7)  # 1-week stride

    out = list(detected.values())
    out.sort(key=lambda c: (c["window_start"], -c["case_count"]))
    return out


# ─── Persistence ────────────────────────────────────────────────────────────

def persist_run(conn, disease_code: str, eps_m: float, min_samples: int,
                 window_weeks: int, cases: list[dict],
                 clusters: list[dict]) -> int:
    cur = conn.cursor()
    date_start = cases[0]["case_date"] if cases else None
    date_end = cases[-1]["case_date"] if cases else None
    cur.execute(
        """INSERT INTO detection_runs
              (disease_code, eps_meters, min_samples, window_weeks,
               date_range_start, date_range_end,
               cases_evaluated, clusters_detected)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (disease_code, eps_m, min_samples, window_weeks,
         date_start, date_end, len(cases), len(clusters)),
    )
    run_id = cur.lastrowid

    for c in clusters:
        bgy_str = ", ".join(c["barangays"])[:255]
        cur.execute(
            """INSERT INTO case_clusters
                  (detection_run_id, fingerprint, window_start, window_end,
                   centroid_lat, centroid_lng, case_count, radius_m,
                   barangays_involved)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (run_id, c["fingerprint"], c["window_start"], c["window_end"],
             c["centroid_lat"], c["centroid_lng"], c["case_count"],
             c["radius_m"], bgy_str),
        )
        cluster_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO case_cluster_members (cluster_id, case_id) VALUES (%s, %s)",
            [(cluster_id, cid) for cid in c["case_ids"]],
        )
    conn.commit()
    cur.close()
    return run_id


# ─── Report ─────────────────────────────────────────────────────────────────

def _ascii(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def report(disease_code: str, cases: list[dict], clusters: list[dict],
           eps_m: float, min_samples: int, window_weeks: int) -> None:
    # Windows console defaults to cp1252, so keep all output ASCII-only.
    # Unicode glyphs like the ge-sign, arrow, and block char would crash print.
    bar = "=" * 75
    print()
    print(bar)
    print("  CESU Dengue Cluster Detection")
    print(bar)
    print(f"  Disease:           {disease_code}")
    print(f"  Rule:              {int(eps_m)}m radius, >={min_samples} cases, "
          f"{window_weeks}-week window")
    print(f"  Cases evaluated:   {len(cases):,}")
    if cases:
        print(f"  Date range:        {cases[0]['case_date']} -> {cases[-1]['case_date']}")
    print(f"  Clusters detected: {len(clusters):,}")
    print()

    if not clusters:
        print("  No clusters met the threshold.")
        print(bar)
        return

    sizes = Counter(c["case_count"] for c in clusters)
    print("  Cluster size distribution:")
    for size in sorted(sizes):
        bar_glyph = "#" * min(40, sizes[size])
        print(f"    {size:>3} cases  {sizes[size]:>5}  {bar_glyph}")
    print()

    bgy_counts: Counter = Counter()
    cross_bgy = 0
    for c in clusters:
        for b in c["barangays"]:
            bgy_counts[b] += 1
        if len(c["barangays"]) > 1:
            cross_bgy += 1
    print(f"  Cross-barangay clusters: {cross_bgy:,} of {len(clusters):,} "
          f"({cross_bgy/len(clusters)*100:.1f}%)")
    print()
    print("  Clusters per barangay (a cluster spanning 2 barangays counts in both):")
    for b in sorted(bgy_counts, key=lambda k: -bgy_counts[k]):
        print(f"    {_ascii(b):<28} {bgy_counts[b]:>5}")
    print()

    yr_counts: Counter = Counter()
    for c in clusters:
        yr_counts[c["window_end"].year] += 1
    print("  Clusters per year:")
    for y in sorted(yr_counts):
        print(f"    {y}  {yr_counts[y]:>5}")
    print()

    print("  Top 10 largest clusters:")
    print(f"    {'window':<24} {'size':>5} {'radius':>8}  barangays")
    for c in sorted(clusters, key=lambda c: -c["case_count"])[:10]:
        win = f"{c['window_start']} -> {c['window_end']}"
        bgys = _ascii(", ".join(c["barangays"]))
        print(f"    {win:<24} {c['case_count']:>5} {c['radius_m']:>7.1f}m  {bgys}")
    print(bar)


# ─── Entry point ────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--disease", default="DENGUE",
                   help="PIDSR disease code (default: DENGUE)")
    p.add_argument("--year", type=int, default=None,
                   help="Limit to a single morbidity_year (default: all years)")
    p.add_argument("--eps", type=float, default=200.0,
                   help="DBSCAN eps in meters (default: 200, per CESU directive)")
    p.add_argument("--min", dest="min_samples", type=int, default=3,
                   help="DBSCAN min_samples (default: 3, per CESU directive)")
    p.add_argument("--weeks", type=int, default=4,
                   help="Rolling window size in weeks (default: 4, per CESU directive)")
    args = p.parse_args()

    conn = connect()
    try:
        ensure_cluster_tables(conn)
        cases = load_eligible_cases(conn, args.disease, args.year)
        clusters = run_detection(cases, args.eps, args.min_samples, args.weeks)
        run_id = persist_run(conn, args.disease, args.eps, args.min_samples,
                              args.weeks, cases, clusters)
        log.info("persisted detection_run_id=%d with %d clusters", run_id, len(clusters))
        report(args.disease, cases, clusters, args.eps, args.min_samples, args.weeks)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
