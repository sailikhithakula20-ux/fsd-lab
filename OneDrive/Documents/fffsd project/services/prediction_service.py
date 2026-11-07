"""
PredictionService: Supervised Clinical Machine Learning & Explainable AI (SHAP) Engine.
Integrates serialized Random Forest diagnostic pipelines for Type 2 Diabetes and Cardiovascular
Disease, executes local TreeExplainer feature attributions, and generates personalized interventions.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
import shap

from models import (
    db,
    User,
    UserProfile,
    HealthAssessment,
    MLPredictionResult
)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml', 'saved_models')

CLINICAL_DISCLAIMER = (
    "CLINICAL DISCLAIMER: AuraHealth AI risk estimations are statistical approximations derived from "
    "supervised machine learning models trained on epidemiological cohorts (Pima Indians & UCI Heart). "
    "This software is strictly educational and does NOT constitute a clinical medical diagnosis, prescription, "
    "or therapeutic directive. Consult a certified medical doctor or endocrinologist for clinical laboratory testing."
)


class PredictionService:
    """Domain service for supervised inference, SHAP attribution, and clinical prevention plans."""

    _models = {}
    _explainers = {}

    @classmethod
    def _load_model(cls, condition_key):
        """Lazy-load and cache the serialized model package and SHAP TreeExplainer."""
        if condition_key not in cls._models:
            file_name = f"{condition_key}_model.joblib"
            model_path = os.path.join(MODELS_DIR, file_name)
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"ML Model file not found at {model_path}. Please run train_models.py.")

            pkg = joblib.load(model_path)
            cls._models[condition_key] = pkg
            cls._explainers[condition_key] = shap.TreeExplainer(pkg['model'])

        return cls._models[condition_key], cls._explainers[condition_key]

    # =========================================================================
    # Type 2 Diabetes Prediction & XAI
    # =========================================================================

    @classmethod
    def evaluate_diabetes_risk(cls, user_id, feature_dict, persist=True):
        """
        Evaluate Type 2 Diabetes risk using 8 clinical parameters:
        pregnancies, glucose, blood_pressure, skin_thickness, insulin, bmi, diabetes_pedigree, age.
        """
        pkg, explainer = cls._load_model('diabetes')
        model = pkg['model']
        feature_names = pkg['feature_names']
        feature_meta = pkg['feature_meta']

        # Construct single-row DataFrame ensuring exact feature alignment
        row_dict = {}
        for feat in feature_names:
            val = float(feature_dict.get(feat, 0.0))
            row_dict[feat] = [val]

        df = pd.DataFrame(row_dict)

        # 1. Model Inference
        probabilities = model.predict_proba(df)[0]
        risk_score = float(probabilities[1])  # Class 1 = diabetic risk

        # 2. Risk Categorization
        if risk_score < 0.35:
            risk_category = 'Low Risk'
            badge_class = 'bg-success'
        elif risk_score < 0.65:
            risk_category = 'Moderate Risk'
            badge_class = 'bg-warning text-dark'
        else:
            risk_category = 'High Risk'
            badge_class = 'bg-danger'

        # 3. Explainable AI via SHAP
        shap_values = explainer.shap_values(df)

        # Handle different SHAP return shapes:
        # Array (1, n_features, 2) or list of [arr_class0, arr_class1]
        if isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:
                vals = shap_values[0, :, 1]
            elif shap_values.ndim == 2:
                vals = shap_values[0, :]
            else:
                vals = shap_values
        elif isinstance(shap_values, list):
            vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            vals = np.zeros(len(feature_names))

        contributing_features = []
        for i, feat in enumerate(feature_names):
            phi = float(vals[i])
            val = float(df[feat].iloc[0])
            meta = feature_meta.get(feat, {'label': feat, 'unit': '', 'normal_range': ''})

            direction = 'risk_increasing' if phi > 0 else 'protective'
            impact_pct = round(abs(phi) * 100, 1)

            # Generate natural language explanation
            explanation = cls._generate_feature_explanation(
                condition='diabetes',
                feature=feat,
                label=meta['label'],
                value=val,
                unit=meta['unit'],
                phi=phi,
                normal_range=meta['normal_range']
            )

            contributing_features.append({
                'feature': feat,
                'label': meta['label'],
                'value': val,
                'unit': meta['unit'],
                'normal_range': meta['normal_range'],
                'shap_value': round(phi, 4),
                'importance': round(abs(phi), 4),
                'direction': direction,
                'impact_pct': impact_pct,
                'explanation': explanation
            })

        # Sort descending by absolute SHAP attribution
        contributing_features.sort(key=lambda x: x['importance'], reverse=True)

        # 4. Generate Clinical Lifestyle Interventions
        interventions = cls._generate_preventive_interventions('diabetes', df.iloc[0].to_dict(), risk_category)

        result_payload = {
            'condition': 'diabetes',
            'condition_name': 'Type 2 Diabetes Mellitus',
            'risk_score': round(risk_score, 3),
            'risk_percentage': round(risk_score * 100, 1),
            'risk_category': risk_category,
            'badge_class': badge_class,
            'contributing_features': contributing_features,
            'interventions': interventions,
            'clinical_disclaimer': CLINICAL_DISCLAIMER,
            'input_data': df.iloc[0].to_dict(),
            'model_version': pkg.get('version', '1.0.0')
        }

        # 5. Database Persistence
        if persist and user_id:
            assessment = HealthAssessment(
                user_id=user_id,
                assessment_type='diabetes'
            )
            assessment.set_inputs(result_payload['input_data'])
            db.session.add(assessment)
            db.session.flush()

            ml_result = MLPredictionResult(
                assessment_id=assessment.id,
                user_id=user_id,
                condition_name='diabetes',
                risk_score=risk_score,
                risk_category=risk_category,
                model_version=pkg.get('version', '1.0.0'),
                clinical_disclaimer=CLINICAL_DISCLAIMER
            )
            ml_result.set_contributing_features(contributing_features)
            db.session.add(ml_result)
            db.session.commit()

            result_payload['assessment_id'] = assessment.id
            result_payload['prediction_id'] = ml_result.id

        return result_payload

    # =========================================================================
    # Cardiovascular Disease Prediction & XAI
    # =========================================================================

    @classmethod
    def evaluate_cardiovascular_risk(cls, user_id, feature_dict, persist=True):
        """
        Evaluate Cardiovascular Disease risk using 12 clinical parameters:
        age, sex, chest_pain_type, resting_bp, cholesterol, fasting_blood_sugar,
        resting_ecg, max_heart_rate, exercise_angina, st_depression, st_slope, num_major_vessels.
        """
        pkg, explainer = cls._load_model('heart')
        model = pkg['model']
        feature_names = pkg['feature_names']
        feature_meta = pkg['feature_meta']

        row_dict = {}
        for feat in feature_names:
            val = float(feature_dict.get(feat, 0.0))
            row_dict[feat] = [val]

        df = pd.DataFrame(row_dict)

        # 1. Model Inference
        probabilities = model.predict_proba(df)[0]
        risk_score = float(probabilities[1])

        # 2. Risk Categorization
        if risk_score < 0.35:
            risk_category = 'Low Risk'
            badge_class = 'bg-success'
        elif risk_score < 0.65:
            risk_category = 'Moderate Risk'
            badge_class = 'bg-warning text-dark'
        else:
            risk_category = 'High Risk'
            badge_class = 'bg-danger'

        # 3. Explainable AI via SHAP
        shap_values = explainer.shap_values(df)

        if isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:
                vals = shap_values[0, :, 1]
            elif shap_values.ndim == 2:
                vals = shap_values[0, :]
            else:
                vals = shap_values
        elif isinstance(shap_values, list):
            vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            vals = np.zeros(len(feature_names))

        contributing_features = []
        for i, feat in enumerate(feature_names):
            phi = float(vals[i])
            val = float(df[feat].iloc[0])
            meta = feature_meta.get(feat, {'label': feat, 'unit': '', 'normal_range': ''})

            direction = 'risk_increasing' if phi > 0 else 'protective'
            impact_pct = round(abs(phi) * 100, 1)

            explanation = cls._generate_feature_explanation(
                condition='cardiovascular',
                feature=feat,
                label=meta['label'],
                value=val,
                unit=meta['unit'],
                phi=phi,
                normal_range=meta['normal_range']
            )

            contributing_features.append({
                'feature': feat,
                'label': meta['label'],
                'value': val,
                'unit': meta['unit'],
                'normal_range': meta['normal_range'],
                'shap_value': round(phi, 4),
                'importance': round(abs(phi), 4),
                'direction': direction,
                'impact_pct': impact_pct,
                'explanation': explanation
            })

        contributing_features.sort(key=lambda x: x['importance'], reverse=True)

        interventions = cls._generate_preventive_interventions('cardiovascular', df.iloc[0].to_dict(), risk_category)

        result_payload = {
            'condition': 'cardiovascular',
            'condition_name': 'Cardiovascular Disease (CVD)',
            'risk_score': round(risk_score, 3),
            'risk_percentage': round(risk_score * 100, 1),
            'risk_category': risk_category,
            'badge_class': badge_class,
            'contributing_features': contributing_features,
            'interventions': interventions,
            'clinical_disclaimer': CLINICAL_DISCLAIMER,
            'input_data': df.iloc[0].to_dict(),
            'model_version': pkg.get('version', '1.0.0')
        }

        if persist and user_id:
            assessment = HealthAssessment(
                user_id=user_id,
                assessment_type='cardiovascular'
            )
            assessment.set_inputs(result_payload['input_data'])
            db.session.add(assessment)
            db.session.flush()

            ml_result = MLPredictionResult(
                assessment_id=assessment.id,
                user_id=user_id,
                condition_name='cardiovascular',
                risk_score=risk_score,
                risk_category=risk_category,
                model_version=pkg.get('version', '1.0.0'),
                clinical_disclaimer=CLINICAL_DISCLAIMER
            )
            ml_result.set_contributing_features(contributing_features)
            db.session.add(ml_result)
            db.session.commit()

            result_payload['assessment_id'] = assessment.id
            result_payload['prediction_id'] = ml_result.id

        return result_payload

    # =========================================================================
    # Natural Language SHAP Explanations & Clinical Interventions
    # =========================================================================

    @staticmethod
    def _generate_feature_explanation(condition, feature, label, value, unit, phi, normal_range):
        """Construct a personalized, scientifically lucid explanation for each feature's SHAP impact."""
        direction_word = "elevated" if phi > 0 else "reduced"
        buffer_word = "risk accelerator" if phi > 0 else "protective buffer"

        if phi > 0:
            return (
                f"{label} at {value} {unit} acts as a {buffer_word}, shifting your statistical "
                f"risk profile upward by +{round(abs(phi) * 100, 1)}% relative to cohort baseline."
            )
        else:
            return (
                f"{label} at {value} {unit} serves as a {buffer_word}, mitigating your risk "
                f"profile by -{round(abs(phi) * 100, 1)}% towards optimal metabolic stability."
            )

    @staticmethod
    def _generate_preventive_interventions(condition, inputs, risk_category):
        """Generate targeted, evidence-based preventive dietary and lifestyle actions."""
        interventions = []

        if condition == 'diabetes':
            glucose = inputs.get('glucose', 100)
            bmi = inputs.get('bmi', 23.0)

            if glucose > 125:
                interventions.append({
                    'category': 'Glycemic Nutrition',
                    'icon': 'bi-cup-straw',
                    'title': 'Strict Low-GI Carbohydrate Substitution',
                    'directive': 'Transition from refined grains (white rice, maida) to complex legumes (moong dal, rajma) and millets (ragi, foxtail) to avoid glycemic spikes.'
                })
            elif glucose > 100:
                interventions.append({
                    'category': 'Glycemic Nutrition',
                    'icon': 'bi-cup-straw',
                    'title': 'Moderate Postprandial Management',
                    'directive': 'Pair dietary carbohydrates with soluble fiber and healthy fats to buffer insulin response; avoid sugary beverages and evening refined sweets.'
                })

            if bmi > 25.0:
                interventions.append({
                    'category': 'Weight & Metabolic Balance',
                    'icon': 'bi-speedometer2',
                    'title': 'Caloric Deficit & Visceral Fat Reduction',
                    'directive': 'Aim for a gradual 5-7% total body weight reduction via a 400 kcal daily deficit, which clinically enhances peripheral insulin sensitivity.'
                })

            interventions.append({
                'category': 'Physical Movement',
                'icon': 'bi-person-walking',
                'title': 'Postprandial 15-Minute Ambulatory Walks',
                'directive': 'Engage in a 15-minute moderate walk within 30 minutes of major meals to activate GLUT4 glucose transporters independent of insulin.'
            })

        elif condition == 'cardiovascular':
            cholesterol = inputs.get('cholesterol', 200)
            bp = inputs.get('resting_bp', 120)

            if cholesterol > 220:
                interventions.append({
                    'category': 'Lipid Management',
                    'icon': 'bi-heart-pulse',
                    'title': 'Saturated Fat Restriction & Soluble Fiber',
                    'directive': 'Limit dietary saturated fats to <7% of daily calories; incorporate oats, psyllium husk, fenugreek seeds, and omega-3 rich walnuts and chia seeds.'
                })

            if bp > 130:
                interventions.append({
                    'category': 'Vascular Health',
                    'icon': 'bi-droplet',
                    'title': 'DASH Diet & Sodium Moderation',
                    'directive': 'Target dietary sodium below 2,000 mg/day (approx. 1 level teaspoon of salt). Increase potassium-rich vegetables (spinach, cucumber, coconut water).'
                })

            interventions.append({
                'category': 'Cardiorespiratory Endurance',
                'icon': 'bi-bicycle',
                'title': 'Aerobic Zone 2 Exercise Protocol',
                'directive': 'Complete at least 150 minutes per week of moderate aerobic exercise (brisk walking, swimming, cycling at 60-70% maximum heart rate).'
            })

        return interventions

    # =========================================================================
    # Assessment History Retrieval
    # =========================================================================

    @classmethod
    def get_user_history(cls, user_id, condition=None):
        """Retrieve chronological assessment history for a specific user."""
        query = MLPredictionResult.query.filter_by(user_id=user_id)
        if condition:
            query = query.filter_by(condition_name=condition)
        records = query.order_by(MLPredictionResult.evaluated_at.desc()).all()
        return [r.to_dict() for r in records]

    @classmethod
    def get_prediction_by_id(cls, prediction_id, user_id):
        """Retrieve a specific prediction record with authorized user verification."""
        pred = MLPredictionResult.query.filter_by(id=prediction_id, user_id=user_id).first()
        if not pred:
            return None

        # Re-derive interventions based on condition and assessment inputs
        assessment = pred.assessment
        inputs = assessment.get_inputs() if assessment else {}
        interventions = cls._generate_preventive_interventions(pred.condition_name, inputs, pred.risk_category)

        data = pred.to_dict()
        data['inputs'] = inputs
        data['interventions'] = interventions
        data['badge_class'] = (
            'bg-success' if pred.risk_category == 'Low Risk' else
            'bg-warning text-dark' if pred.risk_category == 'Moderate Risk' else 'bg-danger'
        )
        return data
