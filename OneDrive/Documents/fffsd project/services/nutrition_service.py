"""
NutritionService: Business Logic for Food Database Search, Proportional
Nutrient Calculation, Meal Logging by Type, and Custom Food Ingestion.
"""

from datetime import date
from sqlalchemy import or_
from models import (
    db,
    FoodItem,
    FoodCategory,
    MealType,
    FoodLog
)


class NutritionService:
    """Manages food search, portion scaling, meal logging, and meal grouping."""

    @classmethod
    def search_foods(cls, query='', category_id=None, regional_tag=None, is_vegetarian=None, limit=30):
        """
        Search food database by name, category, regional origin, or dietary filter.
        """
        query_filter = FoodItem.query.filter(FoodItem.is_verified == True)

        if query and query.strip():
            search_term = f"%{query.strip().lower()}%"
            query_filter = query_filter.filter(
                or_(
                    FoodItem.food_name.ilike(search_term),
                    FoodItem.native_name.ilike(search_term),
                    FoodItem.allergen_tags.ilike(search_term)
                )
            )

        if category_id:
            query_filter = query_filter.filter(FoodItem.category_id == category_id)

        if regional_tag:
            query_filter = query_filter.filter(FoodItem.regional_tag == regional_tag)

        if is_vegetarian is not None:
            query_filter = query_filter.filter(FoodItem.is_vegetarian == is_vegetarian)

        return query_filter.order_by(FoodItem.food_name.asc()).limit(limit).all()

    @classmethod
    def log_meal(cls, user_id, food_item_id, meal_type_id, quantity_multiplier=1.0, log_date=None):
        """
        Log a food item for a specific meal, accurately scaling macronutrients.
        """
        if log_date is None:
            log_date = date.today()

        food = FoodItem.query.get(food_item_id)
        if not food:
            return None, "Food item not found."

        meal = MealType.query.get(meal_type_id)
        if not meal:
            return None, "Invalid meal type specified."

        mult = max(0.1, float(quantity_multiplier))

        # Calculate exact scaled values
        scaled_calories = round(food.calories * mult, 1)
        scaled_protein = round(food.protein_g * mult, 1)
        scaled_carbs = round(food.carbs_g * mult, 1)
        scaled_fat = round(food.fat_g * mult, 1)

        food_log = FoodLog(
            user_id=user_id,
            food_item_id=food_item_id,
            meal_type_id=meal_type_id,
            log_date=log_date,
            quantity_multiplier=mult,
            calculated_calories=scaled_calories,
            calculated_protein=scaled_protein,
            calculated_carbs=scaled_carbs,
            calculated_fat=scaled_fat
        )

        db.session.add(food_log)
        db.session.commit()

        return food_log, None

    @classmethod
    def delete_meal_log(cls, user_id, log_id):
        """Delete an existing food log owned by the user."""
        log = FoodLog.query.filter_by(id=log_id, user_id=user_id).first()
        if not log:
            return False, "Food log record not found or unauthorized."

        db.session.delete(log)
        db.session.commit()
        return True, None

    @classmethod
    def get_meals_by_category(cls, user_id, target_date=None):
        """
        Returns today's logged meals structured by standard meal types:
        Breakfast, Lunch, Snacks, Dinner, along with subtotals.
        """
        if target_date is None:
            target_date = date.today()

        meal_types = MealType.query.order_by(MealType.id.asc()).all()
        organized_meals = {}

        for mt in meal_types:
            logs = FoodLog.query.filter_by(
                user_id=user_id,
                meal_type_id=mt.id,
                log_date=target_date
            ).order_by(FoodLog.logged_at.asc()).all()

            subtotal_calories = round(sum(l.calculated_calories for l in logs), 1)
            subtotal_protein = round(sum(l.calculated_protein for l in logs), 1)
            subtotal_carbs = round(sum(l.calculated_carbs for l in logs), 1)
            subtotal_fat = round(sum(l.calculated_fat for l in logs), 1)

            organized_meals[mt.name] = {
                'meal_type_id': mt.id,
                'meal_name': mt.name.capitalize(),
                'logs': [l.to_dict() for l in logs],
                'subtotals': {
                    'calories': subtotal_calories,
                    'protein': subtotal_protein,
                    'carbs': subtotal_carbs,
                    'fat': subtotal_fat
                }
            }

        return organized_meals

    @classmethod
    def create_custom_food(cls, user_id, food_data):
        """
        Allow a user to register a custom or homemade food item into the database.
        """
        try:
            category_id = int(food_data.get('category_id', 1))
            food_name = food_data['food_name'].strip()
            calories = float(food_data['calories'])
            protein_g = float(food_data.get('protein_g', 0.0))
            carbs_g = float(food_data.get('carbs_g', 0.0))
            fat_g = float(food_data.get('fat_g', 0.0))
            fiber_g = float(food_data.get('fiber_g', 0.0))
            serving_size_grams = float(food_data.get('serving_size_grams', 100.0))
            serving_unit = food_data.get('serving_unit', '100g')
            regional_tag = food_data.get('regional_tag', 'south_indian')
            is_vegetarian = bool(food_data.get('is_vegetarian', True))

            custom_item = FoodItem(
                category_id=category_id,
                food_name=food_name,
                native_name=food_data.get('native_name', ''),
                serving_unit=serving_unit,
                serving_size_grams=serving_size_grams,
                calories=calories,
                protein_g=protein_g,
                carbs_g=carbs_g,
                fat_g=fat_g,
                fiber_g=fiber_g,
                regional_tag=regional_tag,
                is_vegetarian=is_vegetarian,
                is_verified=True
            )

            db.session.add(custom_item)
            db.session.commit()
            return custom_item, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)
