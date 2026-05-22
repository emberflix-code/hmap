"""Compare Nominatim (OSM, free) vs. Google Geocoding API on real PIDSR addresses.

Purpose: produce concrete evidence for the thesis (and for budgeting) about
which geocoder works for Parañaque's mix of subdivisions, named streets,
and purok/sitio-style addresses captured in the Registry's StreetPurok column.

Output:
    - Per-row table showing both geocoder responses, in-Parañaque check,
      and final precision (street-level / subdivision-level / barangay-level / failed).
    - Summary: hit rate, in-bounds rate, estimated Google cost, recommendation.
    - CSV written to ml/geocode_compare_results.csv for the thesis appendix.

Usage:
    pip install -r ml/requirements.txt
    cp ml/.env.example ml/.env   # then add GOOGLE_MAPS_API_KEY=...
    python ml/geocode_compare.py                  # default: 50 dengue addresses
    python ml/geocode_compare.py --n 100          # larger sample
    python ml/geocode_compare.py --skip-google    # Nominatim only (no key needed)
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

logging.basicConfig(
    level=os.getenv("ML_LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("hmap.geocode_compare")


# Parañaque City rough bounding box (slightly padded). Used to reject results
# the geocoder returned that fall outside the city — common Nominatim failure
# mode when a street name also exists elsewhere in Metro Manila.
PARANAQUE_BBOX = {
    "min_lat": 14.43,
    "max_lat": 14.55,
    "min_lng": 120.97,
    "max_lng": 121.06,
}


def in_paranaque(lat: float, lng: float) -> bool:
    return (PARANAQUE_BBOX["min_lat"] <= lat <= PARANAQUE_BBOX["max_lat"]
            and PARANAQUE_BBOX["min_lng"] <= lng <= PARANAQUE_BBOX["max_lng"])


def fix_mojibake(s: str) -> str:
    """Restore Ñ — same fix the ETL applies."""
    if not isinstance(s, str):
        return s
    return s.replace("�", "Ñ")


def build_query(street_purok: str, barangay: str) -> str:
    """Build the single-shot geocoder query string (legacy / Google path).

    Google's geocoder parses multi-component address strings natively, so
    feeding it the full "subdivision, street, house" line works. For Nominatim
    use parse_street_purok + build_query_cascade instead.
    """
    street_purok = fix_mojibake(str(street_purok)).strip()
    barangay = fix_mojibake(str(barangay)).strip().title()
    return f"{street_purok}, Barangay {barangay}, Parañaque City, Metro Manila, Philippines"


# ─── Address parser ─────────────────────────────────────────────────────────

# Tokens that indicate a component is a subdivision/village rather than a street.
# Expanded to catch the residential cluster names seen in the 2026 Registry
# (place, garden, court, square, terrace — common in PH subdivision naming).
SUBDIVISION_HINTS = (
    "subd", "subdivision", "village", "homes", "compound", "cpd",
    "townhomes", "townhouse", "estate", "park", "heights",
    "place", "garden", "court", "square", "terrace", "valley",
    "manor", "residences", "enclave",
)

# Tokens that indicate a component is a named street.
STREET_HINTS = (
    " st.", " st ", " st,", " street", " ave", " avenue", " blvd", " boulevard",
    " road", " rd.", " rd ", " hwy", " highway", " drive", " dr.", " dr ",
    " lane", " ln.", " ln ", " cor.", " corner", " sitio",
)

# Tokens that indicate a component is a house/lot/block number — drop these
# from the geocoder query since Nominatim can't resolve them anyway, but they
# poison the match score if left in.
HOUSE_NUMBER_PATTERN = re.compile(
    r"^\s*("
    r"\d+[-/]?\d*[a-z]?"        # 123, 123-A, 123/4, 5B
    r"|b\s*\d+\s*l\s*\d+"        # Blk 5 Lot 10
    r"|block\s*\d+"              # Block 5
    r"|lot\s*\d+[a-z]?"          # Lot 10A
    r"|l\s*\d+\s*a?\s*\d*"       # L22 A1
    r"|annex\s*\d+"              # Annex 38
    r"|phase\s*\d+[a-z]?"        # Phase 2A
    r"|unit\s*\d+"
    r"|apt\s*\d+"
    r"|zone\s*\d+"
    r")\s*$",
    re.IGNORECASE,
)


def parse_street_purok(raw: str) -> dict[str, str | None]:
    """Split CESU's StreetPurok string into components.

    The Registry packs 2-4 components into one comma-separated string:
        "BETTERLIVING SUBD., ISRAEL ST., L22 A1"  -> subdivision + street + house
        "CANAYNAY AVENUE, 49"                      -> street + house
        "SITIO NAZARETH, BETHLEHEM ST., 02"        -> sitio + street + house
        "MERVILLE SUBD., 13"                       -> subdivision + house

    Returns dict with keys subdivision, street, house. Any may be None.
    """
    out: dict[str, str | None] = {"subdivision": None, "street": None, "house": None}
    if not raw:
        return out
    s = fix_mojibake(str(raw)).strip()
    if not s:
        return out

    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts:
        return out

    # Classify each part. Order matters here:
    #  - house numbers first (so "ANNEX 38" doesn't land in street/subd)
    #  - then sitio/purok prefixes (treated as subdivision; otherwise the "st."
    #    hint inside a *later* part would steal the street slot from sitio)
    #  - then subdivision keywords
    #  - then street keywords
    leftover = []
    sitio_re = re.compile(r"^\s*(sitio|purok)\b", re.IGNORECASE)
    for p in parts:
        pl = p.lower()
        if HOUSE_NUMBER_PATTERN.match(p):
            if out["house"] is None:
                out["house"] = p
            else:
                leftover.append(p)
            continue
        if sitio_re.match(p):
            # Sitio acts like a subdivision-level locator
            if out["subdivision"] is None:
                out["subdivision"] = p
            else:
                leftover.append(p)
            continue
        if any(h in pl for h in SUBDIVISION_HINTS):
            if out["subdivision"] is None:
                out["subdivision"] = p
            else:
                leftover.append(p)
            continue
        if any(h in (" " + pl + " ") for h in STREET_HINTS):
            if out["street"] is None:
                out["street"] = p
            else:
                leftover.append(p)
            continue
        leftover.append(p)

    # Assign anything unclassified to whichever slot is open
    for p in leftover:
        if out["street"] is None:
            out["street"] = p
        elif out["subdivision"] is None:
            out["subdivision"] = p
        elif out["house"] is None:
            out["house"] = p
        # else drop — we're already saturated

    return out


def _normalize_for_nominatim(s: str) -> str:
    """Make a component more digestible for Nominatim's tokenizer.

    Empirically, Nominatim chokes on PIDSR-style "ST." but matches "Street".
    Same for AVE./AVENUE, BLVD./BOULEVARD, etc. Expand the abbreviations and
    strip leading qualifier prefixes like "INT." (interior) and "PUROK N" that
    aren't part of the OSM-known name.
    """
    s = fix_mojibake(str(s)).strip()

    # Strip leading qualifier prefixes that pollute the geocoder query.
    # PUROK N, ZONE N: residential micro-areas not in OSM at this granularity.
    # INT.: shortcut for "interior" — the OSM name is just the street.
    leading_prefixes = [
        r"^\s*PUROK\s+\d+[A-Z]?\s*[,]?\s*",
        r"^\s*ZONE\s+\d+[A-Z]?\s*[,]?\s*",
        r"^\s*SITIO\s+",
        r"^\s*INT\.\s+",
        r"^\s*INT\s+",
        r"^\s*INTERIOR\s+",
    ]
    for pat in leading_prefixes:
        s = re.sub(pat, "", s, flags=re.IGNORECASE)

    # Expand common Philippine address abbreviations to full words
    replacements = [
        (r"\bST\.\s*", "Street "),
        (r"\bSTR\.\s*", "Street "),
        (r"\bAVE\.\s*", "Avenue "),
        (r"\bBLVD\.\s*", "Boulevard "),
        (r"\bRD\.\s*", "Road "),
        (r"\bDR\.\s*", "Drive "),
        (r"\bHWY\.\s*", "Highway "),
        (r"\bLN\.\s*", "Lane "),
        (r"\bEXT\.\s*", "Extension "),
        (r"\bSUBD\.\s*", "Subdivision "),
        (r"\bVILL\.\s*", "Village "),
        (r"\bCPD\.\s*", "Compound "),
    ]
    for pat, rep in replacements:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip(" ,.")


def _token_set(s: str) -> set[str]:
    """Tokenize a name to lowercased significant words for similarity checks."""
    if not s:
        return set()
    s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
    stop = {"street", "st", "avenue", "ave", "road", "rd", "drive", "dr",
            "boulevard", "blvd", "lane", "extension", "ext", "the", "of"}
    return {t for t in s.split() if t and t not in stop and len(t) > 1}


def _name_similar_enough(queried: str, returned: str) -> bool:
    """Reject geocoder results whose street/place name doesn't overlap with ours.

    Catches the "J. de Leon Street → N. de Leon Street" false positive class:
    Nominatim matches a different street whose name is a partial substring of
    ours and returns it. Require at least one significant token in common.
    Stop-words ("street", "the") don't count.
    """
    qt = _token_set(queried)
    rt = _token_set(returned)
    if not qt:
        # Nothing meaningful to match against — accept (don't over-reject)
        return True
    return bool(qt & rt)


def build_query_cascade(street_purok: str, barangay: str) -> list[tuple[str, str]]:
    """Build a list of (query_label, query_string) tuples to try in order.

    Each successive query is broader than the previous one. Stop at the first
    in-Parañaque result. Labels are used for telemetry / debugging.

    Query construction note: Nominatim does NOT understand "Barangay X" as a
    qualifier — it tries to find a literal place called "Barangay X" and fails.
    So we omit "Barangay" and just use the bare barangay name as part of the
    locality, the way OSM tags it.
    """
    bgy = fix_mojibake(str(barangay)).strip().title()
    bgy_suffix = f"{bgy}, Parañaque, Metro Manila, Philippines"

    parts = parse_street_purok(street_purok)
    subd = _normalize_for_nominatim(parts["subdivision"]) if parts["subdivision"] else ""
    street = _normalize_for_nominatim(parts["street"]) if parts["street"] else ""

    queries: list[tuple[str, str]] = []

    # Tier 1: subdivision + street within the barangay (best precision)
    if subd and street:
        queries.append(("subd+street+bgy", f"{street}, {subd}, {bgy_suffix}"))

    # Tier 2: just the street within the barangay
    if street:
        queries.append(("street+bgy", f"{street}, {bgy_suffix}"))

    # Tier 3: subdivision within the barangay (subdivision centroid)
    if subd:
        queries.append(("subd+bgy", f"{subd}, {bgy_suffix}"))

    # Tier 4: barangay centroid (last resort; barangay-level precision)
    queries.append(("bgy_only", bgy_suffix))

    return queries


@dataclass
class GeocodeResult:
    provider: str
    query: str
    success: bool
    lat: Optional[float] = None
    lng: Optional[float] = None
    formatted_address: Optional[str] = None
    location_type: Optional[str] = None   # google: ROOFTOP / RANGE_INTERPOLATED / GEOMETRIC_CENTER / APPROXIMATE
    osm_type: Optional[str] = None        # nominatim: node / way / relation
    osm_class: Optional[str] = None       # nominatim: place / highway / etc.
    in_paranaque: Optional[bool] = None
    error: Optional[str] = None
    elapsed_ms: Optional[int] = None
    # Nominatim cascade: which tier of query produced this hit (e.g. "street+bgy")
    query_tier: Optional[str] = None
    # Number of queries attempted before giving up or finding a match
    attempts: int = 1


# ─── Nominatim (free, OSM) ──────────────────────────────────────────────────

def _geocode_nominatim_one(query: str, user_agent: str) -> GeocodeResult:
    """Single Nominatim query. Used internally by the cascade."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "ph",
        "viewbox": f"{PARANAQUE_BBOX['min_lng']},{PARANAQUE_BBOX['max_lat']},"
                   f"{PARANAQUE_BBOX['max_lng']},{PARANAQUE_BBOX['min_lat']}",
        "bounded": 0,
    }
    headers = {"User-Agent": user_agent}
    t0 = time.monotonic()
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        elapsed = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return GeocodeResult(provider="nominatim", query=query, success=False,
                                 error=f"HTTP {r.status_code}", elapsed_ms=elapsed)
        results = r.json()
        if not results:
            return GeocodeResult(provider="nominatim", query=query, success=False,
                                 error="no_results", elapsed_ms=elapsed)
        top = results[0]
        lat, lng = float(top["lat"]), float(top["lon"])
        return GeocodeResult(
            provider="nominatim",
            query=query,
            success=True,
            lat=lat,
            lng=lng,
            formatted_address=top.get("display_name"),
            osm_type=top.get("osm_type"),
            osm_class=top.get("class"),
            in_paranaque=in_paranaque(lat, lng),
            elapsed_ms=elapsed,
        )
    except requests.RequestException as e:
        return GeocodeResult(provider="nominatim", query=query, success=False,
                             error=str(e)[:120], elapsed_ms=int((time.monotonic() - t0) * 1000))


def geocode_nominatim_cascade(street_purok: str, barangay: str,
                               user_agent: str, sleep_between: float = 1.1) -> GeocodeResult:
    """Try progressively coarser Nominatim queries until one matches inside Parañaque.

    Stops at the first in-bounds result. The similarity-rejection check was
    tried but removed: it killed valid alias matches (COASTAL ROAD →
    Manila-Cavite Expressway) while still letting partial-match false
    positives through (J. de Leon → N. de Leon both share 'de leon').
    Better to accept-with-uncertainty and document the false-positive rate
    in the thesis than to over-reject.
    """
    tiers = build_query_cascade(street_purok, barangay)
    last: GeocodeResult | None = None
    attempts = 0
    for label, q in tiers:
        attempts += 1
        if attempts > 1:
            time.sleep(sleep_between)
        res = _geocode_nominatim_one(q, user_agent)
        res.query_tier = label
        res.attempts = attempts
        last = res
        if res.success and res.in_paranaque:
            return res
    if last is None:
        return GeocodeResult(provider="nominatim", query="", success=False,
                             error="no_tiers_built", attempts=0)
    last.attempts = attempts
    return last


# ─── Google Geocoding API ───────────────────────────────────────────────────

def geocode_google(query: str, api_key: str) -> GeocodeResult:
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": api_key,
        "region": "ph",
        # Bias toward Parañaque bbox (rectangle: southwest|northeast)
        "bounds": f"{PARANAQUE_BBOX['min_lat']},{PARANAQUE_BBOX['min_lng']}|"
                  f"{PARANAQUE_BBOX['max_lat']},{PARANAQUE_BBOX['max_lng']}",
    }
    t0 = time.monotonic()
    try:
        r = requests.get(url, params=params, timeout=15)
        elapsed = int((time.monotonic() - t0) * 1000)
        if r.status_code != 200:
            return GeocodeResult(provider="google", query=query, success=False,
                                 error=f"HTTP {r.status_code}", elapsed_ms=elapsed)
        data = r.json()
        status = data.get("status")
        if status == "ZERO_RESULTS":
            return GeocodeResult(provider="google", query=query, success=False,
                                 error="zero_results", elapsed_ms=elapsed)
        if status != "OK":
            return GeocodeResult(provider="google", query=query, success=False,
                                 error=f"status={status} msg={data.get('error_message','')[:80]}",
                                 elapsed_ms=elapsed)
        top = data["results"][0]
        loc = top["geometry"]["location"]
        lat, lng = float(loc["lat"]), float(loc["lng"])
        return GeocodeResult(
            provider="google",
            query=query,
            success=True,
            lat=lat,
            lng=lng,
            formatted_address=top.get("formatted_address"),
            location_type=top["geometry"].get("location_type"),
            in_paranaque=in_paranaque(lat, lng),
            elapsed_ms=elapsed,
        )
    except requests.RequestException as e:
        return GeocodeResult(provider="google", query=query, success=False,
                             error=str(e)[:120], elapsed_ms=int((time.monotonic() - t0) * 1000))


# ─── Sampling ───────────────────────────────────────────────────────────────

def stratified_sample(df: pd.DataFrame, n: int, seed: int = 42) -> pd.DataFrame:
    """Pick n dengue rows spread roughly evenly across the 16 barangays,
    biased toward recent years where the StreetPurok column is best populated.

    Filters out rows that can't possibly geocode: barangay UNKNOWN / out-of-city,
    and StreetPurok placeholder values like 'NO DATA'. These should be tested
    only at the ETL-rejection layer, not at the geocoder layer.
    """
    df = df[df["Disease"].astype(str).str.lower().str.startswith("dengue")].copy()
    df = df[df["StreetPurok"].notna() & df["Barangay"].notna()]
    # Bias toward recent years (most relevant for clustering)
    df = df[df["Year"] >= 2018]

    # Restrict to the 16 official Parañaque barangays (mirrors ETL's filter set).
    # Out-of-city / unknown rows would land in excluded_cases and never reach the
    # geocoder in production, so they shouldn't appear in this benchmark either.
    valid_bgys = {
        "BACLARAN", "B. F. HOMES", "B.F. HOMES", "DON BOSCO", "DON GALO",
        "LA HUERTA", "MARCELO GREEN", "MARCELO GREEN VILLAGE", "MERVILLE",
        "MOONWALK", "SAN ANTONIO", "SAN DIONISIO", "SAN ISIDRO",
        "SAN MARTIN DE PORRES", "SANTO NIÑO", "SUN VALLEY", "TAMBO", "VITALEZ",
    }
    df["_bgy_clean"] = df["Barangay"].astype(str).map(fix_mojibake).str.upper().str.strip()
    df = df[df["_bgy_clean"].isin(valid_bgys)]

    # Drop rows whose StreetPurok is a placeholder rather than a real address.
    placeholders = {"NO DATA", "N/A", "NA", "NONE", "UNKNOWN", "-", "."}
    df["_sp_clean"] = df["StreetPurok"].astype(str).str.upper().str.strip()
    df = df[~df["_sp_clean"].isin(placeholders)]
    df = df[df["_sp_clean"].str.len() >= 5]  # too short to geocode meaningfully

    df = df.drop(columns=["_bgy_clean", "_sp_clean"])

    per_bgy = max(1, n // 16)
    parts = []
    for _, group in df.groupby("Barangay"):
        take = min(per_bgy, len(group))
        parts.append(group.sample(take, random_state=seed))
    sample = pd.concat(parts, ignore_index=True)
    if len(sample) > n:
        sample = sample.sample(n, random_state=seed).reset_index(drop=True)
    return sample


# ─── Main comparison ────────────────────────────────────────────────────────

def classify_precision(res: GeocodeResult) -> str:
    """Categorize the precision of a successful geocode."""
    if not res.success or not res.in_paranaque:
        return "failed"
    if res.provider == "google":
        return {
            "ROOFTOP": "street_level",
            "RANGE_INTERPOLATED": "street_level",
            "GEOMETRIC_CENTER": "subdivision_level",
            "APPROXIMATE": "barangay_level",
        }.get(res.location_type or "", "unknown")
    if res.provider == "nominatim":
        # The cascade tier that matched is a stronger precision signal than
        # osm_type, because we picked the tier ourselves.
        return {
            "subd+street+bgy": "street_level",
            "street+bgy":      "street_level",
            "subd+bgy":        "subdivision_level",
            "bgy_only":        "barangay_level",
        }.get(res.query_tier or "", "unknown")
    return "unknown"


def run_comparison(sample: pd.DataFrame, google_key: str | None, user_agent: str,
                   skip_google: bool) -> list[dict]:
    out: list[dict] = []
    for i, row in sample.iterrows():
        google_query = build_query(row["StreetPurok"], row["Barangay"])
        parsed = parse_street_purok(row["StreetPurok"])
        log.info("[%d/%d] %s | parsed: subd=%s street=%s house=%s",
                 i + 1, len(sample), row["StreetPurok"][:50],
                 parsed["subdivision"], parsed["street"], parsed["house"])

        # Nominatim cascade (handles its own throttling between tiers)
        nom = geocode_nominatim_cascade(row["StreetPurok"], row["Barangay"], user_agent)
        time.sleep(1.1)  # Throttle to the next sample's first cascade call

        # Google (single shot — its parser handles multi-component strings)
        if skip_google or not google_key:
            goog = GeocodeResult(provider="google", query=google_query, success=False,
                                 error="skipped" if skip_google else "no_api_key")
        else:
            goog = geocode_google(google_query, google_key)

        out.append({
            "row_index": int(i),
            "raw_street_purok": row["StreetPurok"],
            "barangay": row["Barangay"],
            "year": int(row["Year"]),
            "parsed_subdivision": parsed["subdivision"],
            "parsed_street": parsed["street"],
            "parsed_house": parsed["house"],
            # Nominatim
            "nom_query": nom.query,
            "nom_query_tier": nom.query_tier,
            "nom_attempts": nom.attempts,
            "nom_success": nom.success,
            "nom_lat": nom.lat,
            "nom_lng": nom.lng,
            "nom_in_pque": nom.in_paranaque,
            "nom_precision": classify_precision(nom),
            "nom_formatted": nom.formatted_address,
            "nom_osm_type": nom.osm_type,
            "nom_error": nom.error,
            # Google
            "goog_query": google_query,
            "goog_success": goog.success,
            "goog_lat": goog.lat,
            "goog_lng": goog.lng,
            "goog_in_pque": goog.in_paranaque,
            "goog_precision": classify_precision(goog),
            "goog_formatted": goog.formatted_address,
            "goog_location_type": goog.location_type,
            "goog_error": goog.error,
        })
    return out


def summarize(results: list[dict], skip_google: bool) -> None:
    n = len(results)
    bar = "=" * 80
    print()
    print(bar)
    print(f"  Geocoder comparison on {n} dengue addresses from PIDSR Registry")
    print(bar)

    def pct(c: int) -> str:
        return f"{c}/{n} ({c/n*100:.1f}%)"

    # Nominatim stats
    nom_in_pque = sum(1 for r in results if r["nom_in_pque"])
    nom_street = sum(1 for r in results if r["nom_precision"] == "street_level")
    nom_subd = sum(1 for r in results if r["nom_precision"] == "subdivision_level")
    nom_bgy = sum(1 for r in results if r["nom_precision"] == "barangay_level")
    nom_failed = sum(1 for r in results if r["nom_precision"] == "failed")
    nom_usable = nom_street + nom_subd  # what the 200m cluster rule can actually use

    # Cascade tier distribution
    from collections import Counter
    tier_hits = Counter(r["nom_query_tier"] for r in results if r["nom_in_pque"])

    print()
    print("  Nominatim cascade (OSM, free):")
    print(f"    Any in-Parañaque match:    {pct(nom_in_pque)}")
    print(f"    Usable for 200m clustering:{pct(nom_usable)}  (street + subdivision tiers)")
    print(f"      Street-level:            {pct(nom_street)}")
    print(f"      Subdivision-level:       {pct(nom_subd)}")
    print(f"    Barangay-level (too rough):{pct(nom_bgy)}")
    print(f"    Total failed:              {pct(nom_failed)}")
    print()
    print("  Cascade tier that produced each hit:")
    for tier in ("subd+street+bgy", "street+bgy", "subd+bgy", "bgy_only"):
        c = tier_hits.get(tier, 0)
        print(f"    {tier:<22} {pct(c)}")

    if not skip_google:
        goog_success = sum(1 for r in results if r["goog_success"])
        goog_in_pque = sum(1 for r in results if r["goog_in_pque"])
        goog_street = sum(1 for r in results if r["goog_precision"] == "street_level")
        goog_subd = sum(1 for r in results if r["goog_precision"] == "subdivision_level")
        goog_bgy = sum(1 for r in results if r["goog_precision"] == "barangay_level")

        print()
        print("  Google Geocoding API:")
        print(f"    Any response:              {pct(goog_success)}")
        print(f"    Result inside Parañaque:   {pct(goog_in_pque)}")
        print(f"    Street-level (ROOFTOP):    {pct(goog_street)}")
        print(f"    Subdivision-level:         {pct(goog_subd)}")
        print(f"    Barangay-level (too rough):{pct(goog_bgy)}")

        # Cost projection
        unique_addrs = 20_459  # from analysis of 2026 Registry
        backfill_cost = unique_addrs * 5 / 1000  # $5 per 1000 = current Google pricing
        new_per_month = 200
        monthly_cost_after_cache = new_per_month * 0.3 * 5 / 1000  # ~30% cache miss

        print()
        print("  Projected cost for production (with caching):")
        print(f"    One-time backfill (~{unique_addrs:,} unique dengue addrs): ${backfill_cost:.2f}")
        print(f"    -> Covered by Google's $200/mo free credit:    YES")
        print(f"    Ongoing (~200 new cases/mo, ~70% cache hit):   ~${monthly_cost_after_cache:.2f}/mo")
        print(f"    -> Effective recurring cost:                   $0 (inside free tier)")

        # Comparison summary
        print()
        print("  Head-to-head:")
        goog_better = sum(1 for r in results
                          if (r["goog_in_pque"] and not r["nom_in_pque"])
                          or (r["goog_precision"] in ("street_level", "subdivision_level")
                              and r["nom_precision"] in ("barangay_level", "failed")))
        nom_better = sum(1 for r in results
                         if (r["nom_in_pque"] and not r["goog_in_pque"])
                         or (r["nom_precision"] in ("street_level", "subdivision_level")
                             and r["goog_precision"] in ("barangay_level", "failed")))
        both_good = sum(1 for r in results
                        if r["goog_in_pque"] and r["nom_in_pque"]
                        and r["goog_precision"] not in ("failed", "barangay_level")
                        and r["nom_precision"] not in ("failed", "barangay_level"))
        both_failed = sum(1 for r in results
                          if r["goog_precision"] in ("failed", "barangay_level")
                          and r["nom_precision"] in ("failed", "barangay_level"))

        print(f"    Both produced usable precision:   {pct(both_good)}")
        print(f"    Only Google was usable:           {pct(goog_better)}")
        print(f"    Only Nominatim was usable:        {pct(nom_better)}")
        print(f"    Both failed / barangay-level:     {pct(both_failed)}")

        print()
        if goog_street + goog_subd > nom_street + nom_subd:
            print("  Recommendation: Google Geocoding API for production.")
            print("    Higher hit rate at street/subdivision precision (which the 200m")
            print("    cluster rule requires). Cache aggressively; cost stays near $0.")
        else:
            print("  Recommendation: Nominatim is good enough for this dataset.")
            print("    Use the free path; only escalate to Google for cache-miss addresses")
            print("    that come back barangay-level or failed.")

    print()
    print(f"  Detailed results written to: {RESULTS_CSV.relative_to(REPO)}")
    print(bar)


# ─── Entry point ────────────────────────────────────────────────────────────

RESULTS_CSV = HERE / "geocode_compare_results.csv"


def smoke_test_parser() -> None:
    """Print the parser output for a handful of representative addresses.

    Quick sanity check before burning ~5 minutes of Nominatim quota on a
    50-row run. If the parser is splitting things wrong, fix it here first.
    """
    samples = [
        ("BETTERLIVING SUBD., ISRAEL ST., L22 A1", "DON BOSCO"),
        ("CANAYNAY AVENUE, 49", "SAN DIONISIO"),
        ("SITIO NAZARETH, BETHLEHEM ST., 02", "SAN ISIDRO"),
        ("MERVILLE SUBD., 13", "MERVILLE"),
        ("FOURTH ESTATE SUBD., INT. BANNER GARDEN, 18", "SAN ANTONIO"),
        ("BETTERLIVING SUBD., ANNEX 38, 8", "DON BOSCO"),
        ("ST. JOSEPH CULDE SAC A-029", "SUN VALLEY"),
        ("SEVERINA DIAMOND SUBD., VALENCIA ST., 605A", "MARCELO GREEN"),
    ]
    print()
    print("  Parser smoke test:")
    print(f"    {'raw StreetPurok':<48} -> {'subd':<22} | {'street':<18} | house")
    for raw, _bgy in samples:
        p = parse_street_purok(raw)
        print(f"    {raw[:48]:<48} -> {(p['subdivision'] or '-')[:22]:<22} | "
              f"{(p['street'] or '-')[:18]:<18} | {p['house'] or '-'}")
    print()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=50, help="sample size (default: 50)")
    p.add_argument("--skip-google", action="store_true",
                   help="skip Google API calls (Nominatim only — no API key needed)")
    p.add_argument("--parser-only", action="store_true",
                   help="just print the parser smoke test and exit (no API calls)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    if args.parser_only:
        smoke_test_parser()
        return

    load_dotenv(HERE / ".env")
    google_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip() or None
    user_agent = os.getenv("NOMINATIM_USER_AGENT", "hmap-capstone").strip()

    if not args.skip_google and not google_key:
        print("ERROR: GOOGLE_MAPS_API_KEY not set in ml/.env.", file=sys.stderr)
        print("       Either set it, or re-run with --skip-google to test Nominatim only.",
              file=sys.stderr)
        sys.exit(2)

    # Find the registry file (reuse etl_registry's logic)
    candidates = list((REPO / "docs").glob("PIDSR Report YR *.xlsx"))
    if not candidates:
        print("ERROR: no PIDSR Excel found in docs/", file=sys.stderr)
        sys.exit(2)
    def year_of(path: Path) -> int:
        m = re.search(r"YR\s*(\d{4})", path.name)
        return int(m.group(1)) if m else 0
    registry = max(candidates, key=year_of)

    log.info("loading %s", registry.name)
    df = pd.read_excel(registry, sheet_name="Registry")
    sample = stratified_sample(df, args.n, seed=args.seed)
    log.info("sampled %d dengue rows across %d barangays",
             len(sample), sample["Barangay"].nunique())

    results = run_comparison(sample, google_key, user_agent, args.skip_google)

    # Write CSV
    if results:
        with open(RESULTS_CSV, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            writer.writeheader()
            writer.writerows(results)

    summarize(results, args.skip_google)


if __name__ == "__main__":
    main()
