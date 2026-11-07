"""
Unit and Integration Test Script for Phase 2: Database Initialization & Relational Integrity
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import TestingConfig
from models import (
    db,
    User,
    UserProfile,
    AdminUser,
    FoodCategory,
    FoodItem,
    MealType,
    FoodLog,
    NutritionTarget,
    ActivityLog,
    WaterLog,
    SleepLog
)
from database.seed_data import seed_database


@pytest.fixture
def test_app():
    """Create and configure a clean testing application with in-memory database."""
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database(app)
        yield app
        db.session.remove()
        db.drop_all()


def test_seed_data_counts(test_app):
    """Verify standard seeds are properly populated in the database."""
    with test_app.app_context():
        # Verify 4 meal types
        assert MealType.query.count() == 4
        assert [m.name for m in MealType.query.all()] == ['breakfast', 'lunch', 'snacks', 'dinner']

        # Verify 8 food categories
        assert FoodCategory.query.count() == 8

        # Verify food items seeded
        foods_count = FoodItem.query.count()
        assert foods_count >= 25, f"Expected at least 25 food items, got {foods_count}"

        # Verify Admin user
        admin = AdminUser.query.filter_by(username='system_admin').first()
        assert admin is not None
        assert admin.check_password('Admin@12345') is True


def test_food_macro_scaling(test_app):
    """Verify accurate nutritional scaling when a user logs multiple portions."""
    with test_app.app_context():
        idli = FoodItem.query.filter(FoodItem.food_name.like('%Idli%')).first()
        assert idli is not None

        # Base portion is 100g = 130 cal, 4.5g protein
        single_portion = idli.calculate_macros_for_quantity(1.0)
        assert single_portion['calories'] == 130.0
        assert single_portion['protein'] == 4.5

        # 2.5 portions
        double_portion = idli.calculate_macros_for_quantity(2.5)
        assert double_portion['calories'] == 325.0
        assert double_portion['protein'] == 11.2


def test_allergen_detection(test_app):
    """Verify allergic foods are detected based on user allergies."""
    with test_app.app_context():
        poha = FoodItem.query.filter(FoodItem.food_name.like('%Poha%')).first()
        assert poha is not None
        assert poha.has_allergen(['peanuts']) is True
        assert poha.has_allergen(['gluten']) is False


def test_user_creation_and_cascade(test_app):
    """Verify user registration, profile computation, and cascading deletes."""
    with test_app.app_context():
        user = User(
            email='student.test@example.com',
            full_name='Aarav Sharma',
            role='user'
        )
        user.set_password('SecurePass@2026')
        db.session.add(user)
        db.session.commit()

        # Check password hashing
        assert user.check_password('SecurePass@2026') is True
        assert user.check_password('WrongPass') is False

        # Add profile
        profile = UserProfile(
            user_id=user.id,
            age=22,
            gender='male',
            height_cm=175.0,
            weight_kg=70.0,
            activity_level='moderate',
            dietary_preference='vegetarian',
            regional_preference='south_indian'
        )
        bmi = profile.calculate_bmi()
        assert bmi == 22.86  # 70 / (1.75^2)
        assert profile.get_bmi_category() == "Normal weight"
        db.session.add(profile)

        # Add Nutrition targets
        targets = NutritionTarget(
            user_id=user.id,
            target_calories=2150.0,
            target_protein_g=75.0,
            target_carbs_g=280.0,
            target_fats_g=65.0
        )
        db.session.add(targets)
        db.session.commit()

        # Verify relationships
        retrieved_user = User.query.filter_by(email='student.test@example.com').first()
        assert retrieved_user.profile.age == 22
        assert retrieved_user.nutrition_targets.target_calories == 2150.0

        # Test Cascade Delete
        db.session.delete(retrieved_user)
        db.session.commit()

        # Ensure user profile and targets are removed automatically
        assert UserProfile.query.filter_by(user_id=user.id).first() is None
        assert NutritionTarget.query.filter_by(user_id=user.id).first() is None


if __name__ == '__main__':
    pytest.main(['-v', __file__])
