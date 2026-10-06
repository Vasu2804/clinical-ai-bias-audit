import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set seed for exact reproducibility
np.random.seed(42)
random.seed(42)

NUM_RECORDS = 5000

# 1. Demographics & Dates
genders = ['Male', 'Female', 'Non-Binary', 'Unknown']
gender_probs = [0.48, 0.48, 0.01, 0.03]
patient_gender = np.random.choice(genders, NUM_RECORDS, p=gender_probs)

departments = ['General Medicine', 'Emergency', 'Cardiology', 'Geriatrics']

# Generate true patient age: Normal(56, 18), clipped 18 to 95
true_age = np.random.normal(loc=56, scale=18, size=NUM_RECORDS)
true_age = np.clip(true_age, 18, 95).astype(int)

# Encounter dates across 2025
encounter_dates = [datetime(2025, 1, 1) + timedelta(days=int(random.randint(0, 364))) for _ in range(NUM_RECORDS)]

# Department routing based on age and clinical acuity
department_list = []
for a in true_age:
    if a >= 70:
        department_list.append(np.random.choice(departments, p=[0.15, 0.15, 0.20, 0.50]))
    elif a >= 50:
        department_list.append(np.random.choice(departments, p=[0.35, 0.30, 0.30, 0.05]))
    else:
        department_list.append(np.random.choice(departments, p=[0.45, 0.45, 0.10, 0.00]))

# Derive Date of Birth (DOB) from encounter_date and true_age
patient_dob = [enc - timedelta(days=int(a * 365.25 + random.randint(-180, 180))) for enc, a in zip(encounter_dates, true_age)]
patient_dob_str = [d.strftime('%Y-%m-%d') for d in patient_dob]
encounter_date_str = [d.strftime('%Y-%m-%d') for d in encounter_dates]

# INTENTIONAL BIAS 1: Missing age in Geriatrics / Patients > 75 (Completeness & Statistical Representation - Art. 10(3) & 10(2)(h))
# Upstream legacy intake terminal bug in Geriatrics fails to sync patient_age into EMR triage table
patient_age = []
for a, dept in zip(true_age, department_list):
    if dept == 'Geriatrics' and a >= 75:
        # 45% missing rate in geriatric elderly intake
        if random.random() < 0.45:
            patient_age.append(np.nan)
        else:
            patient_age.append(a)
    elif a >= 75 and random.random() < 0.10: # Small leakage across other departments
        patient_age.append(np.nan)
    else:
        patient_age.append(a)

# INTENTIONAL BIAS 2: Clinical Pain Down-coding (Prohibited Recording Bias & Health/Safety - Art. 10(2)(f) & (g))
# Female patients reporting moderate/severe pain (>= 5) have their pain down-coded by 2-3 points with 55% probability
pain_score_reported = np.random.randint(1, 11, size=NUM_RECORDS)
pain_score_recorded = []

for i in range(NUM_RECORDS):
    if patient_gender[i] == 'Female' and pain_score_reported[i] >= 5:
        # 55% chance of being down-coded by 2 or 3 points
        if random.random() < 0.55:
            reduction = random.choice([2, 3])
            pain_score_recorded.append(max(1, pain_score_reported[i] - reduction))
        else:
            pain_score_recorded.append(pain_score_reported[i])
    else:
        pain_score_recorded.append(pain_score_reported[i])

# INTENTIONAL BIAS 3: Geographical Setting & Fragmented Records (Indirect Discrimination - Art. 10(4) & 10(2)(f))
# 100xx are affluent zip codes; 104xx are lower-income zip codes
zip_codes = ['10001', '10002', '10451', '10452', '10453']
zip_probs = [0.2, 0.2, 0.2, 0.2, 0.2]
patient_zip = np.random.choice(zip_codes, NUM_RECORDS, p=zip_probs)

historical_records_available = []
for z in patient_zip:
    if z.startswith('104'):
        historical_records_available.append(bool(np.random.choice([True, False], p=[0.40, 0.60]))) # 60% missing in low-income
    else:
        historical_records_available.append(bool(np.random.choice([True, False], p=[0.90, 0.10]))) # 10% missing in affluent

# 4. Target Variable: Actual 30-Day Readmission vs AI Predicted Risk Score
# Ground truth readmission rate is ~14.5% across all cohorts (demographically neutral)
actual_readmission = np.random.choice([0, 1], NUM_RECORDS, p=[0.855, 0.145])

ai_risk_score = []
for i in range(NUM_RECORDS):
    base_score = 50.0
    if actual_readmission[i] == 1:
        base_score += 25.0
    
    # Age factor: elderly patients (>65) receive higher baseline clinical risk
    cur_age = patient_age[i] if not np.isnan(patient_age[i]) else true_age[i]
    if cur_age > 65:
        base_score += 10.0
        
    # Model algorithmic bias: heavily penalizes fragmented historical records (+20 pts)
    if not historical_records_available[i]:
        base_score += 20.0
    
    score = np.clip(base_score + np.random.normal(0, 9), 0, 100)
    ai_risk_score.append(round(float(score), 1))

# Create DataFrame
df = pd.DataFrame({
    'patient_id': [f"PID-{str(i).zfill(5)}" for i in range(1, NUM_RECORDS + 1)],
    'encounter_date': encounter_date_str,
    'patient_dob': patient_dob_str,
    'department': department_list,
    'patient_age': patient_age,
    'patient_gender': patient_gender,
    'patient_zip': patient_zip,
    'pain_score_reported_triage': pain_score_reported,
    'pain_score_recorded_emr': pain_score_recorded,
    'historical_records_available': historical_records_available,
    'actual_30_day_readmission': actual_readmission,
    'ai_predicted_risk_score': ai_risk_score
})

# Save to CSV
output_csv = 'triage_dataset_raw.csv'
df.to_csv(output_csv, index=False)
print(f"Dataset '{output_csv}' generated successfully with 5,000 records.")
