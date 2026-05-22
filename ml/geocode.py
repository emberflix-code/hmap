"""H-MAP geocoding module: PIDSR StreetPurok → (lat, lng).

The single entry point is `geocode_case_address(conn, raw_street_purok, barangay)`,
which:
    1. Builds a normalized cache key
    2. Returns immediately if the key is already in `geocode_cache`
    3. Otherwise runs the Nominatim cascade strategy and writes to cache

The cascade strategy was validated empirically (see docs/geocoding.md and
the 195-row benchmark in ml/geocode_compare.py): 72% of dengue addresses
resolve to street- or subdivision-level precision; 28% fall to barangay
centroid and are flagged as ineligible for the 200m cluster detection.

Nominatim usage policy: 1 request/second, identifiable User-Agent. The
sleep is enforced in `geocode_via_cascade`. Do not call concurrently.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import requests

log = logging.getLogger("hmap.geocode")


# ─── Parañaque bounding box ─────────────────────────────────────────────────
# Used to reject geocoder matches that landed outside the city (common
# Nominatim failure mode when a street name also exists in another LGU).

PARANAQUE_BBOX = {
    "min_lat": 14.43,
    "max_lat": 14.55,
    "min_lng": 120.97,
    "max_lng": 121.06,
}


def in_paranaque(lat: float, lng: float) -> bool:
    return (PARANAQUE_BBOX["min_lat"] <= lat <= PARANAQUE_BBOX["max_lat"]
            and PARANAQUE_BBOX["min_lng"] <= lng <= PARANAQUE_BBOX["max_lng"])


# ─── Text normalization ─────────────────────────────────────────────────────

def fix_mojibake(s: str | None) -> str | None:
    """Restore Ñ in Registry strings that lost it during encoding round-trips."""
    if s is None or not isinstance(s, str):
        return s
    return s.replace("�", "Ñ")


SUBDIVISION_HINTS = (
    "subd", "subdivision", "village", "homes", "compound", "cpd",
    "townhomes", "townhouse", "estate", "park", "heights",
    "place", "garden", "court", "square", "terrace", "valley",
    "manor", "residences", "enclave",
)

STREET_HINTS = (
    " st.", " st ", " st,", " street", " ave", " avenue", " blvd", " boulevard",
    " road", " rd.", " rd ", " hwy", " highway", " drive", " dr.", " dr ",
    " lane", " ln.", " ln ", " cor.", " corner", " sitio",
)

HOUSE_NUMBER_PATTERN = re.compile(
    r"^\s*("
    r"\d+[-/]?\d*[a-z]?"
    r"|b\s*\d+\s*l\s*\d+"
    r"|block\s*\d+"
    r"|lot\s*\d+[a-z]?"
    r"|l\s*\d+\s*a?\s*\d*"
    r"|annex\s*\d+"
    r"|phase\s*\d+[a-z]?"
    r"|unit\s*\d+"
    r"|apt\s*\d+"
    r"|zone\s*\d+"
    r")\s*$",
    re.IGNORECASE,
)


def parse_street_purok(raw: str | None) -> dict[str, str | None]:
    """Split a CESU StreetPurok string into (subdivision, street, house).

    See ml/geocode_compare.py:parse_street_purok docstring for the rule
    rationale. The parser is rule-based and forgives misclassification: the
    cascade strategy retries with progressively broader queries, so a wrong
    component-assignment shifts which tier matches, not whether one matches.
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

    leftover: list[str] = []
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

    for p in leftover:
        if out["street"] is None:
            out["street"] = p
        elif out["subdivision"] is None:
            out["subdivision"] = p
        elif out["house"] is None:
            out["house"] = p

    return out


def _normalize_for_nominatim(s: str) -> str:
    """Make a component digestible for Nominatim's tokenizer: strip leading
    qualifier prefixes (PUROK N, ZONE N, INT.), expand street-type abbreviations."""
    s = fix_mojibake(str(s)).strip()
    for pat in (
        r"^\s*PUROK\s+\d+[A-Z]?\s*[,]?\s*",
        r"^\s*ZONE\s+\d+[A-Z]?\s*[,]?\s*",
        r"^\s*SITIO\s+",
        r"^\s*INT\.\s+",
        r"^\s*INT\s+",
        r"^\s*INTERIOR\s+",
    ):
        s = re.sub(pat, "", s, flags=re.IGNORECASE)
    for pat, rep in (
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
    ):
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip(" ,.")


# ─── Cache key ──────────────────────────────────────────────────────────────

def make_cache_key(raw_street_purok: str | None, barangay: str | None) -> str:
    """Build the geocode_cache primary key for a (street, barangay) pair.

    Deliberately conservative normalization: lowercase, mojibake-fixed,
    collapsed whitespace. Different StreetPurok strings that resolve to the
    same physical location will get different cache entries (acceptable: the
    cache hit rate is still high because most cases at the same address use
    identical raw strings, per the ETL's 1.18x reuse rate analysis).
    """
    sp = fix_mojibake(str(raw_street_purok or "")).strip().lower()
    bgy = fix_mojibake(str(barangay or "")).strip().lower()
    sp = re.sub(r"\s+", " ", sp)
    bgy = re.sub(r"\s+", " ", bgy)
    key = f"{sp}|{bgy}"
    # MySQL VARCHAR(255) PK ceiling
    return key[:255]


# ─── Cascade query builder ──────────────────────────────────────────────────

@dataclass
class GeocodeOutcome:
    """The result of geocoding a single address. Mirrors columns in
    case_addresses and geocode_cache so it can be written directly."""
    success: bool
    lat: Optional[float]
    lng: Optional[float]
    geocode_source: str   # nominatim_street | nominatim_subd | nominatim_bgy_centroid | failed
    geocode_query: Optional[str]
    formatted: Optional[str]


def _build_cascade(raw_street_purok: str, barangay: str) -> list[tuple[str, str]]:
    """Build the ordered (tier_label, query_string) pairs for the cascade.

    Tier labels feed directly into geocode_source values; see docstring of
    case_addresses table for what each tier means.
    """
    bgy = fix_mojibake(str(barangay)).strip().title()
    bgy_suffix = f"{bgy}, Parañaque, Metro Manila, Philippines"

    parts = parse_street_purok(raw_street_purok)
    subd = _normalize_for_nominatim(parts["subdivision"]) if parts["subdivision"] else ""
    street = _normalize_for_nominatim(parts["street"]) if parts["street"] else ""

    queries: list[tuple[str, str]] = []
    if subd and street:
        queries.append(("nominatim_street", f"{street}, {subd}, {bgy_suffix}"))
    if street:
        queries.append(("nominatim_street", f"{street}, {bgy_suffix}"))
    if subd:
        queries.append(("nominatim_subd", f"{subd}, {bgy_suffix}"))
    queries.append(("nominatim_bgy_centroid", bgy_suffix))
    return queries


# ─── Nominatim API ──────────────────────────────────────────────────────────

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Module-level throttle: enforce a minimum gap between ANY two Nominatim calls,
# not just between cascade tiers of the same address. The earlier pilot proved
# that per-cascade local sleeps were insufficient — once one address finished
# with a tier-1 hit (no sleep needed), the next address's tier-1 call followed
# immediately, occasionally triggering Nominatim's HTTP 429 rate-limit response
# and tanking the cascade for that address all the way through to "failed".
_last_call_monotonic = 0.0

# OSM's published usage policy is ≤1 req/sec for the public Nominatim. We use
# a small safety margin (1.1s) since their server clock and ours drift.
MIN_INTERVAL_SECONDS = 1.1

# Retry budget for HTTP 429 (rate-limit) responses. On 429, sleep this long
# and try again. Each successive retry doubles the wait. 3 retries with
# starting backoff of 2s gives a worst-case 14s per call before we give up.
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_BASE = 2.0


# Sentinel for "all retries exhausted on a transient error". Distinct from
# None (legitimate zero results) so the cascade can avoid caching this as a
# permanent failure.
class TransientGeocodeError(Exception):
    pass


def _enforce_global_rate_limit() -> None:
    """Block until at least MIN_INTERVAL_SECONDS has passed since the last call."""
    global _last_call_monotonic
    now = time.monotonic()
    elapsed = now - _last_call_monotonic
    if elapsed < MIN_INTERVAL_SECONDS:
        time.sleep(MIN_INTERVAL_SECONDS - elapsed)
    _last_call_monotonic = time.monotonic()


def _nominatim_one(query: str, user_agent: str, timeout: float = 15.0) -> dict | None:
    """Single Nominatim call. Returns the top hit dict, or None on legitimate
    no-results.

    Rate-limits internally: every call sleeps as needed to keep ≥1.1s between
    any two outbound requests. On HTTP 429 (rate limited), retries with
    exponential backoff up to RATE_LIMIT_RETRIES times. If all retries
    exhaust, raises TransientGeocodeError so the caller can decide whether
    to treat this as a permanent failure (and cache it) or skip.
    """
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

    for attempt in range(RATE_LIMIT_RETRIES + 1):
        _enforce_global_rate_limit()
        try:
            r = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            # Network error — treat as transient. Don't retry indefinitely;
            # the caller can fall through to the next cascade tier.
            log.warning("nominatim network error for %r: %s", query[:80], e)
            raise TransientGeocodeError(str(e))

        if r.status_code == 200:
            results = r.json()
            if not results:
                return None
            return results[0]

        if r.status_code == 429:
            # Back off and retry. Each attempt waits 2× the previous.
            if attempt < RATE_LIMIT_RETRIES:
                wait = RATE_LIMIT_BACKOFF_BASE * (2 ** attempt)
                log.warning("nominatim HTTP 429 (rate-limited), retry %d/%d in %.1fs: %r",
                            attempt + 1, RATE_LIMIT_RETRIES, wait, query[:60])
                time.sleep(wait)
                continue
            log.error("nominatim HTTP 429 exhausted retries for %r", query[:80])
            raise TransientGeocodeError("429 rate limit, retries exhausted")

        # Other HTTP errors (5xx, etc.) — treat as transient and bail.
        log.warning("nominatim HTTP %d for %r", r.status_code, query[:80])
        raise TransientGeocodeError(f"HTTP {r.status_code}")

    # Unreachable — the loop either returns or raises
    raise TransientGeocodeError("unexpected fall-through")


def geocode_via_cascade(raw_street_purok: str, barangay: str, user_agent: str,
                         sleep_between: float = 1.1) -> tuple[GeocodeOutcome, bool]:
    """Run the cascade against Nominatim. Rate-limiting is handled in
    `_nominatim_one` via the module-level throttle.

    Returns (outcome, is_permanent):
        outcome      — first in-Parañaque match, or a `failed` placeholder
        is_permanent — True if the cascade exhausted all tiers without finding
                       a match (caller can cache); False if any tier returned
                       a transient error (caller should NOT cache, so the
                       address gets retried on the next ETL run).
    """
    tiers = _build_cascade(raw_street_purok, barangay)
    last_query: str | None = None
    hit_transient_error = False

    for source, q in tiers:
        last_query = q
        try:
            top = _nominatim_one(q, user_agent)
        except TransientGeocodeError:
            hit_transient_error = True
            continue
        if not top:
            continue
        try:
            lat, lng = float(top["lat"]), float(top["lon"])
        except (KeyError, ValueError, TypeError):
            continue
        if not in_paranaque(lat, lng):
            continue
        return GeocodeOutcome(
            success=True,
            lat=lat,
            lng=lng,
            geocode_source=source,
            geocode_query=q,
            formatted=top.get("display_name"),
        ), True

    outcome = GeocodeOutcome(
        success=False,
        lat=None,
        lng=None,
        geocode_source="failed",
        geocode_query=last_query,
        formatted=None,
    )
    # Permanent only if no tier raised a transient error. If any tier hit a
    # network/rate-limit error, the failure is not trustworthy — don't cache.
    return outcome, not hit_transient_error


# ─── Cache integration (DB-backed) ──────────────────────────────────────────

def _cache_lookup(conn, cache_key: str) -> GeocodeOutcome | None:
    cur = conn.cursor()
    cur.execute(
        "SELECT lat, lng, geocode_source, geocode_query, formatted "
        "FROM geocode_cache WHERE cache_key = %s",
        (cache_key,),
    )
    row = cur.fetchone()
    cur.close()
    if row is None:
        return None
    lat, lng, source, query, formatted = row
    return GeocodeOutcome(
        success=(source != "failed" and lat is not None),
        lat=float(lat) if lat is not None else None,
        lng=float(lng) if lng is not None else None,
        geocode_source=source,
        geocode_query=query,
        formatted=formatted,
    )


def _cache_store(conn, cache_key: str, outcome: GeocodeOutcome) -> None:
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO geocode_cache
               (cache_key, lat, lng, geocode_source, geocode_query, formatted)
           VALUES (%s, %s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE
               lat = VALUES(lat),
               lng = VALUES(lng),
               geocode_source = VALUES(geocode_source),
               geocode_query = VALUES(geocode_query),
               formatted = VALUES(formatted),
               cached_at = CURRENT_TIMESTAMP""",
        (
            cache_key,
            outcome.lat,
            outcome.lng,
            outcome.geocode_source,
            (outcome.geocode_query or "")[:255] or None,
            (outcome.formatted or "")[:255] or None,
        ),
    )
    cur.close()


def geocode_case_address(conn, raw_street_purok: str, barangay: str,
                          user_agent: str) -> tuple[GeocodeOutcome, bool]:
    """Geocode an address, using `geocode_cache` to skip the API on repeats.

    Returns (outcome, from_cache). The caller commits the connection.

    - Blank input → `failed` outcome without ever calling Nominatim.
    - Transient errors (rate-limit, network) → outcome may be `failed` but
      we DON'T cache it, so the address gets a fresh attempt next run.
    - Successful matches and permanent fall-throughs → cached.
    """
    if not raw_street_purok or not str(raw_street_purok).strip():
        return GeocodeOutcome(success=False, lat=None, lng=None,
                              geocode_source="failed", geocode_query=None,
                              formatted=None), False

    cache_key = make_cache_key(raw_street_purok, barangay)
    cached = _cache_lookup(conn, cache_key)
    if cached is not None:
        return cached, True

    outcome, is_permanent = geocode_via_cascade(raw_street_purok, barangay, user_agent)
    if is_permanent:
        _cache_store(conn, cache_key, outcome)
    return outcome, False
