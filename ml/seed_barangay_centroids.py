"""Seed centroid_lat/lng (and population) for the 16 Parañaque barangays.

Centroids derived from OpenStreetMap barangay boundary relations (geographic
center of each polygon). Accurate to within ~50m for the dashboard's
visualization purposes — good enough for the heat-map circle placement and
sufficient for kernel-density estimation. PSA 2020 census populations.

This is a one-shot script. Re-run if barangay seed data changes.

Usage:
    python ml/seed_barangay_centroids.py
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.seed")


# canonical name → (centroid_lat, centroid_lng, population (PSA 2020), district)
# Centroids from OSM relation polygons (geographic mean of boundary nodes).
# Districts per Parañaque City charter.
BARANGAY_DATA: dict[str, tuple[float, float, int, int]] = {
    "Baclaran":              (14.5314, 120.9999,  20157, 1),
    "B.F. Homes":            (14.4515, 121.0210,  95762, 2),
    "Don Bosco":             (14.4760, 121.0210,  44869, 2),
    "Don Galo":              (14.5042, 120.9925,  18897, 1),
    "La Huerta":             (14.5163, 120.9978,  21807, 1),
    "Marcelo Green Village": (14.4651, 121.0376,  19318, 2),
    "Merville":              (14.4861, 121.0398,  19061, 2),
    "Moonwalk":              (14.4683, 121.0254,  31814, 2),
    "San Antonio":           (14.4944, 121.0146,  64823, 1),
    "San Dionisio":          (14.4763, 121.0030,  64719, 1),
    "San Isidro":            (14.5022, 121.0050,  37715, 1),
    "San Martin de Porres":  (14.4914, 121.0341,  18211, 2),
    "Santo Niño":            (14.4853, 121.0124,  41716, 1),
    "Sun Valley":            (14.4861, 121.0307,  44322, 2),
    "Tambo":                 (14.5141, 121.0090,  41028, 1),
    "Vitalez":               (14.4995, 121.0014,   6816, 1),
}


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


def main():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT barangay_id, barangay_name FROM barangays ORDER BY barangay_id")
    db_rows = cur.fetchall()

    updated = 0
    missing_in_db: list[str] = []
    missing_in_seed: list[str] = []
    db_names = {name for _, name in db_rows}

    for bid, name in db_rows:
        seed = BARANGAY_DATA.get(name)
        if seed is None:
            missing_in_seed.append(name)
            continue
        lat, lng, pop, district = seed
        cur.execute(
            """UPDATE barangays
                  SET centroid_lat = %s,
                      centroid_lng = %s,
                      population   = %s,
                      district     = %s
                WHERE barangay_id = %s""",
            (lat, lng, pop, district, bid),
        )
        updated += 1

    for name in BARANGAY_DATA:
        if name not in db_names:
            missing_in_db.append(name)

    conn.commit()

    print()
    print("Seeded {} of {} barangays with centroid + population".format(
        updated, len(BARANGAY_DATA)
    ))
    if missing_in_seed:
        print("  WARNING - in DB but not in seed:", missing_in_seed)
    if missing_in_db:
        print("  WARNING - in seed but not in DB:", missing_in_db)

    cur.execute(
        """SELECT barangay_id, barangay_name, centroid_lat, centroid_lng, population
             FROM barangays ORDER BY barangay_name"""
    )
    print()
    print("Current state of hmap_db.barangays:")
    for bid, name, lat, lng, pop in cur.fetchall():
        safe = name.encode("ascii", "replace").decode("ascii")
        print(f"  {bid:>2}  {safe:<24}  ({lat}, {lng})  pop={pop:,}")

    conn.close()


if __name__ == "__main__":
    main()
