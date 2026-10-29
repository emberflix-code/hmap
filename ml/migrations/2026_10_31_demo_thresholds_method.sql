-- targets: hmap_db_demo
--
-- The demo database's thresholds table predates the multi-method schema
-- (no `method` column), so GET /api/thresholds failed with "Unknown column
-- t.method" and the dashboard trend chart showed an error. The table holds
-- only computed values, so it is recreated in its current form and refilled
-- right after with:
--
--   python ml/run_migrations.py --db hmap_db_demo
--   python ml/compute_thresholds.py --alert-year 2026      (ml/.env points at hmap_db_demo)
--
-- Demo only: the target line keeps it away from hmap_db. Check hmap_db with
-- SHOW COLUMNS FROM thresholds LIKE 'method' before deploying production.

DROP TABLE IF EXISTS thresholds;

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
