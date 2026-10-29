USE hmap_db;
INSERT INTO diseases (disease_id, disease_code, disease_name, disease_category, single_case_trigger, display_order) VALUES
  (1,'DENGUE','Dengue','Category 2',0,1), (3,'MEA','Measles','Category 1',1,3), (7,'ABD','Acute Bloody Diarrhea','Category 2',0,7);
INSERT INTO barangays (barangay_id, barangay_name, population) VALUES
  (1,'Baclaran',35512), (2,'Tambo',28251), (3,'Vitalez',5350);

-- Dengue baseline 2020-2024, week 30: one case a year in Baclaran and Tambo (mean 1, SD 0, epidemic threshold 1)
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year)
  SELECT 1, 'Confirmed', b.id, 30, 2019 + s.seq FROM seq_1_to_5 s, (SELECT 1 AS id UNION SELECT 2) b;
-- 2025 week 30: Baclaran 5 (Confirmed), Tambo 3 (Probable), plus 2 Baclaran cases in week 28
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year)
  SELECT 1, 'Confirmed', 1, 30, 2025 FROM seq_1_to_5;
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year)
  SELECT 1, 'Probable', 2, 30, 2025 FROM seq_1_to_3;
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year)
  SELECT 1, 'Confirmed', 1, 28, 2025 FROM seq_1_to_2;
-- a Suspect case must not count
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year)
  VALUES (1, 'Suspect', 3, 30, 2025);

-- Active hotspot (CESU rule) containing a Baclaran week-30 case
INSERT INTO detection_runs (detection_run_id, disease_code, eps_meters, min_samples, window_weeks, cases_evaluated, clusters_detected)
  VALUES (1, 'DENGUE', 200, 3, 4, 100, 1);
INSERT INTO case_clusters (cluster_id, detection_run_id, fingerprint, window_start, window_end, centroid_lat, centroid_lng, case_count, radius_m)
  VALUES (1, 1, REPEAT('a', 40), '2025-07-14', '2025-07-26', 14.5, 121.0, 3, 120);
INSERT INTO case_cluster_members (cluster_id, case_id)
  SELECT 1, MIN(case_id) FROM cases WHERE disease_id = 1 AND barangay_id = 1 AND morbidity_year = 2025 AND morbidity_week = 30;

-- Measles: one case in Vitalez. ABD: two cases in Tambo, zero baseline.
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year) VALUES (3, 'Confirmed', 3, 30, 2025);
INSERT INTO cases (disease_id, case_classification, barangay_id, morbidity_week, morbidity_year)
  SELECT 7, 'Confirmed', 2, 30, 2025 FROM seq_1_to_2;
