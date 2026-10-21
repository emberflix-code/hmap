-- Removes patient names that the May 2026 demo dump copied into the staging
-- (anonymized) database. Run ONLY against hmap_db_demo, never against hmap_db.
--
--   mysql -u hris -p -h 127.0.0.1 --protocol=TCP < 2026_10_21_scrub_demo_patient_names.sql
--
-- Background: ml/anonymize_for_demo.py copied excluded_cases verbatim, but
-- excluded_cases.raw_full_name holds the patient's full name from the PIDSR
-- registry. The script now nulls that column; this statement fixes the copy
-- that is already loaded on the staging server.

USE hmap_db_demo;

UPDATE excluded_cases SET raw_full_name = NULL WHERE raw_full_name IS NOT NULL;

-- Verify: both counts must be 0.
SELECT COUNT(*) AS names_remaining FROM excluded_cases WHERE raw_full_name IS NOT NULL;
SELECT COUNT(*) AS names_in_cases_table
  FROM information_schema.columns
 WHERE table_schema = 'hmap_db_demo' AND column_name LIKE '%name%' AND table_name = 'cases';
