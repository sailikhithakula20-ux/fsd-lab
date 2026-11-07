"""
Test Suite for Physical Activity, Hydration, Sleep & MET Metabolic Calculations (Phase 8).
Validates domain logic, database upserts, Ainsworth's MET formulation, and API endpoints.
"""

import pytest
from datetime import date, timedelta
from app import create_app
from models import (
    db,
    User,
    UserProfile,
    ActivityLog,
    WaterLog,
    SleepLog,
    ExerciseLog
)
from services.activity_service import ActivityService, MET_ACTIVITIES


@pytest.fixture
def app():
    """Create testing application context with in-memory SQLite."""
    app = create_app('testing')
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        # Seed test user
        user = User(
            email="athlete@healthportal.local",
            full_name="Arjun Athlete",
            role="user"
        )
        user.set_password("SecurePass@123")
        db.session.add(user)
        db.session.commit()

        # Seed user profile
        profile = UserProfile(
            user_id=user.id,
            age=26,
            gender="male",
            height_cm=175.0,
            weight_kg=70.0,
            dietary_preference="vegetarian",
            activity_level="active"
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
    """Authenticated test client session."""
    with client.session_transaction() as sess:
        sess['_user_id'] = "1"
        sess['_fresh'] = True
    return client


# =============================================================================
# 1. Domain Logic & MET Unit Tests
# =============================================================================

def test_met_calorie_calculation():
    """Validate Ainsworth MET formula: kcal = min * [MET * 3.5 * weight / 200]."""
    # Running (8.0 MET, 30 min, 70 kg)
    # 30 * 8.0 * 3.5 * 70 / 200 = 294.0 kcal
    burn = ActivityService.calculate_met_calories(met_value=8.0, duration_minutes=30, weight_kg=70.0)
    assert burn == 294.0

    # Gentle Yoga (2.5 MET, 60 min, 60 kg)
    # 60 * 2.5 * 3.5 * 60 / 200 = 157.5 kcal
    burn_yoga = ActivityService.calculate_met_calories(met_value=2.5, duration_minutes=60, weight_kg=60.0)
    assert burn_yoga == 157.5

    # Edge cases: 0 or negative
    assert ActivityService.calculate_met_calories(0, 30, 70) == 0.0
    assert ActivityService.calculate_met_calories(8.0, 0, 70) == 0.0
    assert ActivityService.calculate_met_calories(8.0, 30, -5) == 0.0


def test_hydration_target_computation(app):
    """Test weight-based daily hydration target (35 ml / kg, clamped 2000 - 4500 ml)."""
    with app.app_context():
        # 70 kg * 35 = 2450 ml
        target = ActivityService.get_hydration_target(1)
        assert target == 2450

        # High weight clamping (140 kg * 35 = 4900 -> clamped to 4500)
        profile = UserProfile.query.filter_by(user_id=1).first()
        profile.weight_kg = 140.0
        db.session.commit()
        assert ActivityService.get_hydration_target(1) == 4500

        # Low weight clamping (45 kg * 35 = 1575 -> clamped to 2000)
        profile.weight_kg = 45.0
        db.session.commit()
        assert ActivityService.get_hydration_target(1) == 2000


def test_step_kinematics_and_upsert(app):
    """Verify step logging calculates distance and calories, and handles append mode."""
    with app.app_context():
        # Set 6,000 steps
        act = ActivityService.log_steps(user_id=1, steps=6000, append=False)
        assert act.step_count == 6000
        assert act.distance_km == round(6000 * 0.00078, 2)  # 4.68 km
        assert act.calories_burned > 0

        # Append 4,000 steps -> 10,000 total
        act_appended = ActivityService.log_steps(user_id=1, steps=4000, append=True)
        assert act_appended.step_count == 10000
        assert act_appended.distance_km == round(10000 * 0.00078, 2)  # 7.8 km


def test_water_logging_and_deletion(app):
    """Verify logging multiple water entries and deleting specific logs."""
    with app.app_context():
        w1 = ActivityService.log_water(user_id=1, amount_ml=250)
        w2 = ActivityService.log_water(user_id=1, amount_ml=500)

        summary = ActivityService.get_daily_activity_summary(user_id=1)
        assert summary['hydration']['consumed_ml'] == 750
        assert len(summary['hydration']['logs']) == 2

        # Delete w1
        del_success = ActivityService.delete_water_log(user_id=1, log_id=w1.id)
        assert del_success is True

        summary_after = ActivityService.get_daily_activity_summary(user_id=1)
        assert summary_after['hydration']['consumed_ml'] == 500
        assert len(summary_after['hydration']['logs']) == 1


def test_sleep_logging_and_evaluation(app):
    """Verify sleep upsert and clinical restorative assessment."""
    with app.app_context():
        # Sleep Deficit (<6 hours)
        s1 = ActivityService.log_sleep(user_id=1, sleep_hours=5.5, sleep_quality_score=60)
        assert s1.sleep_hours == 5.5
        eval_deficit = ActivityService.get_sleep_evaluation(5.5, 60)
        assert eval_deficit['status'] == 'Sleep Deficit'

        # Update to Optimal Rest (8.0 hours, 90 score)
        s2 = ActivityService.log_sleep(user_id=1, sleep_hours=8.0, sleep_quality_score=90)
        assert s2.id == s1.id  # Same record upserted
        assert s2.sleep_hours == 8.0
        eval_optimal = ActivityService.get_sleep_evaluation(8.0, 90)
        assert eval_optimal['status'] == 'Deep & Restorative'


def test_exercise_logging_and_activity_burn_sync(app):
    """Verify exercise logging computes MET burn and updates ActivityLog total burn."""
    with app.app_context():
        # Initial steps: 5,000 steps
        ActivityService.log_steps(user_id=1, steps=5000)
        act_before = ActivityLog.query.filter_by(user_id=1, log_date=date.today()).first()
        initial_burn = act_before.calories_burned

        # Log 30 min running (jog)
        ex = ActivityService.log_exercise(
            user_id=1,
            exercise_type='running_jog',
            duration_minutes=30
        )
        assert ex.estimated_calories_burned == 294.0

        # Check that ActivityLog.calories_burned increased by 294.0
        act_after = ActivityLog.query.filter_by(user_id=1, log_date=date.today()).first()
        assert act_after.calories_burned == round(initial_burn + 294.0, 1)

        # Delete workout
        del_ok = ActivityService.delete_exercise(user_id=1, exercise_id=ex.id)
        assert del_ok is True

        act_deleted = ActivityLog.query.filter_by(user_id=1, log_date=date.today()).first()
        assert act_deleted.calories_burned == initial_burn


def test_weekly_lifestyle_trends(app):
    """Verify chronological 7-day multi-metric generation."""
    with app.app_context():
        trends = ActivityService.get_weekly_lifestyle_trends(user_id=1, days=7)
        assert len(trends['labels']) == 7
        assert len(trends['steps']) == 7
        assert len(trends['water_ml']) == 7
        assert len(trends['sleep_hours']) == 7
        assert len(trends['active_calories']) == 7


# =============================================================================
# 2. HTTP Routes & REST API Tests
# =============================================================================

def test_activity_hub_page_auth_guard(client):
    """Unauthenticated access must redirect to login."""
    res = client.get('/activity')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']


def test_activity_hub_page_renders(auth_client):
    """Authenticated user can load the activity dashboard view."""
    res = auth_client.get('/activity')
    assert res.status_code == 200
    assert b"Physical Movement, Hydration &amp; Sleep" in res.data or b"Physical Movement, Hydration & Sleep" in res.data
    assert b"Hydration Reservoir" in res.data
    assert b"Step Kinematics" in res.data
    assert b"Circadian Recovery" in res.data
    assert b"Active Caloric Burn" in res.data


def test_api_steps_endpoints(auth_client):
    """Test POST /api/v1/activity/steps."""
    payload = {'steps': 8200, 'mode': 'set'}
    res = auth_client.post('/api/v1/activity/steps', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['data']['step_count'] == 8200


def test_api_water_endpoints(auth_client):
    """Test POST & DELETE /api/v1/activity/water."""
    payload = {'amount_ml': 350}
    res = auth_client.post('/api/v1/activity/water', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    log_id = data['entry']['id']

    # Delete the entry
    del_res = auth_client.delete(f'/api/v1/activity/water/{log_id}')
    assert del_res.status_code == 200
    del_data = del_res.get_json()
    assert del_data['success'] is True


def test_api_sleep_endpoint(auth_client):
    """Test POST /api/v1/activity/sleep."""
    payload = {'sleep_hours': 7.5, 'quality_score': 85}
    res = auth_client.post('/api/v1/activity/sleep', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['sleep']['hours'] == 7.5
    assert data['sleep']['quality_score'] == 85


def test_api_exercise_and_preview_endpoints(auth_client):
    """Test MET preview calculation and exercise session logging/deletion."""
    # Preview endpoint
    prev_res = auth_client.get('/api/v1/activity/met-preview?type=cycling&duration=45')
    assert prev_res.status_code == 200
    prev_data = prev_res.get_json()
    assert prev_data['success'] is True
    assert prev_data['estimated_calories'] > 0

    # Log exercise endpoint
    post_res = auth_client.post('/api/v1/activity/exercise', json={
        'exercise_type': 'cycling',
        'duration_minutes': 45
    })
    assert post_res.status_code == 200
    post_data = post_res.get_json()
    assert post_data['success'] is True
    ex_id = post_data['entry']['id']

    # Delete exercise endpoint
    del_res = auth_client.delete(f'/api/v1/activity/exercise/{ex_id}')
    assert del_res.status_code == 200
    del_data = del_res.get_json()
    assert del_data['success'] is True


def test_api_trends_endpoint(auth_client):
    """Test GET /api/v1/activity/trends."""
    res = auth_client.get('/api/v1/activity/trends?days=7')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['trends']['labels']) == 7
