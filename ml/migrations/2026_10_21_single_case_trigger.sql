-- Adds the PIDSR single-case trigger flag to diseases (Ch.3 Module 3).
-- Run once against each database: hmap_db (production) and hmap_db_demo (staging).
--
--   mysql -u hris -p -h 127.0.0.1 --protocol=TCP hmap_db      < 2026_10_21_single_case_trigger.sql
--   mysql -u hris -p -h 127.0.0.1 --protocol=TCP hmap_db_demo < 2026_10_21_single_case_trigger.sql
--
-- The PIDSR Manual of Procedures (DOH, 2014, p. 58, Table 5) treats a single
-- case of measles or acute flaccid paralysis as an alert. Other Table 5
-- diseases are enabled only after CESU confirms the table.

ALTER TABLE diseases
    ADD COLUMN single_case_trigger TINYINT(1) NOT NULL DEFAULT 0 AFTER forecast_enabled;

UPDATE diseases SET single_case_trigger = 1 WHERE disease_code IN ('MEA', 'AFP');

SELECT disease_code, disease_name, single_case_trigger
  FROM diseases WHERE single_case_trigger = 1;
