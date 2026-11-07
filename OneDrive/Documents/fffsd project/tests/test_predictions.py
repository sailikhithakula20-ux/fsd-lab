"""
Test Suite for Supervised ML Risk Prediction and Explainable AI (SHAP) (Phase 9).
Validates model inference, SHAP TreeExplainer attributions, database persistence, and HTTP routes.
"""

import pytest
from app import create_app
from models import (
    db,
    User,
    UserProfile,
    HealthAssessment,
    MLPredictionResult
)
from services.prediction_service import PredictionService


@pytest.fixture
def app():
    """Create test application context with SQLite."""
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        user = User(
            email="patient@healthportal.local",
            full_name="Pooja Patient",
            role="user"
        )
        user.set_password("SecurePass@123")
        db.session.add(user)
        db.session.commit()

        profile = UserProfile(
            user_id=user.id,
            age=32,
            gender="female",
            height_cm=165.0,
            weight_kg=60.0,
            dietary_preference="vegetarian",
            activity_level="moderate"
        )
        db.session.add(profile)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client, app):
    """Authenticated client session for user id 1."""
    with client.session_transaction() as sess:
        sess['_user_id'] = "1"
        sess['_fresh'] = True
    return client


# =============================================================================
# 1. Model Inference & SHAP Attribution Tests
# =============================================================================

def test_diabetes_inference_high_risk(app):
    """Verify that clinically severe markers yield high diabetes risk and positive SHAP attributions."""
    with app.app_context():
        inputs = {
            'pregnancies': 4,
            'glucose': 185.0,
            'blood_pressure': 88.0,
            'skin_thickness': 38.0,
            'insulin': 240.0,
            'bmi': 36.5,
            'diabetes_pedigree': 1.1,
            'age': 54.0
        }

        res = PredictionService.evaluate_diabetes_risk(user_id=1, feature_dict=inputs, persist=True)

        assert res['condition'] == 'diabetes'
        assert res['risk_score'] >= 0.65
        assert res['risk_category'] == 'High Risk'
        assert len(res['contributing_features']) == 8
        assert 'interventions' in res
        assert len(res['interventions']) > 0

        # Fasting glucose should have a high positive SHAP value
        glucose_feat = next(f for f in res['contributing_features'] if f['feature'] == 'glucose')
        assert glucose_feat['direction'] == 'risk_increasing'
        assert glucose_feat['shap_value'] > 0
        assert "risk accelerator" in glucose_feat['explanation']


def test_diabetes_inference_low_risk(app):
    """Verify that optimal metabolic parameters yield low diabetes risk."""
    with app.app_context():
        inputs = {
            'pregnancies': 0,
            'glucose': 82.0,
            'blood_pressure': 65.0,
            'skin_thickness': 18.0,
            'insulin': 45.0,
            'bmi': 20.8,
            'diabetes_pedigree': 0.18,
            'age': 22.0
        }

        res = PredictionService.evaluate_diabetes_risk(user_id=1, feature_dict=inputs, persist=False)

        assert res['risk_score'] < 0.35
        assert res['risk_category'] == 'Low Risk'

        # Glucose should act as protective buffer
        glucose_feat = next(f for f in res['contributing_features'] if f['feature'] == 'glucose')
        assert glucose_feat['direction'] == 'protective'
        assert glucose_feat['shap_value'] <= 0


def test_cardiovascular_inference(app):
    """Verify CVD inference and multi-parameter SHAP explanation generation."""
    with app.app_context():
        inputs = {
            'age': 66.0,
            'sex': 1,
            'chest_pain_type': 3,
            'resting_bp': 165.0,
            'cholesterol': 310.0,
            'fasting_blood_sugar': 1,
            'resting_ecg': 1,
            'max_heart_rate': 115.0,
            'exercise_angina': 1,
            'st_depression': 2.8,
            'st_slope': 2,
            'num_major_vessels': 2
        }

        res = PredictionService.evaluate_cardiovascular_risk(user_id=1, feature_dict=inputs, persist=True)

        assert res['condition'] == 'cardiovascular'
        assert res['risk_score'] >= 0.60
        assert res['risk_category'] in ['Moderate Risk', 'High Risk']
        assert len(res['contributing_features']) == 12
        assert len(res['interventions']) > 0


def test_prediction_database_persistence(app):
    """Verify that inference creates HealthAssessment and MLPredictionResult relational records."""
    with app.app_context():
        inputs = {
            'pregnancies': 1,
            'glucose': 130.0,
            'blood_pressure': 76.0,
            'skin_thickness': 24.0,
            'insulin': 110.0,
            'bmi': 27.2,
            'diabetes_pedigree': 0.45,
            'age': 38.0
        }

        res = PredictionService.evaluate_diabetes_risk(user_id=1, feature_dict=inputs, persist=True)
        pred_id = res['prediction_id']

        # Query database directly
        db_pred = db.session.get(MLPredictionResult, pred_id)
        assert db_pred is not None
        assert db_pred.user_id == 1
        assert db_pred.condition_name == 'diabetes'
        assert len(db_pred.get_contributing_features()) == 8

        # Test history retrieval
        history = PredictionService.get_user_history(user_id=1)
        assert len(history) >= 1
        assert history[0]['id'] == pred_id

        # Test single report retrieval with authorization
        report = PredictionService.get_prediction_by_id(prediction_id=pred_id, user_id=1)
        assert report is not None
        assert report['condition_name'] == 'diabetes'
        assert 'interventions' in report


# =============================================================================
# 2. HTTP Routes & REST API Tests
# =============================================================================

def test_assessment_hub_page_auth_guard(client):
    """Unauthenticated access redirects to login."""
    res = client.get('/assessment')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']


def test_assessment_hub_page_renders(auth_client):
    """Authenticated user can load the assessment hub."""
    res = auth_client.get('/assessment')
    assert res.status_code == 200
    assert b"Predictive Health Risk Diagnostic Hub" in res.data
    assert b"Type 2 Diabetes Risk Model" in res.data
    assert b"Cardiovascular Disease (CVD) Model" in res.data


def test_diabetes_form_renders_and_prepopulates(auth_client):
    """Form displays and auto-fills age and BMI from UserProfile."""
    res = auth_client.get('/assessment/diabetes')
    assert res.status_code == 200
    assert b"Type 2 Diabetes Risk Evaluation" in res.data
    # User age=32
    assert b'value="32"' in res.data


def test_diabetes_form_submission_and_redirect(auth_client):
    """Valid form submission processes ML inference and redirects to result view."""
    form_data = {
        'glucose': '140',
        'blood_pressure': '80',
        'insulin': '100',
        'bmi': '26.5',
        'age': '40',
        'skin_thickness': '25',
        'pregnancies': '1',
        'diabetes_pedigree': '0.5'
    }
    res = auth_client.post('/assessment/diabetes', data=form_data, follow_redirects=False)
    assert res.status_code == 302
    assert '/assessment/result/' in res.headers['Location']

    # Follow redirect to view report
    follow_res = auth_client.get(res.headers['Location'])
    assert follow_res.status_code == 200
    assert b"Explainable AI: SHAP Feature Attribution" in follow_res.data
    assert b"Evidence-Based Preventive Action Directives" in follow_res.data


def test_cardiovascular_form_submission_and_redirect(auth_client):
    """Valid CVD form submission redirects to report view."""
    form_data = {
        'age': '55',
        'sex': '1',
        'chest_pain_type': '2',
        'resting_bp': '135',
        'cholesterol': '230',
        'fasting_blood_sugar': '0',
        'resting_ecg': '0',
        'max_heart_rate': '148',
        'exercise_angina': '0',
        'st_depression': '0.8',
        'st_slope': '0',
        'num_major_vessels': '0'
    }
    res = auth_client.post('/assessment/cardiovascular', data=form_data, follow_redirects=False)
    assert res.status_code == 302
    assert '/assessment/result/' in res.headers['Location']


def test_api_predict_diabetes_endpoint(auth_client):
    """REST API: POST /api/v1/assessment/predict-diabetes."""
    payload = {
        'glucose': 110,
        'blood_pressure': 72,
        'bmi': 23.5,
        'age': 30,
        'insulin': 60,
        'skin_thickness': 20,
        'pregnancies': 0,
        'diabetes_pedigree': 0.3
    }
    res = auth_client.post('/api/v1/assessment/predict-diabetes', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'risk_score' in data['result']
    assert len(data['result']['contributing_features']) == 8


def test_api_predict_heart_endpoint(auth_client):
    """REST API: POST /api/v1/assessment/predict-heart."""
    payload = {
        'age': 48,
        'sex': 1,
        'chest_pain_type': 0,
        'resting_bp': 125,
        'cholesterol': 210,
        'fasting_blood_sugar': 0,
        'resting_ecg': 0,
        'max_heart_rate': 160,
        'exercise_angina': 0,
        'st_depression': 0.2,
        'st_slope': 0,
        'num_major_vessels': 0
    }
    res = auth_client.post('/api/v1/assessment/predict-heart', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert 'risk_score' in data['result']


def test_api_history_endpoint(auth_client):
    """REST API: GET /api/v1/assessment/history."""
    res = auth_client.get('/api/v1/assessment/history')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert isinstance(data['history'], list)
