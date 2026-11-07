"""
AuthService: Business Logic for Authentication, Registration,
Health Profile Management, and Automated Baseline Target Generation.
"""

from models import db, User, UserProfile, NutritionTarget


class AuthService:
    """Encapsulates all authentication and profile calculation logic."""

    ACTIVITY_MULTIPLIERS = {
        'sedentary': 1.20,
        'light': 1.375,
        'moderate': 1.55,
        'active': 1.725,
        'very_active': 1.90
    }

    @classmethod
    def calculate_baseline_targets(cls, weight_kg, height_cm, age, gender, activity_level):
        """
        Calculate daily calorie and macronutrient targets using the Mifflin-St Jeor formula
        and Indian Council of Medical Research (ICMR-NIN) preventive dietary standards.
        """
        w = float(weight_kg)
        h = float(height_cm)
        a = int(age)
        gen = (gender or 'male').lower()
        act = (activity_level or 'sedentary').lower()

        # 1. Basal Metabolic Rate (BMR) via Mifflin-St Jeor Equation
        if gen == 'male':
            bmr = (10.0 * w) + (6.25 * h) - (5.0 * a) + 5.0
        elif gen == 'female':
            bmr = (10.0 * w) + (6.25 * h) - (5.0 * a) - 161.0
        else:
            bmr = (10.0 * w) + (6.25 * h) - (5.0 * a) - 78.0

        # 2. Total Daily Energy Expenditure (TDEE)
        multiplier = cls.ACTIVITY_MULTIPLIERS.get(act, 1.20)
        tdee = round(bmr * multiplier, 1)

        # 3. Preventive Macronutrient Distribution (ICMR-NIN RDA 2020)
        # Protein: 1.0g per kg body weight baseline (scaled slightly with activity)
        protein_multiplier = 1.0 if act in ['sedentary', 'light'] else 1.2
        target_protein = round(w * protein_multiplier, 1)
        protein_calories = target_protein * 4.0

        # Fats: ~25% of total calories (9 kcal/g)
        target_fats = round((tdee * 0.25) / 9.0, 1)
        fat_calories = target_fats * 9.0

        # Carbohydrates: Remaining calories (4 kcal/g)
        carb_calories = max(0, tdee - (protein_calories + fat_calories))
        target_carbs = round(carb_calories / 4.0, 1)

        # Dietary Fiber: Standard preventive target (30g/day)
        target_fiber = 30.0

        # Water: 35 ml per kg body weight
        target_water = round(w * 35.0, 0)

        return {
            'target_calories': tdee,
            'target_protein_g': target_protein,
            'target_carbs_g': target_carbs,
            'target_fats_g': target_fats,
            'target_fiber_g': target_fiber,
            'target_water_ml': target_water
        }

    @classmethod
    def register_user(cls, form_data):
        """
        Creates User, UserProfile, and baseline NutritionTarget in a single atomic transaction.
        """
        try:
            email = form_data['email'].lower().strip()
            full_name = form_data['full_name'].strip()
            password = form_data['password']

            # Create User
            user = User(
                email=email,
                full_name=full_name,
                role='user',
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # Generate user.id

            # Compute BMI
            h_m = float(form_data['height_cm']) / 100.0
            bmi = round(float(form_data['weight_kg']) / (h_m * h_m), 2)

            # Create UserProfile
            profile = UserProfile(
                user_id=user.id,
                age=int(form_data['age']),
                gender=form_data['gender'],
                height_cm=float(form_data['height_cm']),
                weight_kg=float(form_data['weight_kg']),
                bmi=bmi,
                activity_level=form_data.get('activity_level', 'sedentary'),
                dietary_preference=form_data.get('dietary_preference', 'vegetarian'),
                regional_preference=form_data.get('regional_preference', 'south_indian'),
                budget_preference=form_data.get('budget_preference', 'medium'),
                food_allergies=form_data.get('food_allergies', '').strip(),
                data_sharing_consent=bool(form_data.get('consent', True))
            )
            db.session.add(profile)

            # Compute Baseline Targets
            targets_data = cls.calculate_baseline_targets(
                weight_kg=form_data['weight_kg'],
                height_cm=form_data['height_cm'],
                age=form_data['age'],
                gender=form_data['gender'],
                activity_level=form_data.get('activity_level', 'sedentary')
            )

            targets = NutritionTarget(
                user_id=user.id,
                target_calories=targets_data['target_calories'],
                target_protein_g=targets_data['target_protein_g'],
                target_carbs_g=targets_data['target_carbs_g'],
                target_fats_g=targets_data['target_fats_g'],
                target_fiber_g=targets_data['target_fiber_g'],
                target_water_ml=targets_data['target_water_ml'],
                is_custom=False
            )
            db.session.add(targets)

            db.session.commit()
            return user, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @classmethod
    def authenticate_user(cls, email, password):
        """Verify user credentials and active state."""
        user = User.query.filter_by(email=email.lower().strip()).first()
        if user and user.check_password(password) and user.is_active:
            return user
        return None

    @classmethod
    def update_user_profile(cls, user_id, form_data):
        """Update profile details and recompute BMI / non-custom targets."""
        try:
            user = User.query.get(user_id)
            if not user or not user.profile:
                return False, "User profile not found."

            user.full_name = form_data.get('full_name', user.full_name).strip()
            profile = user.profile
            profile.age = int(form_data['age'])
            profile.gender = form_data['gender']
            profile.height_cm = float(form_data['height_cm'])
            profile.weight_kg = float(form_data['weight_kg'])
            profile.activity_level = form_data.get('activity_level', profile.activity_level)
            profile.dietary_preference = form_data.get('dietary_preference', profile.dietary_preference)
            profile.regional_preference = form_data.get('regional_preference', profile.regional_preference)
            profile.food_allergies = form_data.get('food_allergies', '').strip()
            profile.dietary_restrictions = form_data.get('dietary_restrictions', '').strip()

            # Recalculate BMI
            profile.calculate_bmi()

            # If user has not set a custom target override, automatically adjust targets
            targets = user.nutrition_targets
            if targets and not targets.is_custom:
                new_targets = cls.calculate_baseline_targets(
                    weight_kg=profile.weight_kg,
                    height_cm=profile.height_cm,
                    age=profile.age,
                    gender=profile.gender,
                    activity_level=profile.activity_level
                )
                targets.target_calories = new_targets['target_calories']
                targets.target_protein_g = new_targets['target_protein_g']
                targets.target_carbs_g = new_targets['target_carbs_g']
                targets.target_fats_g = new_targets['target_fats_g']
                targets.target_fiber_g = new_targets['target_fiber_g']
                targets.target_water_ml = new_targets['target_water_ml']

            db.session.commit()
            return True, None
        except Exception as e:
            db.session.rollback()
            return False, str(e)

    @classmethod
    def change_password(cls, user, current_password, new_password):
        """Change user password after verifying current credentials."""
        if not user.check_password(current_password):
            return False, "Current password is incorrect."
        user.set_password(new_password)
        db.session.commit()
        return True, None
