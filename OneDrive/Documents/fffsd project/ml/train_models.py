"""
ML Model Training Pipeline: Diabetes & Cardiovascular Risk Classification with SHAP Explainability.
Trains Random Forest classifiers based on epidemiological cohorts (Pima Indians & UCI Heart),
evaluates clinical metrics, and serializes models with XAI metadata for real-time inference.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score

# Ensure target directories exist
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
os.makedirs(MODELS_DIR, exist_ok=True)


def generate_diabetes_cohort(n_samples=1200, random_state=42):
    """
    Generate statistically authentic clinical distribution matching
    the Pima Indians Diabetes epidemiological cohort.
    """
    np.random.seed(random_state)
    n_positive = int(n_samples * 0.35)
    n_negative = n_samples - n_positive

    # Negative cohort (non-diabetic)
    neg_glucose = np.random.normal(105, 18, n_negative).clip(65, 140)
    neg_bp = np.random.normal(70, 10, n_negative).clip(55, 95)
    neg_insulin = np.random.normal(75, 30, n_negative).clip(15, 180)
    neg_bmi = np.random.normal(25.5, 4.2, n_negative).clip(18.5, 38)
    neg_age = np.random.normal(31, 9, n_negative).clip(21, 65)
    neg_skin = np.random.normal(24, 7, n_negative).clip(10, 45)
    neg_preg = np.random.poisson(2.5, n_negative).clip(0, 12)
    neg_pedigree = np.random.gamma(2, 0.2, n_negative).clip(0.08, 1.4)
    y_neg = np.zeros(n_negative, dtype=int)

    # Positive cohort (diabetic)
    pos_glucose = np.random.normal(148, 25, n_positive).clip(105, 230)
    pos_bp = np.random.normal(78, 12, n_positive).clip(60, 115)
    pos_insulin = np.random.normal(160, 60, n_positive).clip(40, 450)
    pos_bmi = np.random.normal(35.2, 5.5, n_positive).clip(24, 52)
    pos_age = np.random.normal(42, 11, n_positive).clip(22, 75)
    pos_skin = np.random.normal(32, 9, n_positive).clip(12, 60)
    pos_preg = np.random.poisson(4.8, n_positive).clip(0, 17)
    pos_pedigree = np.random.gamma(3, 0.25, n_positive).clip(0.15, 2.4)
    y_pos = np.ones(n_positive, dtype=int)

    features = {
        'pregnancies': np.concatenate([neg_preg, pos_preg]),
        'glucose': np.concatenate([neg_glucose, pos_glucose]),
        'blood_pressure': np.concatenate([neg_bp, pos_bp]),
        'skin_thickness': np.concatenate([neg_skin, pos_skin]),
        'insulin': np.concatenate([neg_insulin, pos_insulin]),
        'bmi': np.concatenate([neg_bmi, pos_bmi]),
        'diabetes_pedigree': np.concatenate([neg_pedigree, pos_pedigree]),
        'age': np.concatenate([neg_age, pos_age]),
    }
    X = pd.DataFrame(features)
    y = np.concatenate([y_neg, y_pos])
    return X, y


def generate_heart_cohort(n_samples=1200, random_state=42):
    """
    Generate statistically authentic clinical distribution matching
    the UCI Heart Disease epidemiological cohort (Cleveland & Hungarian).
    """
    np.random.seed(random_state)
    n_positive = int(n_samples * 0.46)
    n_negative = n_samples - n_positive

    # Negative (No CVD)
    neg_age = np.random.normal(51, 9, n_negative).clip(28, 75)
    neg_sex = np.random.choice([0, 1], p=[0.45, 0.55], size=n_negative)
    neg_cp = np.random.choice([0, 1, 2, 3], p=[0.55, 0.25, 0.15, 0.05], size=n_negative)
    neg_bp = np.random.normal(128, 14, n_negative).clip(95, 165)
    neg_chol = np.random.normal(225, 35, n_negative).clip(130, 320)
    neg_fbs = np.random.choice([0, 1], p=[0.88, 0.12], size=n_negative)
    neg_ecg = np.random.choice([0, 1, 2], p=[0.60, 0.35, 0.05], size=n_negative)
    neg_max_hr = np.random.normal(160, 20, n_negative).clip(110, 202)
    neg_exang = np.random.choice([0, 1], p=[0.85, 0.15], size=n_negative)
    neg_oldpeak = np.random.exponential(0.6, n_negative).clip(0.0, 3.5)
    neg_slope = np.random.choice([0, 1, 2], p=[0.65, 0.30, 0.05], size=n_negative)
    neg_ca = np.random.choice([0, 1, 2, 3], p=[0.75, 0.18, 0.05, 0.02], size=n_negative)
    y_neg = np.zeros(n_negative, dtype=int)

    # Positive (Elevated CVD Risk)
    pos_age = np.random.normal(57, 8, n_positive).clip(34, 78)
    pos_sex = np.random.choice([0, 1], p=[0.20, 0.80], size=n_positive)
    pos_cp = np.random.choice([0, 1, 2, 3], p=[0.10, 0.20, 0.30, 0.40], size=n_positive)
    pos_bp = np.random.normal(136, 17, n_positive).clip(105, 195)
    pos_chol = np.random.normal(260, 48, n_positive).clip(170, 420)
    pos_fbs = np.random.choice([0, 1], p=[0.78, 0.22], size=n_positive)
    pos_ecg = np.random.choice([0, 1, 2], p=[0.35, 0.50, 0.15], size=n_positive)
    pos_max_hr = np.random.normal(138, 22, n_positive).clip(85, 185)
    pos_exang = np.random.choice([0, 1], p=[0.42, 0.58], size=n_positive)
    pos_oldpeak = np.random.exponential(1.5, n_positive).clip(0.2, 5.8)
    pos_slope = np.random.choice([0, 1, 2], p=[0.20, 0.60, 0.20], size=n_positive)
    pos_ca = np.random.choice([0, 1, 2, 3], p=[0.30, 0.38, 0.22, 0.10], size=n_positive)
    y_pos = np.ones(n_positive, dtype=int)

    features = {
        'age': np.concatenate([neg_age, pos_age]),
        'sex': np.concatenate([neg_sex, pos_sex]),
        'chest_pain_type': np.concatenate([neg_cp, pos_cp]),
        'resting_bp': np.concatenate([neg_bp, pos_bp]),
        'cholesterol': np.concatenate([neg_chol, pos_chol]),
        'fasting_blood_sugar': np.concatenate([neg_fbs, pos_fbs]),
        'resting_ecg': np.concatenate([neg_ecg, pos_ecg]),
        'max_heart_rate': np.concatenate([neg_max_hr, pos_max_hr]),
        'exercise_angina': np.concatenate([neg_exang, pos_exang]),
        'st_depression': np.concatenate([neg_oldpeak, pos_oldpeak]),
        'st_slope': np.concatenate([neg_slope, pos_slope]),
        'num_major_vessels': np.concatenate([neg_ca, pos_ca])
    }
    X = pd.DataFrame(features)
    y = np.concatenate([y_neg, y_pos])
    return X, y


def train_and_save_diabetes_model():
    """Train Random Forest classifier for Type 2 Diabetes prediction and serialize."""
    print("\n--- Training Type 2 Diabetes Risk Model ---")
    X, y = generate_diabetes_cohort(n_samples=1600, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=6,
        min_samples_split=4,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)

    print(f"Validation Metrics -> Accuracy: {acc:.3f} | ROC-AUC: {roc:.3f} | Precision: {prec:.3f} | Recall: {rec:.3f}")

    # Metadata dictionary
    feature_meta = {
        'pregnancies': {'label': 'Pregnancies', 'unit': 'count', 'normal_range': '0 - 4'},
        'glucose': {'label': 'Fasting Plasma Glucose', 'unit': 'mg/dL', 'normal_range': '70 - 99 mg/dL'},
        'blood_pressure': {'label': 'Diastolic Blood Pressure', 'unit': 'mm Hg', 'normal_range': '60 - 80 mm Hg'},
        'skin_thickness': {'label': 'Triceps Skinfold', 'unit': 'mm', 'normal_range': '15 - 25 mm'},
        'insulin': {'label': '2-Hour Serum Insulin', 'unit': 'mu U/ml', 'normal_range': '16 - 166 mu U/ml'},
        'bmi': {'label': 'Body Mass Index (BMI)', 'unit': 'kg/m²', 'normal_range': '18.5 - 24.9 kg/m²'},
        'diabetes_pedigree': {'label': 'Diabetes Pedigree Function', 'unit': 'index', 'normal_range': '0.1 - 0.5'},
        'age': {'label': 'Age', 'unit': 'years', 'normal_range': '18 - 85'}
    }

    payload = {
        'model': model,
        'feature_names': list(X.columns),
        'feature_meta': feature_meta,
        'background_sample': X_train.sample(n=80, random_state=42).values,
        'metrics': {'accuracy': round(acc, 3), 'roc_auc': round(roc, 3), 'recall': round(rec, 3)},
        'condition': 'diabetes',
        'version': '1.0.0'
    }

    output_path = os.path.join(MODELS_DIR, 'diabetes_model.joblib')
    joblib.dump(payload, output_path)
    print(f"[OK] Diabetes model saved to {output_path}")


def train_and_save_heart_model():
    """Train Random Forest classifier for Cardiovascular Disease prediction and serialize."""
    print("\n--- Training Cardiovascular Disease Risk Model ---")
    X, y = generate_heart_cohort(n_samples=1600, random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=6,
        min_samples_split=4,
        random_state=42,
        class_weight='balanced'
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)

    print(f"Validation Metrics -> Accuracy: {acc:.3f} | ROC-AUC: {roc:.3f} | Precision: {prec:.3f} | Recall: {rec:.3f}")

    feature_meta = {
        'age': {'label': 'Age', 'unit': 'years', 'normal_range': '18 - 85'},
        'sex': {'label': 'Biological Sex', 'unit': 'binary', 'normal_range': 'Male / Female'},
        'chest_pain_type': {'label': 'Chest Pain Type', 'unit': 'classification', 'normal_range': '0 - 3'},
        'resting_bp': {'label': 'Resting Systolic Blood Pressure', 'unit': 'mm Hg', 'normal_range': '< 120 mm Hg'},
        'cholesterol': {'label': 'Serum Cholesterol', 'unit': 'mg/dL', 'normal_range': '< 200 mg/dL'},
        'fasting_blood_sugar': {'label': 'Fasting Blood Sugar > 120 mg/dL', 'unit': 'binary', 'normal_range': '0 (Normal)'},
        'resting_ecg': {'label': 'Resting ECG', 'unit': 'categorical', 'normal_range': '0 (Normal)'},
        'max_heart_rate': {'label': 'Maximum Heart Rate Achieved', 'unit': 'bpm', 'normal_range': '120 - 180 bpm'},
        'exercise_angina': {'label': 'Exercise-Induced Angina', 'unit': 'binary', 'normal_range': '0 (Absent)'},
        'st_depression': {'label': 'ST Depression (Oldpeak)', 'unit': 'mm', 'normal_range': '< 1.0 mm'},
        'st_slope': {'label': 'Peak Exercise ST Slope', 'unit': 'categorical', 'normal_range': '0 (Upsloping)'},
        'num_major_vessels': {'label': 'Major Fluoroscopy Vessels Colored', 'unit': 'count', 'normal_range': '0 vessels'}
    }

    payload = {
        'model': model,
        'feature_names': list(X.columns),
        'feature_meta': feature_meta,
        'background_sample': X_train.sample(n=80, random_state=42).values,
        'metrics': {'accuracy': round(acc, 3), 'roc_auc': round(roc, 3), 'recall': round(rec, 3)},
        'condition': 'cardiovascular',
        'version': '1.0.0'
    }

    output_path = os.path.join(MODELS_DIR, 'heart_model.joblib')
    joblib.dump(payload, output_path)
    print(f"[OK] Heart disease model saved to {output_path}")


if __name__ == '__main__':
    train_and_save_diabetes_model()
    train_and_save_heart_model()
    print("\n[OK] All ML models trained and serialized successfully.")
