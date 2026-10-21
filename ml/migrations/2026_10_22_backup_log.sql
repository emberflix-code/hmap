-- targets: hmap_db, hmap_db_demo
--
-- Backup register for ml/backup_db.py (Ch.3 Module 9 and Database Design).
--
--   python ml/run_migrations.py --db hmap_db

CREATE TABLE IF NOT EXISTS backup_log (
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
