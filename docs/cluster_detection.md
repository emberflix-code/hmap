# H-MAP Dengue Cluster Detection

Implemented in [ml/detect_clusters.py](../ml/detect_clusters.py). Manual validation tool in [ml/inspect_cluster.py](../ml/inspect_cluster.py). Surfaced via Laravel at `GET /api/clusters`. Schema in `case_clusters`, `case_cluster_members`, `detection_runs`.

This module is the **thesis's headline novelty contribution**. EWARN thresholds (Module 3) and Prophet/RF (Module 4) are existing methodologies — what's new here is operationalizing CESU's spoken clustering directive computationally.

## CESU's operational directive

Per [memory/project_dengue_clustering.md](../memory/project_dengue_clustering.md), the rule comes verbatim from Parañaque CESU:

> **200-meter radius of more than 2 cases in a 4-week period, basis is street address.**

That translates to three parameters:

| Parameter | Value | Role |
|---|---|---|
| `eps` | 200 meters | Spatial neighborhood radius |
| `min_samples` | 3 (= "more than 2") | Minimum cluster size |
| `window_weeks` | 4 morbidity weeks | Temporal sliding window |

Implementation choice: **DBSCAN** (Ester et al., 1996). DBSCAN doesn't need you to specify the number of clusters, accommodates arbitrary cluster shapes, treats spatially isolated cases as noise, and operationalizes the "within `eps` of at least `min_samples` points" rule directly. KDE (the other classical choice) produces a continuous case-density surface — descriptive, not event-oriented — which is what the heat map already does. DBSCAN produces discrete cluster assignments suitable for triggering field investigation.

## Biological basis for the 200m / 4-week numbers

Both parameters are biologically calibrated, not arbitrary:

- **200-meter radius.** *Aedes aegypti*, the principal dengue vector, has a documented adult flight range of approximately 100–200 meters across its lifetime (Harrington et al., 2005, mark-release-recapture study). Cases within 200m of one another are within plausible range of being infected by the same mosquito population; cases farther apart are more likely independent transmission events.
- **4-week window.** Combined human intrinsic incubation (4–10 days) plus mosquito extrinsic incubation (8–12 days) defines a transmission cycle of two to three weeks. A four-week window accommodates this cycle with margin for delayed reporting and clinical recognition (WHO, 2018).

These two citations together justify the parameter choice in defensibly biological terms rather than as black-box ML hyperparameters.

## Algorithm

```
for each rolling 4-morbidity-week window (1-week stride) across the case data:
    points = [(lat, lng) for case in window if geocode usable]
    DBSCAN(eps=200/EARTH_RADIUS_M, min_samples=3, metric='haversine').fit(points)
    for each non-noise cluster:
        record (window_start, window_end, member case_ids, centroid, radius)

deduplicate across windows by SHA1(sorted member case_ids) — same physical
cluster appears in several consecutive windows; keep its FIRST appearance.

INSERT INTO case_clusters + case_cluster_members + detection_runs
```

**Eligible cases.** Only cases with:

- `case_classification ∈ {Confirmed, Probable}` — same filter as WHO EWARN, matches PIDSR surveillance practice
- `geocode_source ∈ {nominatim_street, nominatim_subd, manual_pin}` — barangay-centroid geocodes are too coarse for the 200m rule (see [geocoding.md](geocoding.md))
- `status_flag = 'Active'` — soft-deleted rows excluded

**Haversine metric.** DBSCAN's `metric='haversine'` expects radian-encoded (lat, lng) and produces distances in radians, so `eps` is converted from meters via dividing by the earth's radius (6,371,008 m). Approximation is fine at Parañaque latitudes — error vs. true geodesic distance is well under 1% over a 200m radius.

**Cross-window deduplication.** Because of the 1-week stride, a cluster of cases that all reported in week N will typically appear in the windows ending at weeks N, N+1, N+2, and N+3 — four identical sets of member case_ids across overlapping windows. We compute a SHA1 fingerprint of the sorted member case_ids and keep only the FIRST appearance of each fingerprint. This is what makes "2,234 clusters" a meaningful count rather than a window-multiplicity inflated number.

## Current results

From `detection_run #2` (the latest run as of writing):

```
Disease:               DENGUE
Parameters:            eps=200m  min_samples=3  window_weeks=4
Cases evaluated:       10,042 (Confirmed+Probable with usable geocodes)
Clusters detected:     2,234
Cross-barangay:        288  (12.9% of all clusters)
Avg cluster size:      5.1 cases
Avg cluster radius:    106m  (well under the 200m eps cap)
Largest cluster:       37 cases
```

Cluster volume per year, showing both the seasonal pattern and the 2019 outbreak:

| Year | Clusters | Notes |
|---|---|---|
| 2010 | 13 | |
| 2011 | 6 | |
| 2012 | 77 | |
| 2013 | 62 | |
| 2014 | 28 | |
| 2015 | 170 | |
| 2016 | 93 | |
| 2017 | 164 | |
| 2018 | 318 | |
| **2019** | **536** | Pre-pandemic Dengue peak — biggest year in the dataset |
| 2020 | 31 | COVID lockdown — mobility down, reporting collapsed |
| 2021 | 32 | COVID continued |
| 2022 | 106 | Recovery begins |
| 2023 | 41 | |
| 2024 | 320 | Post-COVID Dengue resurgence |
| 2025 | 224 | |
| 2026 | 13 | YTD |

**The 2019 outbreak is correctly rediscovered.** The model wasn't told that 2019 was an outbreak year; the cluster density emerges from the same data the per-barangay EWARN thresholds use.

## The cross-barangay finding (thesis headline result)

**288 of 2,234 detected clusters (12.9%) involve cases spanning two or more barangays.**

This is the thesis's headline finding because it directly demonstrates a surveillance capability that per-barangay aggregation cannot provide. Worked example:

> A cluster of 5 dengue cases located along a single street that straddles two barangays appears as 3 cases in Barangay A and 2 in Barangay B. Per-barangay EWARN aggregation evaluates each independently against its 5-year-mean threshold; neither subset of 3 or 2 typically exceeds a per-barangay threshold for that morbidity week, so the EWARN module raises no alert. H-MAP's cluster detection, operating on geocoded coordinates rather than administrative aggregates, identifies the 5-case cluster as a single transmission event and surfaces it for field investigation.

CESU's spoken directive ("basis is street address") implicitly anticipates this — the rule was always meant to be applied at the patient-address level, not the barangay aggregate. The contribution of H-MAP is computational support for what was already operational doctrine but performed mentally.

## Manual validation workflow

Use [ml/inspect_cluster.py](../ml/inspect_cluster.py) to verify a detected cluster geographically before trusting the detection for the thesis:

```powershell
# Top 5 largest clusters in the latest run, with Google Maps links per member
python ml\inspect_cluster.py

# Specific cluster
python ml\inspect_cluster.py --cluster-id 42

# Top N
python ml\inspect_cluster.py --top 20
```

For each member case, the script prints the address, lat/lng, and a clickable `https://www.google.com/maps?q=LAT,LNG` URL. Manually open a few of these for the same cluster — they should visibly be on the same street or in the same subdivision.

## API contract

### `GET /api/clusters/latest-run`

Returns the parameters + summary of the most recent detection run:

```json
{
  "detection_run_id": 2,
  "run_at": "2026-05-22T00:19:52Z",
  "disease_code": "DENGUE",
  "eps_meters": 200.0,
  "min_samples": 3,
  "window_weeks": 4,
  "cases_evaluated": 10042,
  "clusters_detected": 2234
}
```

### `GET /api/clusters?from=YYYY-MM-DD&to=YYYY-MM-DD`

List of detected clusters within a date range. Each entry includes centroid, radius, case count, and barangays involved — enough to render markers on a map without a per-cluster API call.

### `GET /api/clusters/{clusterId}`

Detail view: the cluster's window, centroid, radius, and the full list of member cases with coordinates. Used by the dashboard's "inspect this cluster" workflow.

All three routes are HRMO-gated (any active employee can read clusters — they're aggregated, not patient-identifying).

## Re-running

Cluster detection is **offline**: it doesn't run on every new case insert. Re-run it after a batch of new cases or a fresh ETL load:

```powershell
python ml\detect_clusters.py                       # full historical sweep, default params
python ml\detect_clusters.py --year 2024            # only sweep windows starting in 2024
python ml\detect_clusters.py --eps 150 --min 4 --weeks 3   # parameter sweep for sensitivity analysis
```

Each invocation writes a new `detection_runs` row, and the Laravel API always returns the latest one — so you can A/B compare parameter choices for the thesis evaluation chapter.

## Known limitations (for thesis Ch.4)

1. **Geocoding ceiling.** 28% of dengue cases geocode only to barangay centroid (see [geocoding.md](geocoding.md)); those cases are excluded from cluster detection entirely. The true cluster count is therefore an **undercount** of detectable clusters had the geocoder been more accurate. Mitigation: the case-entry UI's `manual_pin` workflow lets encoders correct this case-by-case for new entries.

2. **DBSCAN parameter sensitivity.** The 200m / 3 / 4-week trio comes from CESU's spoken directive, not from a grid search. A formal sensitivity analysis (eps ∈ {100, 150, 200, 300}, min_samples ∈ {2, 3, 4, 5}, window_weeks ∈ {2, 3, 4, 6}) would strengthen the evaluation chapter. Each cell of the grid is one `detect_clusters.py --eps X --min Y --weeks Z` invocation; results land in `detection_runs` and can be diff'd.

3. **No mosquito-vector data.** The 200m radius is the *Aedes aegypti* flight range from Harrington et al. (2005) — a Thai field study. Parañaque's urban mosquito ecology may differ. Field validation (entomological surveys correlating detected clusters with ovitrap density or larval indices) is beyond v1 scope and identified as future work.

4. **Dengue-only.** The 200m radius is biologically meaningful for *Aedes aegypti*-borne disease. It is NOT directly applicable to non-vector-borne diseases. Extension to other PIDSR-notifiable diseases would require disease-specific spatial parameters (e.g., respiratory diseases use household clustering at much shorter ranges). Identified as future work.

## Citation pull-quotes for the thesis

> A spatial cluster detection module that identifies geographically and temporally co-occurring dengue cases using density-based clustering (DBSCAN), operationalizing the CESU directive of three or more cases within a 200-meter radius across a four-week morbidity window, with the capability to detect transmission clusters that cross barangay administrative boundaries (Ester et al., 1996; Harrington et al., 2005).

(Already incorporated as the proposed Ch.1 Specific Objective 1.d in [CHAPTERS_1_TO_3_REVISIONS.md](CHAPTERS_1_TO_3_REVISIONS.md) §1.3.)

> H-MAP addresses this limitation by performing cluster detection on geocoded individual case coordinates rather than barangay-aggregated counts, surfacing transmission patterns that cross administrative boundaries and that the existing per-barangay surveillance cannot detect.

(Already incorporated in [CHAPTERS_1_TO_3_REVISIONS.md](CHAPTERS_1_TO_3_REVISIONS.md) §1.4.)

## References

- Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *Proceedings of the 2nd International Conference on Knowledge Discovery and Data Mining (KDD-96)*, 226–231.
- Harrington, L. C., Scott, T. W., Lerdthusnee, K., et al. (2005). Dispersal of the dengue vector *Aedes aegypti* within and between rural communities. *American Journal of Tropical Medicine and Hygiene*, 72(2), 209–220.
- WHO (2018). *Early detection, assessment and response to acute public health events*. (Same citation as [thresholds.md](thresholds.md) — cited here for the 4-week temporal window calibration.)
