-- H-MAP database schema (hmap_db)
-- Mirrors the table specifications in Ch.3 Figures 3–10 of HMAP_Chapters_1to3_Final.pdf.
-- Run order matters: reference tables before transaction tables before audit tables.
--
-- Cross-schema references to the HRMO employee table are LOGICAL only (no FK constraint)
-- per Ch.3, because the HRMO portal lives in a separate database.

CREATE DATABASE IF NOT EXISTS hmap_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hmap_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS backup_log;
DROP TABLE IF EXISTS excluded_cases;
DROP TABLE IF EXISTS ai_predictions;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS recommendation_rules;
DROP TABLE IF EXISTS user_mfa;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS thresholds;
DROP TABLE IF EXISTS case_cluster_members;
DROP TABLE IF EXISTS case_clusters;
DROP TABLE IF EXISTS detection_runs;
DROP TABLE IF EXISTS case_addresses;
DROP TABLE IF EXISTS cases;
DROP TABLE IF EXISTS facilities;
DROP TABLE IF EXISTS barangays;
DROP TABLE IF EXISTS diseases;
-- geocode_cache is INTENTIONALLY not dropped: it's the address→coordinate
-- memo that lets ETL re-runs avoid re-geocoding the same addresses (each
-- Nominatim call is rate-limited to 1/sec, so a full backfill is hours).
-- The cache survives schema reloads; only its `cached_at` ages.
SET FOREIGN_KEY_CHECKS = 1;

-- ─── Reference: diseases ──────────────────────────────────────────────────
CREATE TABLE diseases (
    disease_id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_code      VARCHAR(20)  NOT NULL,
    disease_name      VARCHAR(100) NOT NULL,
    disease_category  ENUM('Category 1','Category 2') NOT NULL,
    alert_enabled     TINYINT(1)   NOT NULL DEFAULT 1,
    forecast_enabled  TINYINT(1)   NOT NULL DEFAULT 0,
    -- 1 = a single case raises an alert (PIDSR MOP 2014, p. 58, Table 5),
    -- instead of the mean + 1/2 SD thresholds used for other diseases
    single_case_trigger TINYINT(1) NOT NULL DEFAULT 0,
    display_order     TINYINT UNSIGNED NULL,
    PRIMARY KEY (disease_id),
    UNIQUE KEY uq_disease_code (disease_code),
    INDEX idx_disease_name (disease_name)
) ENGINE=InnoDB;

-- ─── Reference: barangays ─────────────────────────────────────────────────
CREATE TABLE barangays (
    barangay_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    barangay_name  VARCHAR(80)  NOT NULL,
    population     INT UNSIGNED NULL,
    centroid_lat   DECIMAL(9,6) NULL,
    centroid_lng   DECIMAL(9,6) NULL,
    geojson_id     VARCHAR(40)  NULL,
    district       TINYINT UNSIGNED NULL,
    PRIMARY KEY (barangay_id),
    UNIQUE KEY uq_barangay_name (barangay_name)
) ENGINE=InnoDB;

-- ─── Reference: facilities ────────────────────────────────────────────────
CREATE TABLE facilities (
    facility_id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
    facility_name  VARCHAR(120) NOT NULL,
    facility_type  ENUM('Health Center','Sentinel Site','Hospital','Other') NOT NULL DEFAULT 'Other',
    barangay_id    INT UNSIGNED NULL,
    is_sentinel    TINYINT(1)   NOT NULL DEFAULT 0,
    facility_lat   DECIMAL(9,6) NULL,
    facility_lng   DECIMAL(9,6) NULL,
    PRIMARY KEY (facility_id),
    UNIQUE KEY uq_facility_name (facility_name),
    CONSTRAINT fk_facilities_barangay
        FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Transaction: cases (PIDSR line list) ────────────────────────────────
CREATE TABLE cases (
    case_id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id           INT UNSIGNED NOT NULL,
    case_classification  ENUM('Suspect','Probable','Confirmed','Discarded','Negative','Compatible','Pending') NOT NULL DEFAULT 'Pending',
    date_onset           DATE NULL,
    date_admitted        DATE NULL,
    date_reported        DATE NULL,
    barangay_id          INT UNSIGNED NULL,
    facility_id          INT UNSIGNED NULL,
    age                  TINYINT UNSIGNED NULL,
    age_group            ENUM('0-4','5-9','10-14','15-19','20-59','60+') NULL,
    sex                  ENUM('Male','Female','Unknown') NULL,
    outcome              ENUM('Alive','Died','Unknown') NULL,
    morbidity_week       TINYINT UNSIGNED NOT NULL,
    morbidity_month      TINYINT UNSIGNED NULL,
    morbidity_year       YEAR NOT NULL,
    entered_by           INT UNSIGNED NULL,
    entered_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    status_flag          ENUM('Active','Deleted') NOT NULL DEFAULT 'Active',
    PRIMARY KEY (case_id),
    INDEX idx_cases_disease_week (disease_id, morbidity_year, morbidity_week),
    INDEX idx_cases_barangay_week (barangay_id, morbidity_year, morbidity_week),
    INDEX idx_cases_year (morbidity_year),
    CONSTRAINT fk_cases_disease
        FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_cases_barangay
        FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_cases_facility
        FOREIGN KEY (facility_id) REFERENCES facilities(facility_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── PII: case_addresses (separated from cases for access control) ──────
-- Patient street addresses + geocoded coordinates. Split out from `cases`
-- so the address column can have its own RA 10173 access policy (only
-- Analysts/Administrators read it; Encoders write their own entries via
-- the Laravel UI and never read others'). The 1:1 relationship is enforced
-- by case_id being both PK and FK.
--
-- Geocoding source is recorded per row so cluster detection can filter:
--   nominatim_street       — street-level OSM match, usable for 200m clusters
--   nominatim_subd         — subdivision-level match, usable for 200m clusters
--   nominatim_bgy_centroid — fallthrough to barangay centroid; NOT usable
--   manual_pin             — encoder dropped a pin on the map (high trust)
--   failed                 — no geocode at all; address stored without coords
CREATE TABLE case_addresses (
    case_id           INT UNSIGNED NOT NULL,
    raw_street_purok  VARCHAR(255) NULL,
    case_lat          DECIMAL(9,6) NULL,
    case_lng          DECIMAL(9,6) NULL,
    geocode_source    ENUM(
        'nominatim_street',
        'nominatim_subd',
        'nominatim_bgy_centroid',
        'manual_pin',
        'failed'
    ) NOT NULL,
    geocode_query     VARCHAR(255) NULL,
    geocode_formatted VARCHAR(255) NULL,
    geocoded_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (case_id),
    INDEX idx_geocode_source (geocode_source),
    INDEX idx_latlng (case_lat, case_lng),
    CONSTRAINT fk_addr_case
        FOREIGN KEY (case_id) REFERENCES cases(case_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Cluster detection: detection_runs ──────────────────────────────────
-- One row per ml/detect_clusters.py invocation. Stores parameters and
-- summary stats so a thesis chapter (or Laravel admin panel) can compare
-- detection runs with different params and reproduce a specific result.
CREATE TABLE detection_runs (
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
) ENGINE=InnoDB;

-- ─── Cluster detection: case_clusters ────────────────────────────────────
-- One row per detected cluster. A cluster is uniquely defined by its set of
-- member case_ids (see fingerprint), so we dedupe across overlapping rolling
-- windows by checking the fingerprint before inserting. window_start/end are
-- the EARLIEST window where this cluster first appeared.
--
-- centroid_lat/lng is the mean of member coordinates; radius_m is the max
-- distance from centroid to any member (a quick "tightness" stat that's
-- always ≤ eps for DBSCAN-found clusters).
CREATE TABLE case_clusters (
    cluster_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    detection_run_id   INT UNSIGNED NOT NULL,
    fingerprint        CHAR(40) NOT NULL,    -- SHA1 of sorted member case_ids
    window_start       DATE NOT NULL,
    window_end         DATE NOT NULL,
    centroid_lat       DECIMAL(9,6) NOT NULL,
    centroid_lng       DECIMAL(9,6) NOT NULL,
    case_count         SMALLINT UNSIGNED NOT NULL,
    radius_m           DECIMAL(8,2) NOT NULL,
    barangays_involved VARCHAR(255) NULL,    -- comma-joined names, for quick display
    PRIMARY KEY (cluster_id),
    UNIQUE KEY uq_cluster_fingerprint (detection_run_id, fingerprint),
    INDEX idx_cluster_window (window_start, window_end),
    INDEX idx_cluster_run (detection_run_id),
    CONSTRAINT fk_cluster_run
        FOREIGN KEY (detection_run_id) REFERENCES detection_runs(detection_run_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Cluster detection: case_cluster_members (M:N junction) ─────────────
CREATE TABLE case_cluster_members (
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
) ENGINE=InnoDB;

-- ─── Cache: geocode_cache (survives schema reloads) ──────────────────────
-- Address-string → (lat, lng, source) memo. Keyed on the normalized cascade
-- key (lowercase, mojibake-fixed, whitespace-collapsed StreetPurok + barangay)
-- so the same address can never round-trip to Nominatim twice. Nominatim's
-- 1 req/sec policy makes this cache load-bearing for ETL turnaround.
CREATE TABLE IF NOT EXISTS geocode_cache (
    cache_key         VARCHAR(255) NOT NULL,
    lat               DECIMAL(9,6) NULL,
    lng               DECIMAL(9,6) NULL,
    geocode_source    ENUM(
        'nominatim_street',
        'nominatim_subd',
        'nominatim_bgy_centroid',
        'manual_pin',
        'failed'
    ) NOT NULL,
    geocode_query     VARCHAR(255) NULL,
    formatted         VARCHAR(255) NULL,
    cached_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cache_key),
    INDEX idx_cache_source (geocode_source)
) ENGINE=InnoDB;

-- ─── Reference: thresholds (multi-method, pre-computed) ──────────────────
-- Each (disease × morbidity_week) gets one row per `method`:
--   ewarn_mu2sigma  — WHO EWARN: μ+2σ over 5 prior years' weekly counts,
--                    counting only Confirmed+Probable classifications.
--                    This is H-MAP's active alert threshold.
--   cesu_mean       — Simple 5-year mean of weekly counts, counting ALL
--                    classifications (matches CESU's 5YrAve sheet "Average"
--                    column; this is what CESU's existing memo template uses).
--   cesu_median     — Same as cesu_mean but median (matches 5YrAve "Median").
-- Storing all three side-by-side lets the dashboard show H-MAP's μ+2σ alert
-- next to CESU's existing reference values, and lets Ch.4 evaluate where
-- the two methods disagree.
CREATE TABLE thresholds (
    threshold_id     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id       INT UNSIGNED NOT NULL,
    morbidity_week   TINYINT UNSIGNED NOT NULL,
    method           ENUM('ewarn_mu2sigma','cesu_mean','cesu_median') NOT NULL,
    baseline_years   VARCHAR(30) NOT NULL,
    mean_cases       DECIMAL(8,4) NOT NULL,
    std_dev          DECIMAL(8,4) NOT NULL,
    threshold_value  DECIMAL(8,4) NOT NULL,
    last_updated     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (threshold_id),
    UNIQUE KEY uq_disease_week_method (disease_id, morbidity_week, method),
    CONSTRAINT fk_thresholds_disease
        FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Decision support: recommendation_rules, recommendations (Module 6) ──
-- The draft rule set is seeded by ml/migrations/2026_10_30_recommendations.sql.
-- Rules for 'Moderate' apply to Moderate and High barangays; 'High' rules
-- only to High. disease_id NULL = fallback for diseases without rules.
CREATE TABLE recommendation_rules (
    rule_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id       INT UNSIGNED NULL,
    risk_tier        ENUM('Moderate','High') NOT NULL,
    category         ENUM('Team','Supply','Medicine','IEC') NOT NULL,
    item             VARCHAR(200) NOT NULL,
    scaling_basis    ENUM('fixed','per_case','per_1000_pop','as_assessed') NOT NULL,
    quantity_factor  DECIMAL(8,2) NULL,
    unit             VARCHAR(40) NULL,
    priority         TINYINT UNSIGNED NOT NULL DEFAULT 50,
    source           VARCHAR(255) NOT NULL,
    notes            VARCHAR(500) NULL,
    status           ENUM('Draft','Validated') NOT NULL DEFAULT 'Draft',
    validated_by     INT UNSIGNED NULL,
    validated_at     DATETIME NULL,
    is_active        TINYINT(1) NOT NULL DEFAULT 1,
    updated_by       INT UNSIGNED NULL,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (rule_id),
    INDEX idx_rule_lookup (disease_id, risk_tier, is_active),
    CONSTRAINT fk_rule_disease FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE recommendations (
    recommendation_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id         INT UNSIGNED NOT NULL,
    barangay_id        INT UNSIGNED NOT NULL,
    morbidity_year     SMALLINT UNSIGNED NOT NULL,
    morbidity_week     TINYINT UNSIGNED NOT NULL,
    rule_id            INT UNSIGNED NOT NULL,
    risk_tier          ENUM('Moderate','High') NOT NULL,
    barangay_rank      SMALLINT UNSIGNED NOT NULL,
    active_cases       INT UNSIGNED NOT NULL,
    category           ENUM('Team','Supply','Medicine','IEC') NOT NULL,
    item               VARCHAR(200) NOT NULL,
    quantity           INT UNSIGNED NULL,
    unit               VARCHAR(40) NULL,
    rule_status        ENUM('Draft','Validated') NOT NULL,
    generated_at       DATETIME NOT NULL,
    action_status      ENUM('Pending','Acted','Not acted') NOT NULL DEFAULT 'Pending',
    action_note        VARCHAR(500) NULL,
    action_by          INT UNSIGNED NULL,
    action_at          DATETIME NULL,
    PRIMARY KEY (recommendation_id),
    UNIQUE KEY uq_rec (disease_id, barangay_id, morbidity_year, morbidity_week, rule_id),
    INDEX idx_rec_week (disease_id, morbidity_year, morbidity_week),
    CONSTRAINT fk_rec_disease FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rec_barangay FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rec_rule FOREIGN KEY (rule_id) REFERENCES recommendation_rules(rule_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Access control: user_roles (logical FK to HRMO db) ──────────────────
CREATE TABLE user_roles (
    role_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    employee_id  INT UNSIGNED NOT NULL,
    role         ENUM('Encoder','Analyst','Administrator') NOT NULL,
    assigned_by  INT UNSIGNED NULL,
    assigned_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active    TINYINT(1)   NOT NULL DEFAULT 1,
    PRIMARY KEY (role_id),
    UNIQUE KEY uq_employee (employee_id),
    INDEX idx_role (role)
) ENGINE=InnoDB;

-- ─── Access control: user_mfa (authenticator enrollment) ─────────────────
-- secret_enc is encrypted with the Laravel APP_KEY; recovery_codes holds
-- SHA-256 hashes only. last_used_step stops a code being used twice.
CREATE TABLE user_mfa (
    employee_id     INT UNSIGNED NOT NULL,
    secret_enc      TEXT NOT NULL,
    confirmed_at    DATETIME NULL,
    last_used_step  BIGINT UNSIGNED NULL,
    recovery_codes  JSON NULL,
    created_at      DATETIME NOT NULL,
    PRIMARY KEY (employee_id)
) ENGINE=InnoDB;

-- ─── Audit: complete user action log (RA 10173) ──────────────────────────
CREATE TABLE audit_log (
    log_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    employee_id   INT UNSIGNED NOT NULL,
    action_type   VARCHAR(30) NOT NULL,
    target_table  VARCHAR(40) NULL,
    target_id     INT UNSIGNED NULL,
    old_values    JSON NULL,
    new_values    JSON NULL,
    ip_address    VARCHAR(45) NULL,
    action_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    INDEX idx_employee (employee_id),
    INDEX idx_action_at (action_at)
) ENGINE=InnoDB;

-- ─── AI output cache: ai_predictions ─────────────────────────────────────
CREATE TABLE ai_predictions (
    prediction_id       INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id          INT UNSIGNED NOT NULL,
    prediction_type     ENUM('Prophet_Forecast','RF_Risk') NOT NULL,
    generated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    forecast_week_start DATE NULL,
    predicted_cases     DECIMAL(8,2) NULL,
    confidence_lower    DECIMAL(8,2) NULL,
    confidence_upper    DECIMAL(8,2) NULL,
    barangay_id         INT UNSIGNED NULL,
    risk_level          ENUM('Low','Moderate','High','Critical') NULL,
    requested_by        INT UNSIGNED NULL,
    PRIMARY KEY (prediction_id),
    INDEX idx_disease_generated (disease_id, generated_at),
    CONSTRAINT fk_aipred_disease
        FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_aipred_barangay
        FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Audit: excluded_cases (rows rejected during ETL) ────────────────────
-- Not in Ch.3 figures but required by docs/data_mappings.md so the thesis
-- can defend exactly how many rows were dropped and why.
CREATE TABLE excluded_cases (
    excluded_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    raw_disease          VARCHAR(120) NULL,
    raw_barangay         VARCHAR(120) NULL,
    raw_caseclass        VARCHAR(120) NULL,
    raw_year             SMALLINT UNSIGNED NULL,
    raw_morbidity_week   TINYINT UNSIGNED NULL,
    raw_full_name        VARCHAR(200) NULL,
    exclusion_reason     ENUM('out_of_city','unknown_barangay','invalid_data') NOT NULL,
    exclusion_notes      VARCHAR(255) NULL,
    excluded_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (excluded_id),
    INDEX idx_reason (exclusion_reason)
) ENGINE=InnoDB;

-- ─── Operations: backup_log (ml/backup_db.py) ────────────────────────────
-- One row per encrypted backup: checksum, per-table row counts, and the
-- result of the latest test restoration. Rows outlive pruned files.
CREATE TABLE backup_log (
    backup_id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    started_at        DATETIME NOT NULL,
    finished_at       DATETIME NULL,
    file_name         VARCHAR(190) NOT NULL,
    file_size_bytes   BIGINT UNSIGNED NULL,
    sha256            CHAR(64) NULL,
    table_row_counts  JSON NULL,
    status            ENUM('running','success','failed') NOT NULL,
    error             TEXT NULL,
    verified_at       DATETIME NULL,
    verify_status     ENUM('passed','failed') NULL,
    verify_detail     TEXT NULL,
    deleted_at        DATETIME NULL,
    PRIMARY KEY (backup_id),
    INDEX idx_backup_started (started_at)
) ENGINE=InnoDB;
