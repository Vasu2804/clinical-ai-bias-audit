-- ------------------------------------------------------------------------------
-- TEST 1: Completeness & Demographic Exclusion Audit (Article 10(3) & 10(2)(h))
-- ------------------------------------------------------------------------------
SELECT 
    department,
    COUNT(*) AS total_patients,
    SUM(CASE WHEN patient_age IS NULL THEN 1 ELSE 0 END) AS missing_age_count,
    ROUND(100.0 * SUM(CASE WHEN patient_age IS NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_missing_age
FROM triage_dataset_raw
GROUP BY department
ORDER BY pct_missing_age DESC;

-- ------------------------------------------------------------------------------
-- TEST 2: Prohibited Bias in Clinical Pain Recording (Article 10(2)(f) & 10(2)(g))
-- GOAL: Find out if female patients reporting pain >= 5 are being down-coded.
-- ------------------------------------------------------------------------------

SELECT 
    patient_gender,
    COUNT(*) AS total_acute_patients,
    ROUND(AVG(pain_score_reported_triage), 2) AS avg_reported,
    ROUND(AVG(pain_score_recorded_emr), 2) AS avg_recorded,
    -- Count how many were down-coded by 2+ points
    SUM(CASE WHEN (pain_score_reported_triage - pain_score_recorded_emr) >= 2 THEN 1 ELSE 0 END) AS downcoded_count,
    -- Calculate the percentage of down-coded patients
    ROUND(100.0 * SUM(CASE WHEN (pain_score_reported_triage - pain_score_recorded_emr) >= 2 THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_downcoded
FROM triage_dataset_raw tdr
WHERE pain_score_reported_triage >= 5
GROUP BY patient_gender;


-- ------------------------------------------------------------------------------
-- TEST 3: Geographical Context & Indirect Discrimination (Article 10(4) & 10(2)(f))
-- GOAL: Compare missing history rates and AI risk scores between Zip Code 100xx and 104xx.
-- ------------------------------------------------------------------------------

SELECT 
    SUBSTR(patient_zip, 1, 3) || 'xx' AS zip_area,
    COUNT(*) AS total_patients,
    -- 1. Missing Medical History
    SUM(CASE WHEN historical_records_available IN (0, 'False') THEN 1 ELSE 0 END) AS missing_history_count,
    ROUND(100.0 * SUM(CASE WHEN historical_records_available IN (0, 'False') THEN 1 ELSE 0 END) / COUNT(*), 2) AS pct_missing_history,
    -- 2. AI Risk Score (Showing the penalty)
    ROUND(AVG(ai_predicted_risk_score), 2) AS avg_predicted_risk,
    -- 3. Ground Truth Parity (Proving the penalty is unwarranted)
    ROUND(100.0 * SUM(actual_30_day_readmission) / COUNT(*), 2) AS actual_readmission_rate
FROM triage_dataset_raw tdr
GROUP BY SUBSTR(patient_zip, 1, 3)



