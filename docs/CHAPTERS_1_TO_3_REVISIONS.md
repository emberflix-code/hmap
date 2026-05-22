# Chapters 1-3 Revision List

Generated 2026-05-22 after reading `HMAP_Chapters_1to3_Final.pdf` (58 pages) and comparing against the current implementation.

The system has grown beyond what Chapters 1-3 describe in **one major way and several minor ways**. The major gap: **household-level dengue cluster detection (200m / ≥3 / 4-week)** is now the thesis's headline novelty contribution but is not in your objectives, scope, methodology, or schema. The minor gaps: framework stack details (Laravel/FastAPI vs the documented PHP/Flask), the geocoding pipeline, and 5 new database tables.

---

## CHAPTER 1 — THE PROBLEM AND ITS BACKGROUND

### 1.1 Introduction (pp. 1-3)

**No major changes required.** The framing of CESU's gap is still accurate. One small factual update:

- **p. 1 / p. 3** — "covering the years 2010 to 2023" and "over 30,000 patient-level records as of 2023" → update to **"covering the years 2010 to 2026"** and **"over 35,000 patient-level records as of 2026."** The 2026 PIDSR Registry is now your source dataset.

- **p. 1, line ~24** — "28 notifiable diseases" → **"29 notifiable diseases"** (your `diseases` seed actually has 29 rows including COVID-19).

### 1.2 Background of the Study (pp. 3-5)

**Add a new paragraph after the existing paragraph ending "...spreadsheet summaries that do not communicate spatial distribution or trend trajectories."** (currently page 4)

> A specific operational pain point identified during structured consultation with CESU staff is the manual geocoding workflow. To detect potential dengue outbreak clusters, CESU staff currently open Google Maps in a browser, search for each patient's reported street address, and visually inspect whether multiple cases occur within proximity of one another. This process is performed case-by-case for every dengue report, and the spatial reasoning required to identify clusters across an entire week of cases is performed mentally rather than computationally. CESU staff have specified an operational clustering rule consistent with field practice: any three or more dengue cases occurring within a 200-meter radius across a four-week period, anchored to patient street address, represents a candidate transmission cluster warranting field investigation. This 200-meter threshold aligns with the documented flight range of *Aedes aegypti*, the principal dengue vector, which disperses approximately 100 to 200 meters during its lifetime (Harrington et al., 2005). The absence of computational support for this clustering analysis directly motivates one of the analytical components of H-MAP.

### 1.3 Objectives of the Study (pp. 5-7)

**Significant changes required.** Your Specific Objective 1 enumerates the system features (a, b, c) but does not include cluster detection. Add a new sub-objective and revise the tech stack in Specific Objective 2.

**Edit Specific Objective 1 (page 5-6):**

Currently has three sub-features:
- a. heat map visualization
- b. data digitization
- c. trend monitoring with EWARN

**Replace with five sub-features** (renaming existing ones if needed):

> 1. To design a comprehensive web-based AI-assisted disease surveillance system with the following features:
>    a. An interactive heat map visualization module using Leaflet.js and OpenStreetMap that will display disease case density across Parañaque City's 16 barangays.
>    b. A data digitization and records management module for encoding disease case records consistent with PIDSR reporting standards (DOH, 2014), with integrated address geocoding to enable household-level spatial analysis.
>    c. A real-time disease trend monitoring module with automated epidemic threshold alerts based on the WHO Early Warning and Response Network (EWARN) methodology (WHO, 2018).
>    **d. A spatial cluster detection module that identifies geographically and temporally co-occurring dengue cases using density-based clustering (DBSCAN), operationalizing the CESU directive of three or more cases within a 200-meter radius across a four-week morbidity window, with the capability to detect transmission clusters that cross barangay administrative boundaries (Ester et al., 1996; Harrington et al., 2005).**
>    **e. A four-week-ahead disease case forecasting module using the Prophet time-series model, and a barangay risk classification module using the Random Forest algorithm, validated in the Philippine context by Olana et al. (2025) and Carvajal et al. (2018).**

**Edit Specific Objective 2 — the tech stack list (page 6):**

Two updates:
- "Python with Flask as an internal AI machine learning microservice" → **"Python with FastAPI as an internal AI machine learning microservice"** (you migrated to FastAPI, which gives you Pydantic typing + OpenAPI docs for free; both are good defensibility points)
- "PHP as the primary server-side scripting language, consistent with the existing HRMO portal" → **"PHP with the Laravel 11 framework as the primary server-side language, providing structured routing, validation, and middleware for HRMO session integration, consistent with the PHP runtime of the existing HRMO portal"**
- Add a new bullet: **"OpenStreetMap Nominatim as the geocoding service for converting PIDSR street addresses to coordinates, accessed under OSM's Free Usage Policy with local caching to respect rate limits."**

### 1.4 Significance of the Study (pp. 7-8)

**Add a paragraph after the existing one ending "...providing a technically documented and evaluated precedent for cost-effective AI-assisted digital health surveillance at the city LGU level in the Philippines."** (page 8)

> A further methodological contribution of this study is the operationalization of household-level spatial cluster detection at the city epidemiology unit level. Existing PIDSR-based surveillance at the city level aggregates cases at barangay resolution, producing per-barangay weekly counts that are then compared against EWARN thresholds. This aggregation, while operationally established, masks transmission clusters that occur at the boundaries between adjacent barangays: a cluster of five cases located along a single street that straddles two barangays appears as three cases in Barangay A and two in Barangay B, with neither subset exceeding the per-barangay alert threshold. H-MAP addresses this limitation by performing cluster detection on geocoded individual case coordinates rather than barangay-aggregated counts, surfacing transmission patterns that cross administrative boundaries and that the existing per-barangay surveillance cannot detect.

### 1.5 Scope and Limitations (pp. 9-10)

**Edit the paragraph listing the five modules** (page 9). Currently five modules; you now have six.

Replace the existing sentence: *"The scope of H-MAP includes five functional modules: an HRMO-integrated authentication module; a data digitization and records management module for encoding PIDSR-compliant case data; an interactive heat map visualization module built with Leaflet.js; a disease trend monitoring module with automated WHO EWARN epidemic threshold alerting (WHO, 2018); and an AI machine learning prediction module..."*

With:

> The scope of H-MAP includes six functional modules: an HRMO-integrated authentication module; a data digitization and records management module for encoding PIDSR-compliant case data with integrated address geocoding; an interactive heat map visualization module built with Leaflet.js; a disease trend monitoring module with automated WHO EWARN epidemic threshold alerting (WHO, 2018); an AI machine learning prediction module implemented as an internal Python FastAPI microservice delivering Prophet-based weekly case forecasts and Random Forest barangay risk classifications, consistent with methodologies validated in the Philippine context by Carvajal et al. (2018) and Olana et al. (2025); and a spatial cluster detection module implementing CESU's operational directive of three or more dengue cases within a 200-meter radius across a four-week morbidity window using DBSCAN density-based clustering (Ester et al., 1996; Harrington et al., 2005).

**Add a new paragraph to the limitations** (also page 9-10), after "The study does not include actual public health intervention planning..."

> The spatial cluster detection module is scoped to dengue only in this version of H-MAP. The 200-meter radius threshold is biologically derived from the *Aedes aegypti* mosquito's flight range and is not directly applicable to non-vector-borne diseases. Extension of household-level cluster detection to other PIDSR-notifiable diseases is identified as future work.

> Address geocoding precision is bounded by OpenStreetMap coverage of Parañaque City. Cases whose street addresses geocode only to the barangay-level centroid rather than to a specific street or subdivision are recorded with their geocoded coordinates but are flagged as ineligible for the 200-meter cluster detection rule, as the centroid-level coordinate is too coarse for that precision threshold. The chosen geocoding approach achieves usable street-level or subdivision-level precision for approximately 74% of dengue cases in the validation sample (n = 195); the remaining 26% fall back to barangay-level coordinates and contribute to choropleth visualization but not to cluster detection.

---

## CHAPTER 2 — CONCEPTUAL FRAMEWORK

### 2.1 Heat Mapping and Spatial Cluster Detection (p. 13-14)

**Significant expansion required.** This section currently treats clustering as a passing concept (KDE + spatial autocorrelation). It needs to become the literature foundation for your new cluster detection module.

**Add the following new subsection right after the current "Heat Mapping and Spatial Cluster Detection" section, before "Epidemic Threshold Methods":**

> **Density-Based Spatial Clustering and the *Aedes aegypti* Flight Range**
>
> Density-based spatial clustering of applications with noise (DBSCAN), introduced by Ester et al. (1996), is a non-parametric clustering algorithm that groups points based on local density without requiring a pre-specified number of clusters. DBSCAN identifies clusters as connected components of points that lie within a specified neighborhood radius (eps) of at least a minimum number of other points (minPts), and flags points outside any such neighborhood as noise. The algorithm is well-suited to disease cluster detection because it accommodates clusters of arbitrary shape, does not assume a global cluster density, and treats spatially isolated cases as noise rather than forcing them into clusters (Ester et al., 1996).
>
> The biological basis for the 200-meter radius parameter adopted in H-MAP is established by entomological studies of *Aedes aegypti*, the principal dengue vector. Harrington et al. (2005) conducted a mark-release-recapture study of *Ae. aegypti* across multiple urban sites and reported that the species typically disperses 100 to 200 meters during its adult life span, with most recaptures occurring within this range of the release point. This flight range constrains the spatial scale at which dengue transmission can occur through a single mosquito generation. The 200-meter clustering threshold therefore corresponds to a biologically interpretable spatial unit: cases within 200 meters of one another are within plausible range of being infected by the same mosquito population, while cases farther apart are more likely to represent independent transmission events.
>
> Temporal clustering parameters in dengue surveillance are similarly grounded in vector biology. The combined intrinsic incubation period in humans (typically 4 to 10 days) and extrinsic incubation period in the mosquito (8 to 12 days) defines a transmission cycle on the order of two to three weeks. A four-week temporal window, as specified in CESU's operational directive and implemented in H-MAP, accommodates this transmission cycle with margin for delayed reporting and clinical recognition. This combination of biologically calibrated spatial and temporal parameters is consistent with the recommended approach for outbreak cluster investigation in vector-borne disease surveillance (WHO, 2018).
>
> Prior research has applied density-based clustering to dengue surveillance in tropical urban contexts. Within the broader spatial epidemiology literature, Lawson (2018) discusses density-based methods alongside kernel density estimation as complementary tools for outbreak cluster detection: KDE is descriptive and visualization-oriented, producing continuous case-density surfaces, while DBSCAN is event-oriented and produces discrete cluster assignments suitable for triggering investigation workflows. H-MAP adopts KDE for the heat map visualization module and DBSCAN for the cluster detection module, applying each method to the task for which it is best suited.

### 2.2 NEW SECTION — Address Geocoding for Disease Surveillance

**Insert this entirely new subsection after the GIS in Public Health section** (around page 13, before Heat Mapping).

> **Address Geocoding for Disease Surveillance**
>
> Geocoding is the process of converting human-readable street addresses to geographic coordinates suitable for spatial analysis. For city-level disease surveillance, geocoding accuracy directly determines the spatial resolution at which clustering and hotspot analyses can be performed. Open-source geocoding services based on OpenStreetMap data, such as Nominatim, have been demonstrated to provide adequate coverage for urban areas in low- and middle-income countries when used with appropriate query strategies, though coverage of informal residential clusters, side streets, and subdivisions is typically less complete than for major thoroughfares (Boulos et al., 2011).
>
> For Philippine addresses, the standard PIDSR Registry captures patient address as a free-text field combining subdivision, street, and house-number components in a single column. Direct submission of this composite string to a geocoding service produces poor matching results because the service's parser is not calibrated to the Philippine address format. A cascading query strategy, in which the address is first parsed into its components and then submitted to the geocoder at progressively coarser specificity (street + barangay, then subdivision + barangay, then barangay centroid as fallback), substantially improves match rate. H-MAP implements this cascading strategy using Nominatim with local caching of results in a dedicated `geocode_cache` table to respect Nominatim's published usage policy of one request per second and to provide instant response for previously seen addresses on subsequent encoding sessions.

**Add to the References list (in your existing References section, alphabetical order):**

```
Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for
   discovering clusters in large spatial databases with noise. In Proceedings of the
   Second International Conference on Knowledge Discovery and Data Mining (KDD-96),
   226–231. AAAI Press.

Harrington, L. C., Scott, T. W., Lerdthusnee, K., Coleman, R. C., Costero, A., Clark, G. G.,
   Jones, J. J., Kitthawee, S., Kittayapong, P., Sithiprasasna, R., & Edman, J. D. (2005).
   Dispersal of the dengue vector Aedes aegypti within and between rural communities.
   The American Journal of Tropical Medicine and Hygiene, 72(2), 209–220.
   https://doi.org/10.4269/ajtmh.2005.72.209
```

### 2.3 Mapping of Related Literature to H-MAP System Features (p. 26-27)

**Edit the paragraph mapping literature to modules** to add a sixth mapping for the new cluster detection module.

Add after the existing sentence about the AI Machine Learning Prediction Module:

> The Spatial Cluster Detection Module is grounded in the density-based clustering algorithm introduced by Ester et al. (1996) and in the *Aedes aegypti* flight-range studies of Harrington et al. (2005), which collectively establish DBSCAN at a 200-meter neighborhood radius as a biologically appropriate spatial unit for dengue transmission-cluster detection. The four-week temporal window draws on the WHO (2018) guidance regarding *Aedes*-borne disease transmission cycles. Lawson (2018) provides the broader spatial epidemiology framing that distinguishes density-based event clustering (DBSCAN) from continuous-surface density estimation (KDE).

### 2.4 Conceptual Framework / IPO Model (p. 28-30)

**Edit the Input section** to add:

- Under "Knowledge Requirements" add: **"the operational dengue cluster detection directive of CESU staff specifying a 200-meter radius, minimum three cases, and four-week rolling window; *Aedes aegypti* flight-range studies (Harrington et al., 2005); and the DBSCAN density-based clustering algorithm (Ester et al., 1996)."**

- Under "Software Requirements" add: **"scikit-learn's DBSCAN implementation for spatial cluster detection; OpenStreetMap Nominatim for street address geocoding; and the FastAPI Python web framework (replacing the earlier Flask selection) for the AI machine learning and geocoding microservice."**

### 2.5 Operational Definition of Terms (pp. 31-33)

**Add three new entries** in alphabetical position:

> **DBSCAN.** Density-Based Spatial Clustering of Applications with Noise, a non-parametric clustering algorithm that groups points based on local density (Ester et al., 1996). In H-MAP, DBSCAN is applied to geocoded dengue case coordinates with a neighborhood radius (eps) of 200 meters and a minimum cluster size (minPts) of three, consistent with CESU's operational clustering directive and *Aedes aegypti* flight-range research (Harrington et al., 2005).

> **Geocoding.** The process of converting a human-readable street address to geographic coordinates (latitude and longitude). In H-MAP, geocoding is performed via the OpenStreetMap Nominatim service using a cascading query strategy that progressively broadens the query from subdivision+street to barangay centroid as fallback. Results are cached in a dedicated `geocode_cache` table to respect Nominatim's usage policy and accelerate subsequent encoding sessions.

> **Spatial Cluster.** In H-MAP, a set of three or more dengue cases whose geocoded coordinates lie within a 200-meter neighborhood radius of one another (in the DBSCAN sense), with case onset dates spanning a rolling four-week period. Clusters that include cases from two or more adjacent barangays are designated cross-barangay clusters and represent transmission patterns not detectable by the per-barangay WHO EWARN threshold module.

---

## CHAPTER 3 — METHODOLOGY

### 3.1 System Overview (p. 35-37)

**Edit the bulleted list of user actions (currently a-f). Add a new bullet between e and f** (between AI forecast and report export):

> g. Detect spatial clusters of dengue cases meeting CESU's operational rule of three or more cases within 200 meters across a four-week morbidity window, with cluster results visualized as case-density circles on the Leaflet.js map and listed in an alert panel sortable by recency, size, and number of barangays involved.

### 3.2 System Modules (p. 38-40)

**Major change.** You currently document five modules. You need to:

1. **Update Module 1** to mention address geocoding integration.
2. **Add a new Module 6** for spatial cluster detection.

**Replace the Module 1 description** ("This module will provide a structured web-based interface for encoding PIDSR disease case records...") with:

> Module 1: Data Digitization and Records Management. This module will provide a structured web-based interface for encoding PIDSR disease case records into the H-MAP MySQL database. Input fields will mirror the PIDSR case report form, consistent with DOH (2014) reporting standards, including disease name, case classification, date of onset, date of admission, patient barangay, **patient street and purok address**, reporting health facility, age, sex, vaccination history, and case outcome. Input validation will check completeness and classification consistency before record insertion. **Upon entry of a street address, the module will invoke the geocoding service (see Section 3.X — Address Geocoding Pipeline) and present the encoder with a confirmation pin on a Leaflet.js preview map. The encoder may accept the auto-located position or drag the pin to a corrected location; manually corrected pins are recorded with `geocode_source = manual_pin` so that downstream cluster detection treats the encoder's correction as authoritative.** A batch import function will support CSV upload of multiple records using a PIDSR-compatible template, facilitating transfer of historical data from existing Excel-based surveillance records.

**Add a new Module 6 description** after Module 5:

> Module 6: Spatial Cluster Detection. This module will implement CESU's operational directive for dengue cluster surveillance: identification of any three or more dengue cases whose geocoded coordinates lie within a 200-meter radius across a four-week morbidity-week window. The module will be implemented as an offline batch process invoked nightly and on-demand, scanning all dengue cases of Confirmed or Probable case classification with usable-precision geocodes (i.e., geocode source not equal to barangay centroid). For each four-week sliding window across the historical and current case data, the DBSCAN algorithm will be applied with eps = 200 meters (converted to radians for the haversine distance metric) and minPts = 3 (Ester et al., 1996). Detected clusters will be persisted to the `case_clusters` and `case_cluster_members` tables along with the originating `detection_runs` row recording the parameters and date range of each run, supporting reproducibility and parameter sensitivity analysis. Cluster results will be surfaced in the H-MAP web dashboard via a dedicated cluster map view that displays each cluster's centroid as a circle scaled by case count, with cross-barangay clusters visually distinguished by outline color. Selecting a cluster expands the view to show the actual radius circle and individual member case coordinates, with member details accessible by clicking each case marker.

### 3.3 NEW SECTION — Address Geocoding Pipeline

**Add this as a new subsection between "System Modules" and "AI Python Machine Learning Microservice"** (around page 40).

> **Address Geocoding Pipeline**
>
> The H-MAP geocoding pipeline converts PIDSR street addresses (the StreetPurok field of the Registry export) to geographic coordinates suitable for spatial cluster detection. The pipeline is implemented in Python (`ml/geocode.py`) and exposed to the Laravel application through a dedicated FastAPI endpoint, with results cached in a dedicated MySQL table to minimize repeated external requests.
>
> *Cascading Query Strategy.* Each address is first parsed into structural components — subdivision, street, and house — using a rule-based parser that recognizes Philippine address conventions including the PUROK and SITIO prefixes, the SUBD./CPD./VILL. abbreviations, and the BLK/LOT/PHASE numbering schemes. The parsed components are then assembled into progressively broader queries and submitted to Nominatim in cascade: (1) subdivision + street within the barangay, (2) street within the barangay, (3) subdivision within the barangay, and (4) barangay centroid as fallback. The cascade stops at the first query that returns a geocode within the Parañaque City bounding box, with the precision tier recorded as the `geocode_source` value (`nominatim_street`, `nominatim_subd`, `nominatim_bgy_centroid`).
>
> *Rate Limiting and Retry.* Nominatim's published usage policy permits one request per second from an identified user agent. The geocoder enforces this limit at the module level (rather than per-cascade) so that consecutive addresses cannot accidentally exceed the rate by chaining multiple cascade calls in quick succession. Responses with HTTP status 429 (rate-limited) are retried with exponential backoff up to three times before being treated as transient errors; transient errors are not cached, so the address is retried fresh on the next encoding session.
>
> *Caching.* Each (street, barangay) pair is normalized to a lowercase, whitespace-collapsed cache key and looked up in the `geocode_cache` table before any external request is issued. Cache hits return instantly; cache misses incur one Nominatim request and are written to the cache regardless of outcome (except for transient errors). The cache persists across ETL re-runs and case-entry sessions, so the full historical backfill of 25,268 dengue cases produced approximately 20,300 unique cache entries that subsequent encoding operations reuse at zero external-request cost.
>
> *Validation Results.* On a stratified sample of 195 dengue addresses spanning all 16 barangays and the years 2018 to 2026, the cascading strategy achieved 72.3 percent usable-precision matches (53.3 percent street-level plus 19.0 percent subdivision-level), with the remaining 27.7 percent falling back to barangay centroid. On the full backfill of 25,268 dengue cases, 16,795 cases (66.5 percent of total, approximately 70 percent of cases with non-blank addresses) reached usable precision; the remaining cases either had no StreetPurok value (approximately 5 percent of total) or resolved only to barangay centroid (approximately 28 percent of total).

### 3.4 AI Python Machine Learning Microservice (p. 40-41)

**Two updates needed.** First, change Flask to FastAPI throughout. Second, add the geocoding endpoint.

**Edit the section opening sentence** ("The AI machine learning component of H-MAP will run as a Flask application..."):

> The AI machine learning and geocoding components of H-MAP will run as a FastAPI application on the same DICT server, listening on internal port 5000 and accessible only through localhost, not exposed to the public internet. FastAPI was selected over the originally proposed Flask framework because its native integration of Pydantic data validation and automatic OpenAPI documentation generation reduces the boilerplate required for typed request and response handling and supports rapid iteration during development. The microservice will provide three endpoints: `/predict/forecast` for Prophet model execution, `/predict/risk` for Random Forest classification, and `/geocode` for address geocoding via the cascading Nominatim pipeline described in the previous section. The Prophet and Random Forest models will be pre-trained and loaded at startup for fast response without retraining on each request.

### 3.5 Development Environment (p. 41-42)

**Edit the Server-Side Technologies list:**

- "Flask 3.x: lightweight Python web framework serving the internal AI prediction API" → **"FastAPI 0.115.x: Python web framework serving the internal AI prediction and geocoding endpoints, with uvicorn as the ASGI server"**
- "PHP 8.x" → **"PHP 8.2+ with the Laravel 11 framework"**

**Add to Client-Side Technologies:**

- **"React 19: component-based frontend framework, replacing direct PHP-templated HTML for the dashboard view, with the Laravel application serving the SPA shell and exposing JSON API endpoints"**
- **"react-leaflet 5.0: React bindings for Leaflet.js, used by both the heat map and cluster detection map views"**

**Add a new bullet:**

- **"OpenStreetMap Nominatim: external HTTP geocoding service, accessed under the OpenStreetMap Foundation's Free Usage Policy with the project identifier `hmap-capstone` as the User-Agent header (https://operations.osmfoundation.org/policies/nominatim/)."**

### 3.6 System Architecture (p. 42-44)

**Edit the Presentation Layer description.** Currently:

> "Presentation Layer. The browser-rendered interface composed of Leaflet.js map panels, Chart.js chart panels, Bootstrap-styled dashboard components, and PHP-generated HTML."

Replace with:

> Presentation Layer. The browser-rendered interface composed of a React 19 single-page application served as a static bundle by the Laravel application, with Leaflet.js (via react-leaflet) map panels, Chart.js (via react-chartjs-2) chart panels, and Tailwind CSS-styled dashboard components. The Laravel application serves the SPA shell on the `/hmap/*` path and the JSON API on the `/api/*` path; all interactive UI state is managed in the browser using React hooks, and surveillance data is loaded via authenticated AJAX requests.

**Edit the Application Logic Layer description.** Currently:

> "...internal cURL calls to the AI Python Flask microservice on localhost:5001."

Replace with:

> ...internal HTTP calls to the FastAPI machine learning and geocoding microservice on localhost:5000, issued via Laravel's `Http` facade. The Laravel application provides all authentication, validation, and authorization at the HTTP boundary; the FastAPI microservice is exposed only on the loopback interface and trusts requests originating from the same host.

### 3.7 Operational Flow (p. 44-45)

**Add new steps to the operational flow** for the new features.

**Edit step (e)** ("For heat map: PHP retrieves geocoded case records...") to clarify that geocoded coordinates now exist at the case level, not just barangay level.

**Add new steps after step (g):**

> h. For case data entry: encoder submits an address; Laravel forwards to FastAPI `/geocode`; FastAPI returns coordinates from the `geocode_cache` table or, on cache miss, executes the Nominatim cascade and writes the result to the cache; coordinates are displayed as a confirmation pin on a Leaflet preview map; the encoder may drag the pin to correct; on case save, the case record is inserted into `cases` and the address into `case_addresses` in the same database transaction.
>
> i. For cluster detection: a scheduled background process (or on-demand Administrator action) runs the DBSCAN cluster detection across all dengue cases of Confirmed or Probable classification with usable-precision geocodes. Detected clusters are persisted to `case_clusters` and `case_cluster_members`; the user-facing cluster dashboard view queries these tables to render the cluster map and alert list.

### 3.8 Database Design (p. 45-49)

**Major changes.** Your Ch.3 currently lists 9 tables (cases, diseases, barangays, thresholds, facilities, user_roles, audit_log, ai_predictions, plus the foreign key diagram). The implemented schema has 14 tables. You need to:

1. Update the **`cases`** description to note that street_purok is no longer part of `cases` (it's in `case_addresses`).
2. Add **five new tables** to the Database Design section.

**Add the following table descriptions and figures (after the existing `ai_predictions` description):**

> **case_addresses:** patient-level street-address and geocoding metadata, structured as a one-to-one extension of the `cases` table with `case_id` serving as both primary key and foreign key. Fields include the raw `street_purok` text as entered by the encoder, the geocoded `case_lat` and `case_lng` coordinates, the `geocode_source` enumeration recording the cascade tier that produced the match (`nominatim_street`, `nominatim_subd`, `nominatim_bgy_centroid`, `manual_pin`, or `failed`), the query string submitted to Nominatim, and the formatted address returned by Nominatim for audit purposes. The separation of address data from the main `cases` table provides a PII isolation boundary consistent with the data minimization principle of Republic Act No. 10173 (2012): access to address-level data can be granted at a different role level than access to aggregate case data.
>
> *Figure 12. PII Isolation Table: case_addresses*

> **geocode_cache:** address-to-coordinate memoization table keyed by the normalized (lowercase, whitespace-collapsed) combination of street address and barangay name. Holds the geocode result, source tier, and timestamp. The cache persists across schema reloads (the table uses `CREATE TABLE IF NOT EXISTS` rather than `DROP TABLE`), allowing a one-time historical backfill of approximately 20,300 unique addresses to be reused indefinitely. This design respects Nominatim's published usage policy of one request per second by ensuring that no address is queried more than once.
>
> *Figure 13. Cache Table: geocode_cache*

> **detection_runs:** one row per invocation of the cluster detection process, recording the disease code, DBSCAN parameters (eps in meters, minPts, window weeks), the date range scanned, the number of cases evaluated, the number of clusters detected, and the run timestamp. This table supports reproducibility of cluster detection results across different parameter choices and is the parent table referenced by all clusters detected in a given run.
>
> *Figure 14. Cluster Detection: detection_runs*

> **case_clusters:** one row per detected cluster, referencing the originating `detection_runs` row and recording the cluster's window start and end dates, centroid latitude and longitude, member case count, maximum radius (distance from the centroid to the farthest member), and a comma-joined list of barangay names that the cluster spans. The table holds a SHA-1 `fingerprint` of the sorted member case IDs that serves as a deduplication key across the overlapping rolling windows of the sliding-window detection strategy.
>
> *Figure 15. Cluster Detection: case_clusters*

> **case_cluster_members:** many-to-many junction table linking each `case_clusters` row to the member case IDs from the `cases` table. A single case may participate in multiple clusters across different detection runs but appears exactly once per cluster.
>
> *Figure 16. Cluster Detection: case_cluster_members*

**Update the foreign-key relationships paragraph** (currently page 49-50) to mention the new tables:

Add a sentence at the end:

> The `case_addresses` table holds a one-to-one foreign key to the `cases` table on `case_id` with CASCADE delete to ensure the address row is removed when its parent case is removed. The `case_clusters` table holds a foreign key to `detection_runs` with CASCADE delete, so deleting a detection run removes its detected clusters atomically. The `case_cluster_members` table holds foreign keys to both `case_clusters` and `cases`, with CASCADE delete on each so cluster membership records cannot outlive either parent. The `geocode_cache` table has no foreign keys: it is a pure memoization table that may be truncated and rebuilt at any time without affecting referential integrity.

### 3.9 Security Considerations (p. 54-55)

**Edit one item and add one new item.**

**Edit item (f) "Data Minimization in Display":** Currently states the dashboard operates on aggregated barangay-level counts. With the cluster detection module, this is no longer fully accurate. Replace with:

> f. Data Minimization in Display: heat map and trend dashboard visualizations will operate on aggregated, barangay-level case counts without exposing individual patient identifiers. Cluster detection visualizations will display individual case coordinates on the map as anonymous dots; the underlying case identifier, address text, and demographic details are made available only on explicit selection of a cluster and only to users with the Health Analyst or Administrator role. Patient names and other directly identifying fields are never exposed through the cluster detection interface. This tiered disclosure design is consistent with the data minimization principle under Republic Act No. 10173 (2012) and National Privacy Commission (n.d.) guidelines for processing personal health information.

**Add a new item (g):**

> g. Address-Level PII Isolation: the patient street-address column is stored in a dedicated `case_addresses` table, separate from the main `cases` transaction table, with a strict one-to-one foreign-key relationship. This structural separation enables future access-control policies to restrict address-level reads to roles with documented public health necessity (such as field investigation officers) while leaving aggregate surveillance access (heat maps, threshold alerts, forecasts) available to broader user roles, consistent with the data minimization principle of Republic Act No. 10173 (2012).

### 3.10 References

Add the two new references from §2.2 above (Ester et al. 1996, Harrington et al. 2005). Their full citations are provided in §2.2 of this revision document.

---

## SUMMARY OF NEW REFERENCES TO ADD

```
Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm
   for discovering clusters in large spatial databases with noise. In Proceedings of
   the Second International Conference on Knowledge Discovery and Data Mining
   (KDD-96), 226–231. AAAI Press.

Harrington, L. C., Scott, T. W., Lerdthusnee, K., Coleman, R. C., Costero, A.,
   Clark, G. G., Jones, J. J., Kitthawee, S., Kittayapong, P., Sithiprasasna, R.,
   & Edman, J. D. (2005). Dispersal of the dengue vector Aedes aegypti within and
   between rural communities. The American Journal of Tropical Medicine and
   Hygiene, 72(2), 209–220. https://doi.org/10.4269/ajtmh.2005.72.209
```

---

## SUMMARY OF FIGURES TO UPDATE

| Figure | Current | Action |
|---|---|---|
| Figure 1 (Conceptual Framework / IPO) | exists | Add cluster detection + geocoding inputs |
| Figure 2 (System Architecture) | exists | Add geocoding service + cluster job |
| Figure 3 (cases) | exists | No change (note in caption that address moved out) |
| Figure 11 (ER diagram) | exists | **Add 5 new tables + their relationships** |
| Figure 12-16 | new | Add per the table descriptions above |

---

## CHANGES NOT REQUIRED

The following parts of Ch.1-3 remain valid as written and do **not** need revision:

- ISO/IEC 25010 evaluation framework (Ch.3 §Evaluation Model)
- Statistical treatment (5-point Likert, weighted mean) (Ch.3 §Data Processing)
- HRMO authentication design (Ch.3 §HRMO Portal Authentication)
- Three-role RBAC (Encoder / Analyst / Administrator)
- WHO EWARN threshold methodology (Ch.2 §Epidemic Threshold Methods, Ch.3 §Module 3)
- Prophet model description (Ch.2 §Machine Learning for Disease Forecasting)
- Random Forest model description (Ch.2 §Machine Learning for Barangay Risk Classification)
- Research design (Applied Developmental Research) and Agile-Iterative methodology
- Significance to CESU, residents, and the IT research literature (Ch.1 §Significance) — your additions strengthen rather than replace these
- All existing references already cited

---

## RECOMMENDED ORDER OF EDITS

1. **First pass — Ch.1 objectives and scope (highest priority).** The new "objective d" (cluster detection) sets the entire frame for the rest of the document. Get this right first.
2. **Ch.1 background paragraph** about CESU's manual workflow pain point. This is the motivation.
3. **Ch.2 new DBSCAN/Aedes literature subsection.** This is the conceptual foundation citations.
4. **Ch.2 geocoding subsection.** Smaller addition.
5. **Ch.3 Module 6** description.
6. **Ch.3 Address Geocoding Pipeline** subsection.
7. **Ch.3 Database Design** — five new table descriptions and figure references.
8. **Ch.3 housekeeping** — Flask → FastAPI, PHP → Laravel, etc.
9. **References** — add the two new citations.
10. **Figures** — update Figure 1 (IPO), Figure 2 (architecture), Figure 11 (ER), add Figures 12-16.

Estimated total writing time: **roughly 6-10 hours** if you write directly from this list, longer if you also need to redraw figures. The Methods chapter changes are the largest in word count but the most mechanical; the conceptual framework additions in Ch.2 require the most careful prose.
