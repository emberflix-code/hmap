-- targets: hmap_db, hmap_db_demo
--
-- Authenticator-app enrollment per CESU staff member (Ch.3 Module 9,
-- Security a). Written by laravel/app/Services/Mfa.php.
--
--   python ml/run_migrations.py --db hmap_db

CREATE TABLE IF NOT EXISTS user_mfa (
    employee_id     INT UNSIGNED NOT NULL,
    secret_enc      TEXT NOT NULL,
    confirmed_at    DATETIME NULL,
    last_used_step  BIGINT UNSIGNED NULL,
    recovery_codes  JSON NULL,
    created_at      DATETIME NOT NULL,
    PRIMARY KEY (employee_id)
) ENGINE=InnoDB;
