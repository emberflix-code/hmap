"""Fetch barangay boundary polygons for Parañaque from OpenStreetMap (Overpass API).

OSM tags barangays as `admin_level=10` relations within their parent city.
For Parañaque (`name=Parañaque`, place=city in Metro Manila) we query
Overpass for all admin_level=10 relations whose `is_in` chain includes
Parañaque, then convert each relation's outer-way geometry into a GeoJSON
polygon.

Output:
    laravel/public/barangays.geojson

The dashboard fetches this static file at runtime. ~30-200KB depending on
how detailed OSM has each barangay traced. We do NOT simplify aggressively
because Parañaque is small enough that the raw OSM detail still serves
without lag.

Usage:
    python ml/fetch_barangay_geojson.py
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import unicodedata
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT_PATH = REPO / "laravel" / "public" / "barangays.geojson"

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.osm")

# Mapping from canonical H-MAP barangay names → likely OSM `name` variants.
# OSM is inconsistent: some barangays are "Barangay X", some are bare "X",
# some include the city. We accept any of these as a match.
CANONICAL_NAMES = [
    "Baclaran",
    "B.F. Homes",
    "Don Bosco",
    "Don Galo",
    "La Huerta",
    "Marcelo Green Village",
    "Merville",
    "Moonwalk",
    "San Antonio",
    "San Dionisio",
    "San Isidro",
    "San Martin de Porres",
    "Santo Niño",
    "Sun Valley",
    "Tambo",
    "Vitalez",
]

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# Bounding box around Parañaque City. Loose enough to catch boundary-straddling
# relations; we filter to our canonical list afterwards.
PARANAQUE_BBOX = "14.40,120.97,14.55,121.06"

OVERPASS_QUERY = f"""
[out:json][timeout:60];
(
  rel["admin_level"="10"]({PARANAQUE_BBOX});
);
out body;
>;
out skel qt;
"""


def normalize(s: str) -> str:
    """Lowercase + strip diacritics + collapse non-alphanumerics for matching."""
    n = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return "".join(c.lower() for c in n if c.isalnum())


def canonical_match(osm_name: str) -> str | None:
    """Return the canonical H-MAP barangay name if osm_name matches one, else None."""
    if not osm_name:
        return None
    n = normalize(osm_name)
    # Strip common prefixes
    for prefix in ("barangay", "brgy"):
        if n.startswith(prefix):
            n = n[len(prefix):]
    for canon in CANONICAL_NAMES:
        if normalize(canon) == n:
            return canon
        # Variants: 'bfhomes' should match 'B.F. Homes'
        if normalize(canon).replace(" ", "") == n.replace(" ", ""):
            return canon
    return None


def fetch_overpass() -> dict:
    log.info("querying Overpass API (this can take ~30s)...")
    # Overpass requires a descriptive User-Agent or it returns 406.
    headers = {
        "User-Agent": "H-MAP-thesis-project/1.0 (Paranaque City CESU surveillance system)",
        "Accept": "application/json",
    }
    resp = requests.post(OVERPASS_URL, data={"data": OVERPASS_QUERY},
                         headers=headers, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"Overpass returned {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def build_geometry(rel: dict, members: dict, nodes: dict) -> list | None:
    """Stitch a relation's `outer` ways into a closed ring of [lng, lat] coords.

    OSM relations carry boundary ways as `outer` (and sometimes `inner`).
    Each way is a list of node ids; we need to chain them into a continuous
    ring. Returns the coordinate list, or None if the geometry can't be
    closed (incomplete OSM data).
    """
    outer_ways: list[list[int]] = []
    for m in rel.get("members", []):
        if m.get("type") == "way" and m.get("role") in ("outer", ""):
            way = members.get(m["ref"])
            if way:
                outer_ways.append(list(way.get("nodes", [])))

    if not outer_ways:
        return None

    # Stitch ways head-to-tail. Each way's endpoints must connect to a neighbor.
    chain: list[int] = list(outer_ways[0])
    used = {0}
    while len(used) < len(outer_ways):
        end = chain[-1]
        for i, way in enumerate(outer_ways):
            if i in used:
                continue
            if way[0] == end:
                chain.extend(way[1:])
                used.add(i)
                break
            elif way[-1] == end:
                chain.extend(reversed(way[:-1]))
                used.add(i)
                break
        else:
            # Could not extend — incomplete relation
            return None

    # Close the ring if not already closed
    if chain[0] != chain[-1]:
        chain.append(chain[0])

    coords = []
    for nid in chain:
        n = nodes.get(nid)
        if not n:
            return None
        coords.append([n["lon"], n["lat"]])
    return coords


def main():
    data = fetch_overpass()

    # Index Overpass elements
    relations = [e for e in data["elements"] if e["type"] == "relation"]
    ways = {e["id"]: e for e in data["elements"] if e["type"] == "way"}
    nodes = {e["id"]: e for e in data["elements"] if e["type"] == "node"}

    log.info("Overpass returned %d relations, %d ways, %d nodes",
             len(relations), len(ways), len(nodes))

    features: list[dict] = []
    matched: dict[str, dict] = {}

    for rel in relations:
        tags = rel.get("tags", {})
        osm_name = tags.get("name") or tags.get("official_name") or ""
        canon = canonical_match(osm_name)
        if not canon:
            continue
        if canon in matched:
            # OSM sometimes has duplicate relations; keep the one with more members
            if len(rel.get("members", [])) <= len(matched[canon].get("members", [])):
                continue

        coords = build_geometry(rel, ways, nodes)
        if coords is None or len(coords) < 4:
            log.warning("could not build geometry for %s (osm_name=%r)", canon, osm_name)
            continue

        matched[canon] = rel
        features.append({
            "type": "Feature",
            "properties": {
                "canonical_name": canon,
                "osm_name": osm_name,
                "osm_id": rel["id"],
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords],
            },
        })

    # Build the FeatureCollection
    fc = {"type": "FeatureCollection", "features": features}

    # Report which canonical names did/did not match
    found = set(matched.keys())
    missing = [n for n in CANONICAL_NAMES if n not in found]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(fc), encoding="utf-8")

    print()
    print(f"Wrote {OUT_PATH.relative_to(REPO)}: {len(features)} polygon(s), "
          f"{OUT_PATH.stat().st_size:,} bytes")
    print(f"Matched ({len(found)}): {sorted(found)}")
    if missing:
        print(f"MISSING ({len(missing)}): {missing}")
        print("  → fallback ring circles will continue to render for these in the dashboard.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\naborted", file=sys.stderr)
        sys.exit(2)
