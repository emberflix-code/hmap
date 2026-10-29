-- targets: hmap_db, hmap_db_demo
--
-- Outbreak alerts and notifications (Ch.3 Module 7), written by
-- laravel/app/Services/Notifier.php (php artisan hmap:notify).
--
--   python ml/run_migrations.py --db hmap_db
--
-- notifications holds one row per (disease, barangay, alert type, morbidity
-- week): the unique key is the de-duplication rule. Messages carry no patient
-- identifiers. notification_deliveries records every attempt per recipient
-- and channel with its status.

CREATE TABLE IF NOT EXISTS notification_recipients (
    recipient_id   INT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_name      VARCHAR(120) NOT NULL,
    position       VARCHAR(120) NULL,
    email          VARCHAR(190) NULL,
    mobile         VARCHAR(20)  NULL,
    via_email      TINYINT(1) NOT NULL DEFAULT 1,
    via_sms        TINYINT(1) NOT NULL DEFAULT 0,
    is_active      TINYINT(1) NOT NULL DEFAULT 1,
    updated_by     INT UNSIGNED NULL,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipient_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notifications (
    notification_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id       INT UNSIGNED NOT NULL,
    barangay_id      INT UNSIGNED NOT NULL,
    morbidity_year   SMALLINT UNSIGNED NOT NULL,
    morbidity_week   TINYINT UNSIGNED NOT NULL,
    alert_type       ENUM('epidemic_threshold','single_case','hotspot') NOT NULL,
    case_count       INT UNSIGNED NOT NULL,
    threshold_value  DECIMAL(8,2) NULL,
    subject          VARCHAR(200) NOT NULL,
    message          VARCHAR(480) NOT NULL,
    created_at       DATETIME NOT NULL,
    PRIMARY KEY (notification_id),
    UNIQUE KEY uq_notification (disease_id, barangay_id, alert_type, morbidity_year, morbidity_week),
    INDEX idx_notification_created (created_at),
    CONSTRAINT fk_notif_disease FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_notif_barangay FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notification_deliveries (
    delivery_id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    notification_id  INT UNSIGNED NOT NULL,
    recipient_id     INT UNSIGNED NOT NULL,
    channel          ENUM('email','sms') NOT NULL,
    status           ENUM('pending','sent','failed','skipped') NOT NULL DEFAULT 'pending',
    attempts         TINYINT UNSIGNED NOT NULL DEFAULT 0,
    error            VARCHAR(500) NULL,
    sent_at          DATETIME NULL,
    PRIMARY KEY (delivery_id),
    UNIQUE KEY uq_delivery (notification_id, recipient_id, channel),
    INDEX idx_delivery_status (status),
    CONSTRAINT fk_delivery_notification FOREIGN KEY (notification_id) REFERENCES notifications(notification_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_delivery_recipient FOREIGN KEY (recipient_id) REFERENCES notification_recipients(recipient_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;
