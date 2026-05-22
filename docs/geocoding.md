# H-MAP Address Geocoding

Implemented in [ml/geocode.py](../ml/geocode.py). Served by FastAPI at `POST /geocode`. Proxied by Laravel at `POST /api/geocode`. Persistent cache in `hmap_db.geocode_cache`.

## Why we need it

The PIDSR Registry includes a `StreetPurok` column with human-readable patient addresses (`"SAMPALOC SITE 2, DALANDAN ST., 474"`). Per [memory/reference_address_data.md](../memory/reference_address_data.md), ~95% of dengue cases have a non-blank `StreetPurok`. To run household-level cluster detection (Module 6, the [200m / ≥3 / 4-week rule](cluster_detection.md)), we need to convert those strings to (lat, lng) coordinates with enough precision to be usable inside a 200-meter radius — i.e., **street-level or subdivision-level**, not just barangay centroid.

## The cascade

The geocoder isn't a single Nominatim call. It's a strategy that tries the most specific query first and falls back to less specific ones, recording the precision of whichever tier matched:

| Tier | Query format | Records `geocode_source` as |
|---|---|---|
| 1. subdivision + street + barangay | `"<STREET>, <SUBDIVISION>, <BARANGAY>, Parañaque, Metro Manila, Philippines"` | `nominatim_street` |
| 2. street + barangay | `"<STREET>, <BARANGAY>, Parañaque, Metro Manila, Philippines"` | `nominatim_street` |
| 3. subdivision + barangay | `"<SUBDIVISION>, <BARANGAY>, Parañaque, Metro Manila, Philippines"` | `nominatim_subd` |
| 4. barangay only | `"<BARANGAY>, Parañaque, Metro Manila, Philippines"` | `nominatim_bgy_centroid` ← **NOT usable for the 200m rule** |
| (fallthrough) | — | `failed` |

Why the cascade pattern: Nominatim's coverage of Parañaque streets is uneven. A bare street name often matches; sometimes the subdivision name is the only thing OSM has indexed. By trying multiple query shapes and keeping the first match that lands inside the Parañaque bounding box, we get usable coordinates for far more rows than a single "best guess" query would.

**Bounding box filter.** After every Nominatim response, we check that `(lat, lng)` falls within the Parañaque BBOX (lat 14.43–14.55, lng 120.97–121.06). This rejects the common failure mode of a Nominatim match landing on a same-named street in a different city.

## Empirical validation (the 195-row benchmark)

Ran [ml/geocode_compare.py](../ml/geocode_compare.py) on a stratified random sample of 195 dengue cases. Results saved to [ml/geocode_compare_results.csv](../ml/geocode_compare_results.csv). Aggregate distribution:

| Precision | Rows | Share | Usable for 200m clusters? |
|---|---|---|---|
| `street_level` | 104 | **53.3%** | ✅ yes |
| `subdivision_level` | 37 | **19.0%** | ✅ yes (subdivisions in Parañaque are typically 100–300m across) |
| `barangay_level` | 54 | **27.7%** | ❌ no — too coarse |

**Usable street/subdivision precision: 72.3%** (104+37 of 195). This is the headline number for the thesis Ch.1 / Ch.4 limitations sections — see [CHAPTERS_1_TO_3_REVISIONS.md](CHAPTERS_1_TO_3_REVISIONS.md) §1.5.

Per [memory/reference_geocoding_findings.md](../memory/reference_geocoding_findings.md), the 28% barangay-level cases are mostly **real OSM gaps** in the PIDSR address data — i.e., that's the ceiling for free open-source geocoding of Parañaque without commercial APIs. Google Maps Geocoding API was tested as a comparator in `geocode_compare.py` but produced no improvement above Nominatim for this dataset (the `goog_*` columns in the CSV show predominantly `failed` because the streets aren't in Google's index at street-level either).

## Caching

Nominatim's usage policy caps requests at **1 per second** and requires a descriptive User-Agent. A full ETL backfill (35,000 cases) at 1 req/sec is ~10 hours; the cache makes re-runs minutes instead of hours.

The cache table (`hmap_db.geocode_cache`) is **intentionally not dropped** by `schema.sql` — it survives schema reloads:

```sql
-- geocode_cache is INTENTIONALLY not dropped: it's the address→coordinate
-- memo that lets ETL re-runs avoid re-geocoding the same addresses ...
-- The cache survives schema reloads; only its `cached_at` ages.
```

Cache key construction (see `make_cache_key` in [ml/geocode.py](../ml/geocode.py)):
- Lowercase the raw `StreetPurok` + barangay name
- Fix mojibake (`�` → `Ñ`)
- Collapse repeated whitespace
- Concatenate with a separator

So `"SAMPALOC SITE 2, DALANDAN ST., 474"` in `B. F. HOMES` produces the same key as `"sampaloc site  2, dalandan st., 474"` in `B. F. Homes` — the normalization makes the cache hit rate insensitive to encoder typos.

**Transient vs. permanent errors.** A `failed` outcome is only cached when no tier hit a transient error (rate-limit, network timeout). If Nominatim 429'd halfway through the cascade, we return `failed` to the caller but **don't write it to the cache**, so the next run gets a fresh attempt. This matters during long backfills.

## Five canonical `geocode_source` values

The `case_addresses.geocode_source` column (and the cache table) uses one of these five enum values:

| Source | Meaning | Cluster eligibility |
|---|---|---|
| `nominatim_street` | Tier 1 or 2 — street-level match | ✅ used in DBSCAN |
| `nominatim_subd` | Tier 3 — subdivision-level match | ✅ used in DBSCAN |
| `nominatim_bgy_centroid` | Tier 4 — fallthrough to barangay centroid | ❌ excluded from DBSCAN |
| `manual_pin` | Encoder dragged the pin on the map | ✅ used in DBSCAN (highest trust) |
| `failed` | No usable geocode at any tier | ❌ no coordinates stored |

`manual_pin` is the escape hatch in the case-entry UI. If the encoder sees Nominatim returned `nominatim_bgy_centroid` (yellow "approximate" warning in [CaseEntry.jsx](../laravel/resources/js/hmap/CaseEntry.jsx)), they can drag the Leaflet pin to the actual location. The pin coordinates overwrite the geocode and flag it as `manual_pin` so cluster detection can use it.

## API contract

### FastAPI: `POST /geocode`

```json
{
  "street_purok": "SAMPALOC SITE 2, DALANDAN ST., 474",
  "barangay": "B.F. Homes"
}
```

Returns:

```json
{
  "success": true,
  "lat": 14.4567274,
  "lng": 121.0270029,
  "geocode_source": "nominatim_street",
  "geocode_query": "DALANDAN Street, SAMPALOC SITE 2, B. F. Homes, Parañaque, Metro Manila, Philippines",
  "formatted": "Dalandan Street, Sampaloc Site 2, BF Homes, Parañaque District 2, ...",
  "from_cache": false
}
```

`from_cache=true` indicates the result came from `geocode_cache` and did not touch Nominatim.

### Laravel proxy: `POST /api/geocode`

Same request/response as FastAPI. HRMO-gated like every other API route. The browser never talks to FastAPI directly.

## Re-running

Geocoding happens **at case-entry time** for new cases (the form fires `POST /api/geocode` as soon as the encoder fills in street + barangay). For historical records loaded via the ETL, you can run a backfill:

```powershell
# TODO: there's no standalone backfill script yet; etl_registry.py handles
# geocoding inline when loading new rows but won't backfill pre-existing rows.
# Easiest manual approach: re-run python ml\etl_registry.py — the cache
# means already-geocoded addresses skip Nominatim and just populate
# case_addresses for any rows missing it.
```

(See [docs/cluster_detection.md](cluster_detection.md) for what happens after the addresses are geocoded.)

## Citation pull-quote for the thesis

> The chosen geocoding approach achieves usable street-level or subdivision-level precision for approximately 72% of dengue cases in the validation sample (n = 195); the remaining 28% fall back to barangay-level coordinates and contribute to choropleth visualization but not to cluster detection.

(Already incorporated as the proposed Ch.1 scope-and-limitations update in [CHAPTERS_1_TO_3_REVISIONS.md](CHAPTERS_1_TO_3_REVISIONS.md) §1.5.)
