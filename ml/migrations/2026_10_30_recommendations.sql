-- targets: hmap_db, hmap_db_demo
--
-- Resource allocation recommender (Ch.3 Module 6): the Administrator-
-- maintained rule table and the recommendations generated from it, with the
-- action the Health Analyst records for each one.
--
--   python ml/run_migrations.py --db hmap_db
--
-- The seeded rules are a DRAFT encoded from DOH and WHO guidance. Every rule
-- starts with status 'Draft' and must be validated (or edited) by CESU before
-- it is presented as CESU protocol. Rules apply cumulatively: 'Moderate'
-- rules apply to Moderate and High barangays, 'High' rules only to High.
-- Rules with no disease apply to any disease that has no rules of its own.

CREATE TABLE IF NOT EXISTS recommendation_rules (
    rule_id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id       INT UNSIGNED NULL,
    risk_tier        ENUM('Moderate','High') NOT NULL,
    category         ENUM('Team','Supply','Medicine','IEC') NOT NULL,
    item             VARCHAR(200) NOT NULL,
    scaling_basis    ENUM('fixed','per_case','per_1000_pop','as_assessed') NOT NULL,
    quantity_factor  DECIMAL(8,2) NULL,
    unit             VARCHAR(40) NULL,
    priority         TINYINT UNSIGNED NOT NULL DEFAULT 50,
    source           VARCHAR(255) NOT NULL,
    notes            VARCHAR(500) NULL,
    status           ENUM('Draft','Validated') NOT NULL DEFAULT 'Draft',
    validated_by     INT UNSIGNED NULL,
    validated_at     DATETIME NULL,
    is_active        TINYINT(1) NOT NULL DEFAULT 1,
    updated_by       INT UNSIGNED NULL,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (rule_id),
    INDEX idx_rule_lookup (disease_id, risk_tier, is_active),
    CONSTRAINT fk_rule_disease FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    disease_id         INT UNSIGNED NOT NULL,
    barangay_id        INT UNSIGNED NOT NULL,
    morbidity_year     SMALLINT UNSIGNED NOT NULL,
    morbidity_week     TINYINT UNSIGNED NOT NULL,
    rule_id            INT UNSIGNED NOT NULL,
    risk_tier          ENUM('Moderate','High') NOT NULL,
    barangay_rank      SMALLINT UNSIGNED NOT NULL,
    active_cases       INT UNSIGNED NOT NULL,
    category           ENUM('Team','Supply','Medicine','IEC') NOT NULL,
    item               VARCHAR(200) NOT NULL,
    quantity           INT UNSIGNED NULL,
    unit               VARCHAR(40) NULL,
    rule_status        ENUM('Draft','Validated') NOT NULL,
    generated_at       DATETIME NOT NULL,
    action_status      ENUM('Pending','Acted','Not acted') NOT NULL DEFAULT 'Pending',
    action_note        VARCHAR(500) NULL,
    action_by          INT UNSIGNED NULL,
    action_at          DATETIME NULL,
    PRIMARY KEY (recommendation_id),
    UNIQUE KEY uq_rec (disease_id, barangay_id, morbidity_year, morbidity_week, rule_id),
    INDEX idx_rec_week (disease_id, morbidity_year, morbidity_week),
    CONSTRAINT fk_rec_disease FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rec_barangay FOREIGN KEY (barangay_id) REFERENCES barangays(barangay_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_rec_rule FOREIGN KEY (rule_id) REFERENCES recommendation_rules(rule_id)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─── Draft rules ──────────────────────────────────────────────────────────
-- Quantities are given only where the guidance itself fixes them (one test
-- per case, two vitamin A doses per measles case, two stool specimens per AFP
-- case). Everything else is 'as_assessed' until CESU supplies its figures.

-- Dengue
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Case investigation and active case finding in the barangay by the CESU surveillance officer', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures, outbreak investigation and response (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'DENGUE';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Search-and-destroy of mosquito breeding sites with barangay health workers', 'fixed', 1, 'team', 20,
       'DOH 4S strategy against dengue (Search and destroy)', 'Coordinate a daily clean-up with the barangay council.'
  FROM diseases WHERE disease_code = 'DENGUE';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Supply', 'Dengue NS1 rapid diagnostic test kits for the health center', 'per_case', 1, 'test kits', 30,
       'CESU to confirm (NS1 rapid testing at health centers)', 'One test per suspected case in the last 4 weeks.'
  FROM diseases WHERE disease_code = 'DENGUE';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Medicine', 'Oral rehydration salts and paracetamol for early management of suspected cases (no NSAIDs)', 'as_assessed', NULL, NULL, 40,
       'WHO (2009) Dengue guidelines for diagnosis, treatment, prevention and control', 'Quantities per CESU stock policy.'
  FROM diseases WHERE disease_code = 'DENGUE';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'IEC', '4S information materials (search and destroy, self-protection, early consultation)', 'as_assessed', NULL, NULL, 50,
       'DOH 4S strategy against dengue', NULL
  FROM diseases WHERE disease_code = 'DENGUE';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'High', 'Team', 'Spraying or fogging team for the hotspot area', 'fixed', 1, 'team', 15,
       'DOH 4S strategy against dengue (spraying and fogging of hotspot areas)', 'Only where cases rose for two consecutive weeks.'
  FROM diseases WHERE disease_code = 'DENGUE';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'High', 'Team', 'Advise hospitals and health centers serving the barangay to prepare for more dengue consultations and admissions', 'fixed', 1, 'advisory', 25,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'DENGUE';

-- Measles (single-case trigger: one case makes the barangay Moderate)
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Case investigation within 24 hours of notification (Category I disease)', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'MEA';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Supply', 'Specimen collection kit for laboratory confirmation at the national reference laboratory', 'per_case', 1, 'kits', 20,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'MEA';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Medicine', 'Vitamin A, two age-appropriate doses 24 hours apart for each case', 'per_case', 2, 'doses', 30,
       'WHO recommendation on vitamin A for measles cases', 'Dose by age (50,000 / 100,000 / 200,000 IU).'
  FROM diseases WHERE disease_code = 'MEA';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Contact tracing and vaccination of susceptible contacts', 'fixed', 1, 'team', 40,
       'DOH National Immunization Program, CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'MEA';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'IEC', 'Measles vaccination advisory for households in the barangay', 'as_assessed', NULL, NULL, 50,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'MEA';

-- Acute flaccid paralysis (single-case trigger)
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Case investigation within 24 hours of notification (Category I disease)', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'AFP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Supply', 'Stool specimen containers with cold-chain carrier', 'per_case', 2, 'containers', 20,
       'WHO polio surveillance standard: two stool specimens within 14 days of onset, at least 24 hours apart', NULL
  FROM diseases WHERE disease_code = 'AFP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Follow-up examination 60 days after onset for residual paralysis', 'per_case', 1, 'visits', 30,
       'WHO polio surveillance standard', NULL
  FROM diseases WHERE disease_code = 'AFP';

-- Leptospirosis
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Case investigation, including flood and floodwater exposure history', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'LEP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Medicine', 'Doxycycline for post-exposure prophylaxis of exposed residents', 'as_assessed', NULL, NULL, 20,
       'DOH interim guidelines on leptospirosis prophylaxis', 'Prescribed by a physician by exposure risk. No self-medication.'
  FROM diseases WHERE disease_code = 'LEP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'IEC', 'Advisory on avoiding floodwater and early consultation after exposure', 'as_assessed', NULL, NULL, 30,
       'DOH leptospirosis advisories', NULL
  FROM diseases WHERE disease_code = 'LEP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'High', 'Team', 'Rodent control and drainage clean-up with the barangay and city environment office', 'fixed', 1, 'team', 15,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'LEP';

-- Typhoid fever
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Case investigation and identification of shared water and food sources', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'TYP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Water source inspection and sampling by sanitary inspectors', 'fixed', 1, 'team', 20,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'TYP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'IEC', 'Safe water, food handling, and hand-washing advisory', 'as_assessed', NULL, NULL, 30,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'TYP';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'High', 'Supply', 'Household water chlorination supplies for the affected area', 'as_assessed', NULL, NULL, 15,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'TYP';

-- Hand, foot and mouth disease
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Case investigation, including schools and day-care centers attended by cases', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'HFMD';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'IEC', 'Hand-washing and disinfection advisory for schools and day-care centers', 'as_assessed', NULL, NULL, 20,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'HFMD';

-- Influenza-like illness
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'Team', 'Verify clustering of cases and refer severe acute respiratory infections', 'fixed', 1, 'team', 10,
       'PIDSR Manual of Procedures (DOH, 2014)', NULL
  FROM diseases WHERE disease_code = 'ILI';
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
SELECT disease_id, 'Moderate', 'IEC', 'Respiratory hygiene and cough etiquette advisory', 'as_assessed', NULL, NULL, 20,
       'CESU to confirm', NULL
  FROM diseases WHERE disease_code = 'ILI';

-- Any other disease (no rules of its own)
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
VALUES (NULL, 'Moderate', 'Team', 'Case verification and investigation by the CESU surveillance officer', 'fixed', 1, 'team', 10,
        'PIDSR Manual of Procedures, outbreak investigation and response (DOH, 2014)', NULL);
INSERT INTO recommendation_rules (disease_id, risk_tier, category, item, scaling_basis, quantity_factor, unit, priority, source, notes)
VALUES (NULL, 'High', 'Team', 'Report to the City Health Officer for an outbreak response decision', 'fixed', 1, 'report', 15,
        'PIDSR Manual of Procedures (DOH, 2014)', NULL);

SELECT COALESCE(d.disease_code, '(any)') AS disease, r.risk_tier, COUNT(*) AS rules
  FROM recommendation_rules r LEFT JOIN diseases d ON d.disease_id = r.disease_id
 GROUP BY d.disease_code, r.risk_tier ORDER BY disease, r.risk_tier;
