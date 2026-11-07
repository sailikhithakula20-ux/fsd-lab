"""
Test Suite for Phase 6:
Smart Nutrition & Food Tracking Engine, Proportional Macro Scaling,
and Meal Category Journaling.
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
    FoodCategory,
    FoodItem,
    MealType,
    FoodLog
)
from services import AuthService, NutritionService


@pytest.fixture
def nutrition_setup():
    """Setup clean testing database with seeded categories and dishes."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()

        # Seed meal types
        b_fast = MealType(name='breakfast')
        lunch = MealType(name='lunch')
        snacks = MealType(name='snacks')
        dinner = MealType(name='dinner')
        db.session.add_all([b_fast, lunch, snacks, dinner])

        # Seed categories
        cat_south = FoodCategory(name='Breakfast Specialties', regional_origin='south_india')
        cat_dal = FoodCategory(name='Lentils, Dals & Curries', regional_origin='pan_india')
        db.session.add_all([cat_south, cat_dal])
        db.session.commit()

        # Seed food items
        dosa = FoodItem(
            category_id=cat_south.id,
            food_name='Plain Dosa',
            native_name='Sada Dosa',
            serving_size_grams=90,
            calories=165.0,
            protein_g=3.8,
            carbs_g=29.0,
            fat_g=3.6,
            regional_tag='south_indian',
            is_vegetarian=True,
            is_verified=True
        )
        sambar = FoodItem(
            category_id=cat_dal.id,
            food_name='South Indian Sambar',
            native_name='Sambar',
            serving_size_grams=150,
            calories=115.0,
            protein_g=5.2,
            carbs_g=18.0,
            fat_g=2.8,
            regional_tag='south_indian',
            is_vegetarian=True,
            is_verified=True
        )
        db.session.add_all([dosa, sambar])
        db.session.commit()

        # Register user
        user, _ = AuthService.register_user({
            'email': 'nutrition.test@example.com',
            'full_name': 'Kiran Kumar',
            'password': 'SecurePassword@2026',
            'age': 25,
            'gender': 'male',
            'height_cm': 175.0,
            'weight_kg': 70.0,
            'consent': True
        })

        yield {
            'app': app,
            'user': user,
            'dosa': dosa,
            'sambar': sambar,
            'breakfast': b_fast,
            'lunch': lunch
        }

        db.session.remove()
        db.drop_all()


def test_food_search_queries(nutrition_setup):
    """Verify search filter by query string, category, and regional origin."""
    app = nutrition_setup['app']
    with app.app_context():
        # Search by keyword
        results = NutritionService.search_foods(query='dosa')
        assert len(results) == 1
        assert results[0].food_name == 'Plain Dosa'

        # Search by regional tag
        results = NutritionService.search_foods(regional_tag='south_indian')
        assert len(results) == 2

        # Non-matching keyword
        results = NutritionService.search_foods(query='pizza')
        assert len(results) == 0


def test_meal_logging_with_proportional_scaling(nutrition_setup):
    """Verify exact macronutrient scaling when logging multiple portions."""
    app = nutrition_setup['app']
    user = nutrition_setup['user']
    dosa = nutrition_setup['dosa']
    b_fast = nutrition_setup['breakfast']

    with app.app_context():
        # Log 1.5 portions of Dosa (Base: 165 cal, 3.8g prot, 29g carbs, 3.6g fat)
        # Scaled (1.5x): 247.5 cal, 5.7g prot, 43.5g carbs, 5.4g fat
        log_entry, error = NutritionService.log_meal(
            user_id=user.id,
            food_item_id=dosa.id,
            meal_type_id=b_fast.id,
            quantity_multiplier=1.5,
            log_date=date.today()
        )
        assert error is None
        assert log_entry is not None
        assert log_entry.calculated_calories == 247.5
        assert log_entry.calculated_protein == 5.7
        assert log_entry.calculated_carbs == 43.5
        assert log_entry.calculated_fat == 5.4


def test_meals_organized_by_category(nutrition_setup):
    """Verify meal journaling groups entries into Breakfast, Lunch, etc. with subtotals."""
    app = nutrition_setup['app']
    user = nutrition_setup['user']
    dosa = nutrition_setup['dosa']
    sambar = nutrition_setup['sambar']
    b_fast = nutrition_setup['breakfast']
    lunch = nutrition_setup['lunch']

    with app.app_context():
        # Log Dosa for Breakfast
        NutritionService.log_meal(user.id, dosa.id, b_fast.id, 1.0)
        # Log Sambar for Lunch
        NutritionService.log_meal(user.id, sambar.id, lunch.id, 2.0)

        journal = NutritionService.get_meals_by_category(user.id, date.today())
        assert 'breakfast' in journal
        assert 'lunch' in journal

        # Verify Breakfast subtotals (1 Dosa = 165 cal, 3.8g prot)
        assert len(journal['breakfast']['logs']) == 1
        assert journal['breakfast']['subtotals']['calories'] == 165.0
        assert journal['breakfast']['subtotals']['protein'] == 3.8

        # Verify Lunch subtotals (2 portions Sambar = 230 cal, 10.4g prot)
        assert len(journal['lunch']['logs']) == 1
        assert journal['lunch']['subtotals']['calories'] == 230.0
        assert journal['lunch']['subtotals']['protein'] == 10.4


def test_custom_food_creation(nutrition_setup):
    """Verify users can create homemade/custom food items."""
    app = nutrition_setup['app']
    user = nutrition_setup['user']

    with app.app_context():
        food_data = {
            'food_name': 'Homemade Ragi Malt',
            'native_name': 'Ragi Ganji',
            'calories': 110.0,
            'protein_g': 3.5,
            'carbs_g': 22.0,
            'fat_g': 0.8,
            'serving_unit': '1 glass (200ml)',
            'regional_tag': 'south_indian',
            'is_vegetarian': True
        }
        item, error = NutritionService.create_custom_food(user.id, food_data)
        assert error is None
        assert item is not None
        assert item.food_name == 'Homemade Ragi Malt'
        assert item.calories == 110.0


def test_delete_meal_log(nutrition_setup):
    """Verify meal entries can be deleted safely."""
    app = nutrition_setup['app']
    user = nutrition_setup['user']
    dosa = nutrition_setup['dosa']
    b_fast = nutrition_setup['breakfast']

    with app.app_context():
        log_entry, _ = NutritionService.log_meal(user.id, dosa.id, b_fast.id, 1.0)
        log_id = log_entry.id

        success, err = NutritionService.delete_meal_log(user.id, log_id)
        assert success is True
        assert err is None
        assert FoodLog.query.get(log_id) is None


def test_nutrition_http_endpoints(nutrition_setup):
    """Verify nutrition HTTP views and REST APIs."""
    app = nutrition_setup['app']
    dosa = nutrition_setup['dosa']
    b_fast = nutrition_setup['breakfast']
    client = app.test_client()

    # Log in
    client.post('/login', data={
        'email': 'nutrition.test@example.com',
        'password': 'SecurePassword@2026'
    }, follow_redirects=True)

    # 1. GET /nutrition view
    resp = client.get('/nutrition')
    assert resp.status_code == 200
    assert b"Smart Nutrition Tracker" in resp.data

    # 2. GET /api/v1/nutrition/search
    search_resp = client.get('/api/v1/nutrition/search?q=dosa')
    assert search_resp.status_code == 200
    assert search_resp.json['count'] == 1
    assert search_resp.json['items'][0]['food_name'] == 'Plain Dosa'

    # 3. POST /api/v1/nutrition/log (JSON payload)
    log_resp = client.post('/api/v1/nutrition/log', json={
        'food_item_id': dosa.id,
        'meal_type_id': b_fast.id,
        'quantity_multiplier': 1.0,
        'log_date': date.today().isoformat()
    })
    assert log_resp.status_code == 201
    log_id = log_resp.json['log']['id']

    # 4. DELETE /api/v1/nutrition/log/<id>
    del_resp = client.delete(f'/api/v1/nutrition/log/{log_id}')
    assert del_resp.status_code == 200


if __name__ == '__main__':
    pytest.main(['-v', __file__])
