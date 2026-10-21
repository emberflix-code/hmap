-- targets: hmap_db_demo
--
-- Removes patient names that the May 2026 demo dump copied into the staging
-- (anonymized) database. Demo only: the target line above stops
-- ml/run_migrations.py from ever running it against hmap_db.
--
--   python ml/run_migrations.py --db hmap_db_demo
--
-- Background: ml/anonymize_for_demo.py copied excluded_cases verbatim, but
-- excluded_cases.raw_full_name holds the patient's full name from the PIDSR
-- registry. The script now nulls that column; this statement fixes the copy
-- that is already loaded on the staging server.

UPDATE excluded_cases SET raw_full_name = NULL WHERE raw_full_name IS NOT NULL;

-- Verify: must print 0.
SELECT COUNT(*) AS names_remaining FROM excluded_cases WHERE raw_full_name IS NOT NULL;
