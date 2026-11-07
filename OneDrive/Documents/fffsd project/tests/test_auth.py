"""
Integration & Unit Test Suite for Phase 3:
User Registration, Authentication, Session Management, and Health Profile Updates.
"""

import os
import sys
import pytest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db, User, UserProfile, NutritionTarget
from services import AuthService


@pytest.fixture
def app():
    """Create a configured Flask testing app."""
    test_app = create_app('testing')
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


def test_user_registration_service(app):
    """Test AuthService.register_user generates User, Profile, and Baseline Targets."""
    with app.app_context():
        form_data = {
            'email': 'patient.test@example.com',
            'full_name': 'Meera Rao',
            'password': 'SecurePassword@2026',
            'age': 28,
            'gender': 'female',
            'height_cm': 162.0,
            'weight_kg': 58.0,
            'activity_level': 'light',
            'dietary_preference': 'vegetarian',
            'regional_preference': 'south_indian',
            'budget_preference': 'medium',
            'food_allergies': 'peanuts',
            'consent': True
        }

        user, error = AuthService.register_user(form_data)
        assert error is None
        assert user is not None
        assert user.email == 'patient.test@example.com'
        assert user.check_password('SecurePassword@2026') is True

        # Check UserProfile
        profile = UserProfile.query.filter_by(user_id=user.id).first()
        assert profile is not None
        assert profile.age == 28
        assert profile.gender == 'female'
        # BMI = 58 / (1.62^2) = 22.10
        assert round(profile.bmi, 1) == 22.1
        assert profile.get_bmi_category() == "Normal weight"

        # Check Baseline NutritionTarget
        # BMR female = (10 * 58) + (6.25 * 162) - (5 * 28) - 161 = 580 + 1012.5 - 140 - 161 = 1291.5
        # TDEE (light = 1.375) = 1291.5 * 1.375 = 1775.8
        targets = NutritionTarget.query.filter_by(user_id=user.id).first()
        assert targets is not None
        assert targets.target_calories > 1500
        assert targets.target_protein_g >= 58.0  # 1.0g per kg
        assert targets.target_water_ml == 58.0 * 35.0  # 2030 ml


def test_user_authentication_service(app):
    """Test AuthService.authenticate_user credentials verification."""
    with app.app_context():
        form_data = {
            'email': 'rohit@example.com',
            'full_name': 'Rohit Verma',
            'password': 'CorrectPassword123!',
            'age': 32,
            'gender': 'male',
            'height_cm': 178.0,
            'weight_kg': 75.0,
            'activity_level': 'moderate',
            'dietary_preference': 'non_vegetarian',
            'regional_preference': 'pan_india',
            'food_allergies': '',
            'consent': True
        }
        user, _ = AuthService.register_user(form_data)

        # Successful auth
        auth_user = AuthService.authenticate_user('rohit@example.com', 'CorrectPassword123!')
        assert auth_user is not None
        assert auth_user.id == user.id

        # Failed auth (wrong password)
        failed_auth = AuthService.authenticate_user('rohit@example.com', 'WrongPassword!')
        assert failed_auth is None

        # Failed auth (non-existent email)
        no_user = AuthService.authenticate_user('unknown@example.com', 'CorrectPassword123!')
        assert no_user is None


def test_profile_update_and_target_recalculation(app):
    """Test updating profile parameters recalculates BMI and baseline targets."""
    with app.app_context():
        form_data = {
            'email': 'update.test@example.com',
            'full_name': 'Kavya Nair',
            'password': 'Password1234',
            'age': 25,
            'gender': 'female',
            'height_cm': 160.0,
            'weight_kg': 55.0,
            'activity_level': 'sedentary',
            'consent': True
        }
        user, _ = AuthService.register_user(form_data)
        initial_calories = user.nutrition_targets.target_calories

        # Update weight and activity level
        update_data = {
            'full_name': 'Kavya Nair',
            'age': 25,
            'gender': 'female',
            'height_cm': 160.0,
            'weight_kg': 65.0,  # +10 kg weight change
            'activity_level': 'active',  # increased activity
            'dietary_preference': 'vegetarian',
            'regional_preference': 'south_indian',
            'food_allergies': 'dairy',
            'dietary_restrictions': 'low_sodium'
        }
        success, error = AuthService.update_user_profile(user.id, update_data)
        assert success is True
        assert error is None

        # Re-fetch user
        updated_user = User.query.get(user.id)
        assert updated_user.profile.weight_kg == 65.0
        # New BMI = 65 / (1.60^2) = 25.39 (Overweight)
        assert round(updated_user.profile.bmi, 2) == 25.39
        assert updated_user.profile.get_bmi_category() == "Overweight"
        assert updated_user.profile.food_allergies == 'dairy'

        # Target calories should increase due to higher weight and activity multiplier
        assert updated_user.nutrition_targets.target_calories > initial_calories


def test_password_change(app):
    """Test password update mechanism with verification."""
    with app.app_context():
        form_data = {
            'email': 'pass.test@example.com',
            'full_name': 'Vikram Singh',
            'password': 'InitialPassword123!',
            'age': 30,
            'gender': 'male',
            'height_cm': 175.0,
            'weight_kg': 70.0,
            'consent': True
        }
        user, _ = AuthService.register_user(form_data)

        # Try changing password with wrong current password
        success, err = AuthService.change_password(user, 'WrongOldPass!', 'NewPassword2026!')
        assert success is False
        assert "incorrect" in err

        # Change with correct current password
        success, err = AuthService.change_password(user, 'InitialPassword123!', 'NewPassword2026!')
        assert success is True
        assert err is None

        # Verify new password works
        assert user.check_password('NewPassword2026!') is True
        assert user.check_password('InitialPassword123!') is False


def test_auth_http_endpoints(client):
    """Test HTTP views and protected route enforcement."""
    # Unauthenticated GET /profile redirects to login
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    # Unauthenticated GET /logout redirects to login
    response = client.get('/logout', follow_redirects=False)
    assert response.status_code == 302
    assert '/login' in response.headers['Location']

    # GET /login returns 200
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Sign In" in response.data

    # GET /register returns 200
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Preventive Health Onboarding" in response.data

    # API Auth status endpoint
    response = client.get('/api/v1/auth/status')
    assert response.status_code == 200
    assert response.json['authenticated'] is False


if __name__ == '__main__':
    pytest.main(['-v', __file__])
