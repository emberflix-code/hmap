-- targets: hmap_db, hmap_db_demo
--
-- The weekly dengue memo template, editable by the Administrator (Weekly
-- Report > Memo draft > Edit template), so recipients, signatory and wording
-- can change without a code change. No row = the built-in default in
-- laravel/app/Services/MemoTemplate.php.
--
--   python ml/run_migrations.py --db hmap_db

CREATE TABLE IF NOT EXISTS memo_templates (
    template_key  VARCHAR(40) NOT NULL,
    body          TEXT NOT NULL,
    updated_by    INT UNSIGNED NULL,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (template_key)
) ENGINE=InnoDB;
