# Data Governance Remediation Report (MEMO)

**TO:** Chief Risk Officer, VP of Data Science, Medical Director  
**FROM:** AI Governance Analyst (Vasu Sharma)  
**DATE:** September 25, 2026  
**SUBJECT:** URGENT: EU AI Act Article 10 Violations in Clinical Triage AI Training Data (Regulation (EU) 2024/1689)  

---

## Executive Summary
An audit of the `triage_dataset_raw.csv` candidate training data intended for the Clinical Triage Readmission Predictor has revealed three structural violations of the EU AI Act (Article 10: Data and Data Governance, Regulation (EU) 2024/1689). 

**Recommendation:** The training of this AI model must be HALTED until the underlying data biases are remediated. Training a model on this data will result in a non-compliant High-Risk AI system that cannot be legally deployed in the European Union.

---

## 1. Finding: Completeness Failure & Geriatric Exclusion (Article 10(3) & 10(2)(h))
*   **The Issue:** Upon analyzing the data in SQL and visualizing it in Power BI, we found that patient age is missing by a significant margin in the Geriatrics department. Specifically, **215 out of 5,000 records (4.30%) lack age data**, with **100% of missing records clustered in patients aged 70+**. The Geriatrics department displays a **27.00% missingness rate (182/674 encounters)**, compared to <1.5% across all other departments.
*   **The Risk:** The dataset violates Article 10(3) requiring training data to be "to the best extent possible, free of errors and complete" and have appropriate statistical properties regarding vulnerable groups. The AI will perform unreliably on elderly patients who represent the highest clinical readmission risk.
*   **Remediation Required:** Data Engineering must implement an automated ETL ingestion rule deriving `patient_age` directly from `patient_dob` (`DATEDIFF(patient_dob, encounter_date, YEAR)`), while fixing the legacy Geriatric intake terminal sync to ensure elderly demographic data is never skipped.

## 2. Finding: Prohibited Bias in Clinical Pain Recording (Article 10(2)(f) & 10(2)(g))
*   **The Issue:** For female patients, the average pain score recorded in the EMR is significantly down-coded compared to what patients verbally reported. Across all encounters, recorded female pain drops to **4.56 vs 5.38 reported (-0.82 delta)**, while male recording is 100% faithful (5.46 vs 5.46). For female patients presenting with moderate-to-severe pain (`reported >= 5`), **56.40% of records are down-coded by 2 to 3 points**, dropping average recorded pain from 7.48 to 6.07.
*   **The Risk:** The dataset contains historical recording bias. In violation of Article 10(2)(f), this bias will lead to prohibited sex-based discrimination and adverse health outcomes for female patients by systematically under-triaging acute female conditions.
*   **Remediation Required:** The model must be trained on `pain_score_reported_triage` (the direct patient-reported score) rather than `pain_score_recorded_emr` in order to prevent historical clinical recording bias from trickling into automated risk scoring.

## 3. Finding: Geographical Context & Prohibited Indirect Discrimination (Article 10(4) & 10(2)(f))
*   **The Issue:** Upon analyzing the data across zip code tiers, patients in affluent neighborhoods (`100xx`) have a much lower rate of missing medical records (**10.09%**) compared to those living in lower-income regions (`104xx`, **60.68% missing records**). The AI model penalizes missing history with an automatic +20 point penalty, artificially inflating lower-income risk scores to **68.12 vs 58.31 (+9.81 pt penalty)** -- despite both cohorts exhibiting virtually identical ground-truth 30-day readmission rates (**13.92% vs 14.22%**).
*   **The Risk:** The model fails to account for the specific geographical/contextual setting under Article 10(4). It penalizes patients from lower-income zip codes (`104xx`) who naturally face fragmented healthcare histories, artificially inflating their readmission risk despite equal actual readmissions (indirect proxy discrimination under Article 10(2)(f)).
*   **Remediation Required:** The Data Science team must decouple the missing historical records factor from the scoring algorithm (treating missing history as neutral variance rather than an adverse clinical penalty) to prevent socioeconomic redlining from corrupting clinical predictions.

---
*Signed,*  
**Vasu Sharma**  
AI Governance & Regulatory Compliance Analyst
