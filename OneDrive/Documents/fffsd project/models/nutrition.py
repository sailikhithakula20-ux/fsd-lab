from datetime import datetime, date
from models import db


class FoodCategory(db.Model):
    """Categorization of foods (Grains, Dals, Breakfast, etc.)."""
    __tablename__ = 'food_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    regional_origin = db.Column(db.String(50), default='pan_india')

    items = db.relationship('FoodItem', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'regional_origin': self.regional_origin
        }

    def __repr__(self):
        return f"<FoodCategory id={self.id} name='{self.name}'>"


class FoodItem(db.Model):
    """Nutritional profile of individual food items (per 100g base or standard serving)."""
    __tablename__ = 'food_items'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('food_categories.id'), nullable=False)
    
    food_name = db.Column(db.String(120), nullable=False, index=True)
    native_name = db.Column(db.String(120), nullable=True)  # e.g., 'Ragi Mudde', 'Masala Dosa'
    serving_unit = db.Column(db.String(50), default='100g', nullable=False)
    serving_size_grams = db.Column(db.Float, default=100.0, nullable=False)
    
    # Nutritional values normalized to standard serving size
    calories = db.Column(db.Float, nullable=False)
    protein_g = db.Column(db.Float, default=0.0, nullable=False)
    carbs_g = db.Column(db.Float, default=0.0, nullable=False)
    fat_g = db.Column(db.Float, default=0.0, nullable=False)
    fiber_g = db.Column(db.Float, default=0.0, nullable=False)
    sugar_g = db.Column(db.Float, default=0.0, nullable=False)
    sodium_mg = db.Column(db.Float, default=0.0, nullable=False)
    potassium_mg = db.Column(db.Float, default=0.0, nullable=False)

    # Classification & Dietary Tags
    regional_tag = db.Column(db.String(50), default='south_indian', index=True)
    is_vegetarian = db.Column(db.Boolean, default=True, nullable=False)
    is_vegan = db.Column(db.Boolean, default=False, nullable=False)
    allergen_tags = db.Column(db.String(255), default='')  # e.g. "dairy, gluten, nuts"
    is_verified = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    logs = db.relationship('FoodLog', backref='food_item', lazy='dynamic')
    recommendations = db.relationship('Recommendation', backref='food_item', lazy='dynamic')

    def calculate_macros_for_quantity(self, quantity_multiplier=1.0):
        """Calculate exact nutritional values for a given serving multiplier."""
        mult = float(quantity_multiplier)
        return {
            'calories': round(self.calories * mult, 1),
            'protein': round(self.protein_g * mult, 1),
            'carbs': round(self.carbs_g * mult, 1),
            'fat': round(self.fat_g * mult, 1),
            'fiber': round(self.fiber_g * mult, 1),
            'sugar': round(self.sugar_g * mult, 1),
            'sodium': round(self.sodium_mg * mult, 1),
            'potassium': round(self.potassium_mg * mult, 1),
            'grams': round(self.serving_size_grams * mult, 1)
        }

    def has_allergen(self, allergen_list):
        """Check if food item contains any allergens from user's allergy list."""
        if not self.allergen_tags or not allergen_list:
            return False
        item_allergens = [a.strip().lower() for a in self.allergen_tags.split(',') if a.strip()]
        for user_allergy in allergen_list:
            if user_allergy.strip().lower() in item_allergens:
                return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'category_id': self.category_id,
            'food_name': self.food_name,
            'native_name': self.native_name,
            'serving_unit': self.serving_unit,
            'serving_size_grams': self.serving_size_grams,
            'calories': self.calories,
            'protein_g': self.protein_g,
            'carbs_g': self.carbs_g,
            'fat_g': self.fat_g,
            'fiber_g': self.fiber_g,
            'sugar_g': self.sugar_g,
            'regional_tag': self.regional_tag,
            'is_vegetarian': self.is_vegetarian,
            'is_vegan': self.is_vegan,
            'allergen_tags': [a.strip() for a in self.allergen_tags.split(',') if a.strip()] if self.allergen_tags else []
        }

    def __repr__(self):
        return f"<FoodItem id={self.id} name='{self.food_name}' cal={self.calories}>"


class MealType(db.Model):
    """Standard meal categorization (Breakfast, Lunch, Snacks, Dinner)."""
    __tablename__ = 'meal_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)  # breakfast, lunch, snacks, dinner

    logs = db.relationship('FoodLog', backref='meal_type', lazy='dynamic')

    def to_dict(self):
        return {'id': self.id, 'name': self.name}

    def __repr__(self):
        return f"<MealType id={self.id} name='{self.name}'>"


class FoodLog(db.Model):
    """Daily consumption record of a specific food item by a user."""
    __tablename__ = 'food_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    meal_type_id = db.Column(db.Integer, db.ForeignKey('meal_types.id'), nullable=False)
    
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    quantity_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    
    # Pre-calculated macronutrients for analytical query performance
    calculated_calories = db.Column(db.Float, nullable=False)
    calculated_protein = db.Column(db.Float, nullable=False)
    calculated_carbs = db.Column(db.Float, nullable=False)
    calculated_fat = db.Column(db.Float, nullable=False)
    
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.Index('idx_user_log_date', 'user_id', 'log_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'food_item': self.food_item.to_dict() if self.food_item else None,
            'meal_type': self.meal_type.name if self.meal_type else None,
            'log_date': self.log_date.isoformat(),
            'quantity_multiplier': self.quantity_multiplier,
            'calories': self.calculated_calories,
            'protein': self.calculated_protein,
            'carbs': self.calculated_carbs,
            'fat': self.calculated_fat,
            'logged_at': self.logged_at.isoformat()
        }

    def __repr__(self):
        return f"<FoodLog id={self.id} user_id={self.user_id} date={self.log_date} cal={self.calculated_calories}>"


class NutritionTarget(db.Model):
    """Daily nutritional and calorie goals for a user."""
    __tablename__ = 'nutrition_targets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    target_calories = db.Column(db.Float, default=2000.0, nullable=False)
    target_protein_g = db.Column(db.Float, default=60.0, nullable=False)
    target_carbs_g = db.Column(db.Float, default=250.0, nullable=False)
    target_fats_g = db.Column(db.Float, default=65.0, nullable=False)
    target_fiber_g = db.Column(db.Float, default=30.0, nullable=False)
    target_water_ml = db.Column(db.Float, default=2500.0, nullable=False)
    
    is_custom = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'calories': self.target_calories,
            'protein_g': self.target_protein_g,
            'carbs_g': self.target_carbs_g,
            'fats_g': self.target_fats_g,
            'fiber_g': self.target_fiber_g,
            'water_ml': self.target_water_ml,
            'is_custom': self.is_custom
        }

    def __repr__(self):
        return f"<NutritionTarget user_id={self.user_id} cal={self.target_calories}>"


class Recommendation(db.Model):
    """Food recommendation generated for filling real-time user nutritional deficits."""
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_items.id'), nullable=False)
    
    recommendation_date = db.Column(db.Date, default=date.today, nullable=False)
    meal_time = db.Column(db.String(30), default='lunch')  # breakfast, lunch, snacks, dinner
    match_score = db.Column(db.Float, default=0.0)  # 0.0 to 1.0 ranking
    
    recommendation_reason = db.Column(db.String(255), nullable=False)
    clinical_justification = db.Column(db.Text, nullable=True)
    is_accepted = db.Column(db.Boolean, default=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'food_item': self.food_item.to_dict() if self.food_item else None,
            'meal_time': self.meal_time,
            'match_score': self.match_score,
            'recommendation_reason': self.recommendation_reason,
            'clinical_justification': self.clinical_justification,
            'is_accepted': self.is_accepted,
            'generated_at': self.generated_at.isoformat()
        }

    def __repr__(self):
        return f"<Recommendation user_id={self.user_id} food_id={self.food_item_id} score={self.match_score}>"
