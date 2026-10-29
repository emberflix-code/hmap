-- targets: hmap_db, hmap_db_demo
--
-- Email (SMTP) and SMS (Paranaque SMS API) settings that the CESU
-- Administrator maintains from the dashboard (Reports > Email and SMS
-- settings), following the HRIS Portal's module_smtp_config /
-- module_sms_config design. Written by laravel/app/Services/ChannelSettings.php.
--
--   python ml/run_migrations.py --db hmap_db
--
-- settings_enc is the whole settings object (host, port, user, password or
-- client id and secret, ...) encrypted with the Laravel APP_KEY, so the
-- database alone never reveals the SMTP password or SMS client secret.

CREATE TABLE IF NOT EXISTS channel_settings (
    channel       ENUM('email','sms') NOT NULL,
    settings_enc  TEXT NOT NULL,
    is_active     TINYINT(1) NOT NULL DEFAULT 0,
    updated_by    INT UNSIGNED NULL,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel)
) ENGINE=InnoDB;
