"""
Test Suite for Phase 7:
Personalized Food Recommendation Engine (Dynamic Deficit-Filling,
Allergy Exclusion, Cultural Adaptability, and One-Click Acceptance).
"""

import os
import sys
from datetime import date
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
    Recommendation
)
from services import AuthService, RecommendationService


@pytest.fixture
def reco_setup():
    """Setup clean testing database with seeded dishes across categories and allergies."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        # Seed meal types
        b_fast = MealType(name='breakfast')
        lunch = MealType(name='lunch')
        db.session.add_all([b_fast, lunch])

        # Seed categories
        cat1 = FoodCategory(name='Breakfast Specialties', regional_origin='south_india')
        cat2 = FoodCategory(name='Vegetable Curries & Sabzis', regional_origin='pan_india')
        cat3 = FoodCategory(name='Poultry, Seafood & Eggs', regional_origin='pan_india')
        db.session.add_all([cat1, cat2, cat3])
        db.session.commit()

        # Dish A: Poha (contains peanuts)
        poha = FoodItem(
            category_id=cat1.id,
            food_name='Poha with Peanuts',
            calories=230.0,
            protein_g=5.2,
            carbs_g=38.0,
            fat_g=6.8,
            allergen_tags='peanuts',
            regional_tag='pan_india',
            is_vegetarian=True,
            is_verified=True
        )

        # Dish B: High-Protein Soya Chunks Curry (Vegetarian, no peanuts, high protein)
        soya = FoodItem(
            category_id=cat2.id,
            food_name='Soya Chunks Curry',
            calories=210.0,
            protein_g=18.5,
            carbs_g=16.0,
            fat_g=7.5,
            allergen_tags='soy',
            regional_tag='south_indian',
            is_vegetarian=True,
            is_verified=True
        )

        # Dish C: Chicken Curry (Non-Vegetarian)
        chicken = FoodItem(
            category_id=cat3.id,
            food_name='South Indian Chicken Curry',
            calories=260.0,
            protein_g=24.5,
            carbs_g=6.5,
            fat_g=15.2,
            allergen_tags='',
            regional_tag='south_indian',
            is_vegetarian=False,
            is_verified=True
        )

        db.session.add_all([poha, soya, chicken])
        db.session.commit()

        # User A: Vegetarian patient with Peanut allergy
        user_veg_allergic, _ = AuthService.register_user({
            'email': 'veg.allergy@example.com',
            'full_name': 'Pooja Iyer',
            'password': 'SecurePassword@2026',
            'age': 24,
            'gender': 'female',
            'height_cm': 160.0,
            'weight_kg': 55.0,
            'dietary_preference': 'vegetarian',
            'regional_preference': 'south_indian',
            'food_allergies': 'peanuts',
            'consent': True
        })

        yield {
            'app': app,
            'user': user_veg_allergic,
            'poha': poha,
            'soya': soya,
            'chicken': chicken,
            'lunch': lunch
        }

        db.session.remove()
        db.drop_all()


def test_strict_allergy_exclusion_constraint(reco_setup):
    """Verify foods containing allergic ingredients are 100% excluded from recommendations."""
    app = reco_setup['app']
    user = reco_setup['user']

    with app.app_context():
        # User has peanut allergy
        recommendations = RecommendationService.generate_recommendations(user.id, meal_time='breakfast')
        reco_names = [r['food_item']['food_name'] for r in recommendations]

        # Poha contains peanuts; it must never appear
        assert 'Poha with Peanuts' not in reco_names


def test_strict_dietary_preference_constraint(reco_setup):
    """Verify vegetarian users are never recommended non-vegetarian dishes."""
    app = reco_setup['app']
    user = reco_setup['user']

    with app.app_context():
        recommendations = RecommendationService.generate_recommendations(user.id, meal_time='lunch')
        reco_names = [r['food_item']['food_name'] for r in recommendations]

        # User is vegetarian; Chicken Curry must never appear
        assert 'South Indian Chicken Curry' not in reco_names
        # Soya Curry is vegetarian and non-peanut; it should be recommended
        assert 'Soya Chunks Curry' in reco_names


def test_protein_deficit_scoring_boost(reco_setup):
    """Verify high-protein foods receive prioritized match scores when protein deficit is high."""
    app = reco_setup['app']
    user = reco_setup['user']

    with app.app_context():
        recommendations = RecommendationService.generate_recommendations(user.id, meal_time='lunch')
        assert len(recommendations) > 0

        top_reco = recommendations[0]
        assert top_reco['food_item']['food_name'] == 'Soya Chunks Curry'
        assert top_reco['match_score'] >= 0.70
        assert "protein" in top_reco['recommendation_reason'].lower()


def test_accept_recommendation_and_auto_logging(reco_setup):
    """Verify accepting a recommendation marks it accepted and creates a FoodLog entry."""
    app = reco_setup['app']
    user = reco_setup['user']

    with app.app_context():
        recommendations = RecommendationService.generate_recommendations(user.id, meal_time='lunch')
        reco_id = recommendations[0]['id']

        # Accept recommendation
        food_log, err = RecommendationService.accept_recommendation(user.id, reco_id)
        assert err is None
        assert food_log is not None
        assert food_log.food_item.food_name == 'Soya Chunks Curry'
        assert food_log.calculated_protein == 18.5

        # Check Recommendation state in DB
        reco_in_db = Recommendation.query.get(reco_id)
        assert reco_in_db.is_accepted is True


def test_recommendation_http_endpoints(reco_setup):
    """Verify HTTP views and REST APIs for recommendation engine."""
    app = reco_setup['app']
    client = app.test_client()

    # Log in
    client.post('/login', data={
        'email': 'veg.allergy@example.com',
        'password': 'SecurePassword@2026'
    }, follow_redirects=True)

    # 1. GET /recommendations view
    resp = client.get('/recommendations?meal_time=lunch')
    assert resp.status_code == 200
    assert b"Personalized Food Recommendations" in resp.data

    # 2. GET /api/v1/recommendations/daily REST API
    api_resp = client.get('/api/v1/recommendations/daily?meal_time=lunch')
    assert api_resp.status_code == 200
    json_data = api_resp.json
    assert json_data['status'] == 'success'
    assert len(json_data['recommendations']) > 0

    reco_id = json_data['recommendations'][0]['id']

    # 3. POST /api/v1/recommendations/accept/<id>
    accept_resp = client.post(f'/api/v1/recommendations/accept/{reco_id}', follow_redirects=False)
    assert accept_resp.status_code == 302  # Form redirect to /nutrition


if __name__ == '__main__':
    pytest.main(['-v', __file__])
