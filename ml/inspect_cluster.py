"""Inspect a detected cluster's members for manual map validation.

Pulls members of a specific cluster (or the top-N largest in the latest
detection run) with their addresses, coordinates, and clickable Google Maps
links. Use this to verify a detected cluster's cases really do cluster
geographically, before trusting the cluster detection for the thesis.

Usage:
    python ml/inspect_cluster.py                    # top 5 largest clusters
    python ml/inspect_cluster.py --cluster-id 42    # specific cluster
    python ml/inspect_cluster.py --top 10           # top N largest
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent


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


def latest_run_id(conn) -> int | None:
    cur = conn.cursor()
    cur.execute("SELECT MAX(detection_run_id) FROM detection_runs")
    row = cur.fetchone()
    cur.close()
    return int(row[0]) if row and row[0] else None


def top_clusters(conn, run_id: int, n: int) -> list[dict]:
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT cluster_id, window_start, window_end, case_count,
                  radius_m, centroid_lat, centroid_lng, barangays_involved
             FROM case_clusters
            WHERE detection_run_id = %s
            ORDER BY case_count DESC, radius_m
            LIMIT %s""",
        (run_id, n),
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def cluster_members(conn, cluster_id: int) -> list[dict]:
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT c.case_id, c.date_onset, c.morbidity_year, c.morbidity_week,
                  c.case_classification,
                  b.barangay_name,
                  a.raw_street_purok, a.case_lat, a.case_lng,
                  a.geocode_source, a.geocode_formatted
             FROM case_cluster_members m
             JOIN cases c ON c.case_id = m.case_id
             JOIN barangays b ON b.barangay_id = c.barangay_id
             JOIN case_addresses a ON a.case_id = c.case_id
            WHERE m.cluster_id = %s
            ORDER BY c.date_onset, c.case_id""",
        (cluster_id,),
    )
    members = cur.fetchall()
    cur.close()
    return members


def gmaps_url(lat: float, lng: float) -> str:
    """Direct link to the lat/lng on Google Maps. No API key needed."""
    return f"https://www.google.com/maps/place/{lat},{lng}/@{lat},{lng},19z"


def show_cluster(conn, cluster_id: int) -> None:
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT cluster_id, detection_run_id, window_start, window_end,
                  case_count, radius_m, centroid_lat, centroid_lng,
                  barangays_involved
             FROM case_clusters WHERE cluster_id = %s""",
        (cluster_id,),
    )
    c = cur.fetchone()
    cur.close()
    if not c:
        print(f"  No cluster with id={cluster_id}")
        return

    bar = "=" * 80
    print()
    print(bar)
    print(f"  Cluster #{c['cluster_id']}  (run {c['detection_run_id']})")
    print(bar)
    print(f"  Window:     {c['window_start']} to {c['window_end']}")
    print(f"  Cases:      {c['case_count']}")
    print(f"  Radius:     {float(c['radius_m']):.1f}m")
    print(f"  Centroid:   {c['centroid_lat']}, {c['centroid_lng']}")
    bgys = (c["barangays_involved"] or "").encode("ascii", "replace").decode("ascii")
    print(f"  Barangays:  {bgys}")
    print(f"  Centroid on map: {gmaps_url(float(c['centroid_lat']), float(c['centroid_lng']))}")
    print()
    print("  Members:")
    print(f"    {'case_id':<8} {'onset':<11} {'cls':<10} {'barangay':<22} {'src':<22} address")

    for m in cluster_members(conn, c["cluster_id"]):
        onset = str(m["date_onset"]) if m["date_onset"] else f"MW{m['morbidity_week']}/{m['morbidity_year']}"
        bgy = (m["barangay_name"] or "").encode("ascii", "replace").decode("ascii")
        addr = (m["raw_street_purok"] or "").encode("ascii", "replace").decode("ascii")
        src = m["geocode_source"] or ""
        print(f"    {m['case_id']:<8} {onset:<11} {m['case_classification']:<10} "
              f"{bgy[:22]:<22} {src:<22} {addr[:50]}")

    # Print a single map URL with all members as pins (using Google Maps "search" trick)
    # Limited to ~10 points per URL; show all members as individual links instead.
    print()
    print("  Individual member map links:")
    for m in cluster_members(conn, c["cluster_id"]):
        print(f"    case {m['case_id']:<6}  {gmaps_url(float(m['case_lat']), float(m['case_lng']))}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cluster-id", type=int, default=None,
                   help="Specific cluster_id to inspect (default: show top N)")
    p.add_argument("--top", type=int, default=5,
                   help="If no cluster-id, show this many largest clusters (default 5)")
    p.add_argument("--run-id", type=int, default=None,
                   help="Detection run to inspect (default: latest)")
    args = p.parse_args()

    conn = connect()
    try:
        run_id = args.run_id or latest_run_id(conn)
        if run_id is None:
            print("  No detection runs in the database. Run ml/detect_clusters.py first.")
            return

        if args.cluster_id is not None:
            show_cluster(conn, args.cluster_id)
            return

        print(f"\n  Showing top {args.top} clusters from detection_run_id={run_id}:")
        tops = top_clusters(conn, run_id, args.top)
        for tc in tops:
            show_cluster(conn, tc["cluster_id"])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
