"""
Test Suite for Phase 5:
Personalized Health Dashboard, Daily Aggregations, 7-Day Time Series, and Clinical Insights.
"""

import os
import sys
from datetime import date, timedelta
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import (
    db,
    User,
    UserProfile,
    NutritionTarget,
    FoodCategory,
    FoodItem,
    MealType,
    FoodLog,
    WaterLog,
    ActivityLog,
    SleepLog
)
from services import AuthService, DashboardService


@pytest.fixture
def test_setup():
    """Create Flask testing app and seed a test patient."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        # Seed meal types & category
        breakfast = MealType(name='breakfast')
        lunch = MealType(name='lunch')
        db.session.add_all([breakfast, lunch])

        cat = FoodCategory(name='Breakfast Specialties', regional_origin='south_india')
        db.session.add(cat)
        db.session.commit()

        # Seed a food item: Idli (100g, 130 kcal, 4.5g protein, 26.5g carbs, 0.4g fat)
        idli = FoodItem(
            category_id=cat.id,
            food_name='Steamed Idli',
            serving_size_grams=100,
            calories=130.0,
            protein_g=4.5,
            carbs_g=26.5,
            fat_g=0.4
        )
        db.session.add(idli)
        db.session.commit()

        # Register a test patient
        user, _ = AuthService.register_user({
            'email': 'dashboard.user@example.com',
            'full_name': 'Ananya Sen',
            'password': 'SecurePassword@2026',
            'age': 26,
            'gender': 'female',
            'height_cm': 165.0,
            'weight_kg': 60.0,
            'activity_level': 'sedentary',
            'dietary_preference': 'vegetarian',
            'consent': True
        })

        yield {
            'app': app,
            'user': user,
            'food_item': idli,
            'meal_type': breakfast
        }

        db.session.remove()
        db.drop_all()


def test_dashboard_daily_summary_empty(test_setup):
    """Verify daily summary returns zeroed consumption with intact targets when no logs exist."""
    app = test_setup['app']
    user = test_setup['user']

    with app.app_context():
        summary = DashboardService.get_daily_summary(user.id)
        assert summary is not None
        assert summary['nutrition']['calories']['consumed'] == 0.0
        assert summary['nutrition']['calories']['remaining'] > 1200
        assert summary['hydration']['consumed_ml'] == 0
        assert summary['activity']['steps'] == 0


def test_dashboard_daily_summary_with_consumption(test_setup):
    """Verify daily summary aggregates multiple meals and water logs correctly."""
    app = test_setup['app']
    user = test_setup['user']
    food = test_setup['food_item']
    meal = test_setup['meal_type']

    with app.app_context():
        today = date.today()

        # Log 2 portions of Idli (260 kcal, 9g protein, 53g carbs, 0.8g fat)
        log1 = FoodLog(
            user_id=user.id,
            food_item_id=food.id,
            meal_type_id=meal.id,
            log_date=today,
            quantity_multiplier=2.0,
            calculated_calories=260.0,
            calculated_protein=9.0,
            calculated_carbs=53.0,
            calculated_fat=0.8
        )
        # Log 500ml water
        water1 = WaterLog(user_id=user.id, log_date=today, amount_ml=500)

        # Log 4500 steps
        act1 = ActivityLog(user_id=user.id, log_date=today, step_count=4500, calories_burned=180.0)

        db.session.add_all([log1, water1, act1])
        db.session.commit()

        summary = DashboardService.get_daily_summary(user.id, today)
        assert summary['nutrition']['calories']['consumed'] == 260.0
        assert summary['nutrition']['protein']['consumed'] == 9.0
        assert summary['hydration']['consumed_ml'] == 500
        assert summary['activity']['steps'] == 4500
        assert len(summary['recent_meals']) == 1


def test_seven_day_trends_structure(test_setup):
    """Verify 7-day trend arrays match expected 7 date labels and format."""
    app = test_setup['app']
    user = test_setup['user']

    with app.app_context():
        trends = DashboardService.get_seven_day_trends(user.id)
        assert len(trends['labels']) == 7
        assert len(trends['calories']) == 7
        assert len(trends['protein']) == 7
        assert len(trends['water_ml']) == 7
        assert len(trends['steps']) == 7
        assert len(trends['sleep_hours']) == 7
        assert len(trends['target_calories_line']) == 7


def test_personalized_insights_generation(test_setup):
    """Verify clinical rule engine triggers protein gap and lifestyle insights."""
    app = test_setup['app']
    user = test_setup['user']

    with app.app_context():
        # New user with no logs triggers onboarding insight
        insights = DashboardService.generate_personalized_insights(user.id)
        assert len(insights) > 0
        assert any("Baseline Profile Active" in ins['title'] for ins in insights)

        # Add low sleep logs (<6.0 hours) across the week
        today = date.today()
        for i in range(7):
            d = today - timedelta(days=i)
            slp = SleepLog(user_id=user.id, log_date=d, sleep_hours=5.0, sleep_quality_score=60)
            db.session.add(slp)
        db.session.commit()

        updated_insights = DashboardService.generate_personalized_insights(user.id)
        # Should now contain the chronic sleep restriction warning
        sleep_warnings = [ins for ins in updated_insights if "Sleep" in ins['category']]
        assert len(sleep_warnings) > 0
        assert "Sleep Restriction" in sleep_warnings[0]['title']


def test_dashboard_http_endpoints(test_setup):
    """Verify protected HTTP view and REST API endpoints."""
    app = test_setup['app']
    user = test_setup['user']
    client = app.test_client()

    # 1. Unauthenticated request to /dashboard redirects to login
    resp = client.get('/dashboard')
    assert resp.status_code == 302
    assert '/login' in resp.headers['Location']

    # 2. Authenticated request to /dashboard succeeds
    client.post('/login', data={
        'email': 'dashboard.user@example.com',
        'password': 'SecurePassword@2026'
    }, follow_redirects=True)

    resp = client.get('/dashboard')
    assert resp.status_code == 200
    assert b"Welcome back, Ananya" in resp.data
    assert b"Daily Calories" in resp.data

    # 3. Authenticated REST API call
    api_resp = client.get('/api/v1/dashboard/summary')
    assert api_resp.status_code == 200
    json_data = api_resp.json
    assert json_data['status'] == 'success'
    assert 'summary' in json_data
    assert 'trends' in json_data
    assert 'insights' in json_data


if __name__ == '__main__':
    pytest.main(['-v', __file__])
