-- targets: hmap_db, hmap_db_demo
--
-- Display name on the CESU staff authorization list, so the Administrator's
-- staff panel shows who each employee ID is. The HRMO employee directory is
-- in a separate database; the name is filled in from HRMO at each sign-in
-- (AuthController) or typed by the Administrator when adding someone.
--
--   python ml/run_migrations.py --db hmap_db

ALTER TABLE user_roles
    ADD COLUMN full_name VARCHAR(120) NULL AFTER employee_id;
