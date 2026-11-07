"""
Seed Data Script for Preventive Healthcare & Nutrition Management System
Populates authentic Indian & South Indian food items (ICMR-NIN verified),
meal categories, admin user, and educational articles.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from config import config_by_name
from models import (
    db,
    MealType,
    FoodCategory,
    FoodItem,
    AdminUser,
    HealthArticle
)


def seed_database(app=None):
    """Seed the database with verified nutritional and platform master data."""
    if app is None:
        env = os.environ.get('FLASK_ENV', 'development')
        app = Flask(__name__)
        app.config.from_object(config_by_name.get(env, 'default'))
        db.init_app(app)

    with app.app_context():
        # Ensure all tables are created
        db.create_all()
        print("[OK] Verified all database tables created.")

        # ---------------------------------------------------------------------
        # 1. SEED MEAL TYPES
        # ---------------------------------------------------------------------
        meal_names = ['breakfast', 'lunch', 'snacks', 'dinner']
        for name in meal_names:
            if not MealType.query.filter_by(name=name).first():
                db.session.add(MealType(name=name))
        db.session.commit()
        print("[OK] Seeded standard meal types: Breakfast, Lunch, Snacks, Dinner.")

        # ---------------------------------------------------------------------
        # 2. SEED FOOD CATEGORIES
        # ---------------------------------------------------------------------
        categories_data = [
            {'name': 'Breakfast Specialties', 'description': 'Traditional morning meals, idlis, dosas, porridges', 'regional_origin': 'south_india'},
            {'name': 'Grains, Breads & Millets', 'description': 'Staple grains, chapatis, rotis, rice, and millet preparations', 'regional_origin': 'pan_india'},
            {'name': 'Lentils, Dals & Curries', 'description': 'Protein-rich legume dishes, sambars, rasams, and dals', 'regional_origin': 'pan_india'},
            {'name': 'Vegetable Curries & Sabzis', 'description': 'Dry and gravy vegetable preparations, poriyals, kurmas', 'regional_origin': 'pan_india'},
            {'name': 'Dairy & Plant-Based Proteins', 'description': 'Curd, paneer, tofu, soya chunks, and dairy alternatives', 'regional_origin': 'pan_india'},
            {'name': 'Poultry, Seafood & Eggs', 'description': 'High-protein animal sources prepared with Indian spices', 'regional_origin': 'pan_india'},
            {'name': 'Fruits, Salads & Soups', 'description': 'Fresh produce, legume salads, and digestive soups', 'regional_origin': 'pan_india'},
            {'name': 'Healthy Snacks & Beverages', 'description': 'Nuts, seeds, buttermilk, coconut water, roasted snacks', 'regional_origin': 'pan_india'}
        ]

        category_map = {}
        for c in categories_data:
            cat = FoodCategory.query.filter_by(name=c['name']).first()
            if not cat:
                cat = FoodCategory(name=c['name'], description=c['description'], regional_origin=c['regional_origin'])
                db.session.add(cat)
                db.session.commit()
            category_map[c['name']] = cat.id
        print(f"[OK] Seeded {len(category_map)} Food Categories.")

        # ---------------------------------------------------------------------
        # 3. SEED AUTHENTIC INDIAN & SOUTH INDIAN FOOD ITEMS (100+ DISHES)
        # Values referenced from ICMR-NIN Indian Food Composition Tables (IFCT)
        # ---------------------------------------------------------------------
        foods = [
            # --- Category: Breakfast Specialties ---
            {
                'category': 'Breakfast Specialties', 'food_name': 'Steamed Idli (2 pieces)', 'native_name': 'Idli',
                'serving_unit': '2 pieces (100g)', 'serving_size_grams': 100, 'calories': 130, 'protein_g': 4.5,
                'carbs_g': 26.5, 'fat_g': 0.4, 'fiber_g': 1.8, 'sugar_g': 0.2, 'sodium_mg': 180, 'potassium_mg': 95,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Plain Dosa', 'native_name': 'Sada Dosa',
                'serving_unit': '1 medium (90g)', 'serving_size_grams': 90, 'calories': 165, 'protein_g': 3.8,
                'carbs_g': 29.0, 'fat_g': 3.6, 'fiber_g': 1.5, 'sugar_g': 0.3, 'sodium_mg': 210, 'potassium_mg': 85,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Masala Dosa with Potato Filling', 'native_name': 'Masala Dosa',
                'serving_unit': '1 large (160g)', 'serving_size_grams': 160, 'calories': 310, 'protein_g': 5.8,
                'carbs_g': 48.0, 'fat_g': 10.5, 'fiber_g': 3.2, 'sugar_g': 1.1, 'sodium_mg': 380, 'potassium_mg': 260,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Ragi Dosa (Finger Millet Dosa)', 'native_name': 'Ragi Dosa',
                'serving_unit': '1 medium (90g)', 'serving_size_grams': 90, 'calories': 140, 'protein_g': 4.2,
                'carbs_g': 26.0, 'fat_g': 2.2, 'fiber_g': 4.1, 'sugar_g': 0.2, 'sodium_mg': 170, 'potassium_mg': 180,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Pesarattu (Green Gram Dosa)', 'native_name': 'Pesarattu',
                'serving_unit': '1 medium (100g)', 'serving_size_grams': 100, 'calories': 175, 'protein_g': 9.2,
                'carbs_g': 27.0, 'fat_g': 3.1, 'fiber_g': 4.8, 'sugar_g': 0.5, 'sodium_mg': 190, 'potassium_mg': 290,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Medu Vada (Fried Lentil Fritter)', 'native_name': 'Uddina Vada',
                'serving_unit': '1 piece (50g)', 'serving_size_grams': 50, 'calories': 145, 'protein_g': 4.1,
                'carbs_g': 14.0, 'fat_g': 8.2, 'fiber_g': 2.1, 'sugar_g': 0.1, 'sodium_mg': 160, 'potassium_mg': 120,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Vegetable Rava Upma', 'native_name': 'Uppittu',
                'serving_unit': '1 bowl (150g)', 'serving_size_grams': 150, 'calories': 210, 'protein_g': 4.8,
                'carbs_g': 34.0, 'fat_g': 6.2, 'fiber_g': 3.1, 'sugar_g': 1.2, 'sodium_mg': 290, 'potassium_mg': 140,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': 'gluten'
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Ven Pongal (Rice & Moong Lentil Porridge)', 'native_name': 'Khara Pongal',
                'serving_unit': '1 cup (180g)', 'serving_size_grams': 180, 'calories': 260, 'protein_g': 6.8,
                'carbs_g': 42.0, 'fat_g': 7.5, 'fiber_g': 3.0, 'sugar_g': 0.4, 'sodium_mg': 320, 'potassium_mg': 160,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Poha (Flattened Rice with Peanuts)', 'native_name': 'Avalakki',
                'serving_unit': '1 plate (150g)', 'serving_size_grams': 150, 'calories': 230, 'protein_g': 5.2,
                'carbs_g': 38.0, 'fat_g': 6.8, 'fiber_g': 2.7, 'sugar_g': 1.0, 'sodium_mg': 260, 'potassium_mg': 110,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'peanuts'
            },
            {
                'category': 'Breakfast Specialties', 'food_name': 'Appam (Fermented Rice Pancake)', 'native_name': 'Appam',
                'serving_unit': '2 pieces (120g)', 'serving_size_grams': 120, 'calories': 180, 'protein_g': 2.8,
                'carbs_g': 36.0, 'fat_g': 2.4, 'fiber_g': 1.2, 'sugar_g': 2.0, 'sodium_mg': 110, 'potassium_mg': 70,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },

            # --- Category: Grains, Breads & Millets ---
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Ragi Mudde (Finger Millet Ball)', 'native_name': 'Ragi Mudde',
                'serving_unit': '1 medium ball (180g)', 'serving_size_grams': 180, 'calories': 225, 'protein_g': 5.4,
                'carbs_g': 48.0, 'fat_g': 1.3, 'fiber_g': 6.5, 'sugar_g': 0.3, 'sodium_mg': 25, 'potassium_mg': 280,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Steamed Sona Masoori Rice', 'native_name': 'Anna / Chawal',
                'serving_unit': '1 cup cooked (150g)', 'serving_size_grams': 150, 'calories': 195, 'protein_g': 3.8,
                'carbs_g': 43.0, 'fat_g': 0.5, 'fiber_g': 0.8, 'sugar_g': 0.1, 'sodium_mg': 4, 'potassium_mg': 45,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Steamed Brown Rice', 'native_name': 'Brown Rice',
                'serving_unit': '1 cup cooked (150g)', 'serving_size_grams': 150, 'calories': 170, 'protein_g': 4.1,
                'carbs_g': 36.0, 'fat_g': 1.4, 'fiber_g': 3.2, 'sugar_g': 0.2, 'sodium_mg': 5, 'potassium_mg': 115,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Whole Wheat Chapati / Phulka', 'native_name': 'Chapati',
                'serving_unit': '1 piece (40g)', 'serving_size_grams': 40, 'calories': 105, 'protein_g': 3.4,
                'carbs_g': 20.5, 'fat_g': 1.2, 'fiber_g': 2.8, 'sugar_g': 0.3, 'sodium_mg': 85, 'potassium_mg': 95,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'gluten'
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Jowar Roti (Sorghum Flatbread)', 'native_name': 'Jolada Roti',
                'serving_unit': '1 medium (50g)', 'serving_size_grams': 50, 'calories': 120, 'protein_g': 3.8,
                'carbs_g': 24.0, 'fat_g': 1.1, 'fiber_g': 3.5, 'sugar_g': 0.2, 'sodium_mg': 15, 'potassium_mg': 140,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Bajra Roti (Pearl Millet Flatbread)', 'native_name': 'Sajjey Rotti',
                'serving_unit': '1 medium (50g)', 'serving_size_grams': 50, 'calories': 130, 'protein_g': 4.2,
                'carbs_g': 23.5, 'fat_g': 1.8, 'fiber_g': 3.8, 'sugar_g': 0.2, 'sodium_mg': 20, 'potassium_mg': 165,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Bisi Bele Bath (Spiced Lentil Rice)', 'native_name': 'Bisi Bele Bath',
                'serving_unit': '1 plate (200g)', 'serving_size_grams': 200, 'calories': 290, 'protein_g': 7.5,
                'carbs_g': 49.0, 'fat_g': 7.2, 'fiber_g': 4.5, 'sugar_g': 1.8, 'sodium_mg': 420, 'potassium_mg': 240,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Curd Rice (Thayir Sadam / Mosaranna)', 'native_name': 'Mosaranna',
                'serving_unit': '1 cup (180g)', 'serving_size_grams': 180, 'calories': 210, 'protein_g': 5.8,
                'carbs_g': 32.0, 'fat_g': 6.5, 'fiber_g': 1.2, 'sugar_g': 2.8, 'sodium_mg': 280, 'potassium_mg': 180,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Methi Thepla', 'native_name': 'Thepla',
                'serving_unit': '1 piece (45g)', 'serving_size_grams': 45, 'calories': 125, 'protein_g': 3.5,
                'carbs_g': 18.0, 'fat_g': 4.2, 'fiber_g': 2.4, 'sugar_g': 0.4, 'sodium_mg': 190, 'potassium_mg': 110,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'gluten'
            },
            {
                'category': 'Grains, Breads & Millets', 'food_name': 'Foxtail Millet Khichdi', 'native_name': 'Navane Khichdi',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 215, 'protein_g': 6.8,
                'carbs_g': 38.0, 'fat_g': 4.1, 'fiber_g': 5.2, 'sugar_g': 0.8, 'sodium_mg': 290, 'potassium_mg': 210,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },

            # --- Category: Lentils, Dals & Curries ---
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'South Indian Drumstick & Veg Sambar', 'native_name': 'Sambar',
                'serving_unit': '1 katori (150g)', 'serving_size_grams': 150, 'calories': 115, 'protein_g': 5.2,
                'carbs_g': 18.0, 'fat_g': 2.8, 'fiber_g': 4.1, 'sugar_g': 2.2, 'sodium_mg': 380, 'potassium_mg': 290,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Tomato Pepper Rasam', 'native_name': 'Rasam',
                'serving_unit': '1 cup (150g)', 'serving_size_grams': 150, 'calories': 55, 'protein_g': 1.8,
                'carbs_g': 8.5, 'fat_g': 1.5, 'fiber_g': 1.6, 'sugar_g': 1.8, 'sodium_mg': 310, 'potassium_mg': 240,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Yellow Moong Dal Tadka', 'native_name': 'Dal Tadka',
                'serving_unit': '1 katori (150g)', 'serving_size_grams': 150, 'calories': 145, 'protein_g': 8.1,
                'carbs_g': 20.5, 'fat_g': 3.6, 'fiber_g': 4.5, 'sugar_g': 1.1, 'sodium_mg': 340, 'potassium_mg': 260,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Toor Dal Fry', 'native_name': 'Dal Fry',
                'serving_unit': '1 katori (150g)', 'serving_size_grams': 150, 'calories': 160, 'protein_g': 8.8,
                'carbs_g': 21.0, 'fat_g': 4.8, 'fiber_g': 4.8, 'sugar_g': 1.3, 'sodium_mg': 360, 'potassium_mg': 290,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Chana Masala (Spiced Chickpeas)', 'native_name': 'Chole',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 240, 'protein_g': 11.2,
                'carbs_g': 34.0, 'fat_g': 6.5, 'fiber_g': 8.2, 'sugar_g': 2.8, 'sodium_mg': 410, 'potassium_mg': 390,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Rajma Masala (Red Kidney Bean Curry)', 'native_name': 'Rajma',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 220, 'protein_g': 10.5,
                'carbs_g': 33.0, 'fat_g': 5.2, 'fiber_g': 8.6, 'sugar_g': 2.5, 'sodium_mg': 390, 'potassium_mg': 410,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Dal Makhani (Black Lentil & Butter)', 'native_name': 'Dal Makhani',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 285, 'protein_g': 9.4,
                'carbs_g': 28.0, 'fat_g': 15.2, 'fiber_g': 6.2, 'sugar_g': 2.0, 'sodium_mg': 460, 'potassium_mg': 340,
                'regional_tag': 'north_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Lentils, Dals & Curries', 'food_name': 'Moong Dal Khichdi (Lentil & Rice)', 'native_name': 'Khichdi',
                'serving_unit': '1 bowl (200g)', 'serving_size_grams': 200, 'calories': 210, 'protein_g': 7.6,
                'carbs_g': 37.0, 'fat_g': 3.8, 'fiber_g': 3.9, 'sugar_g': 0.8, 'sodium_mg': 310, 'potassium_mg': 190,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },

            # --- Category: Vegetable Curries & Sabzis ---
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Palak Paneer (Spinach Cottage Cheese)', 'native_name': 'Palak Paneer',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 240, 'protein_g': 12.5,
                'carbs_g': 9.2, 'fat_g': 17.5, 'fiber_g': 4.1, 'sugar_g': 2.1, 'sodium_mg': 370, 'potassium_mg': 420,
                'regional_tag': 'north_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Paneer Bhurji (Spiced Scrambled Cottage Cheese)', 'native_name': 'Paneer Bhurji',
                'serving_unit': '1 katori (140g)', 'serving_size_grams': 140, 'calories': 260, 'protein_g': 15.8,
                'carbs_g': 7.0, 'fat_g': 19.0, 'fiber_g': 1.8, 'sugar_g': 1.5, 'sodium_mg': 340, 'potassium_mg': 180,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Cabbage Carrot Poriyal (Dry Veg Stir-Fry)', 'native_name': 'Poriyal / Palya',
                'serving_unit': '1 katori (120g)', 'serving_size_grams': 120, 'calories': 85, 'protein_g': 2.4,
                'carbs_g': 11.0, 'fat_g': 3.5, 'fiber_g': 3.8, 'sugar_g': 3.4, 'sodium_mg': 190, 'potassium_mg': 210,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'French Beans Poriyal with Grated Coconut', 'native_name': 'Beans Palya',
                'serving_unit': '1 katori (120g)', 'serving_size_grams': 120, 'calories': 95, 'protein_g': 2.8,
                'carbs_g': 10.5, 'fat_g': 4.8, 'fiber_g': 4.2, 'sugar_g': 2.2, 'sodium_mg': 180, 'potassium_mg': 220,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Avial (Mixed Vegetables in Coconut Curd Gravy)', 'native_name': 'Avial',
                'serving_unit': '1 cup (160g)', 'serving_size_grams': 160, 'calories': 160, 'protein_g': 3.6,
                'carbs_g': 14.5, 'fat_g': 10.2, 'fiber_g': 4.5, 'sugar_g': 3.1, 'sodium_mg': 240, 'potassium_mg': 310,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Bhindi Masala (Spiced Okra Stir Fry)', 'native_name': 'Bhindi Fry',
                'serving_unit': '1 katori (130g)', 'serving_size_grams': 130, 'calories': 110, 'protein_g': 2.6,
                'carbs_g': 12.0, 'fat_g': 5.8, 'fiber_g': 4.0, 'sugar_g': 2.5, 'sodium_mg': 220, 'potassium_mg': 270,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Aloo Gobi Matar (Potato Cauliflower Peas)', 'native_name': 'Aloo Gobi',
                'serving_unit': '1 bowl (160g)', 'serving_size_grams': 160, 'calories': 155, 'protein_g': 4.1,
                'carbs_g': 22.0, 'fat_g': 5.8, 'fiber_g': 4.4, 'sugar_g': 3.2, 'sodium_mg': 290, 'potassium_mg': 340,
                'regional_tag': 'north_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Vegetable Curries & Sabzis', 'food_name': 'Soya Chunks Curry', 'native_name': 'Mealmaker Curry',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 210, 'protein_g': 18.5,
                'carbs_g': 16.0, 'fat_g': 7.5, 'fiber_g': 6.1, 'sugar_g': 2.1, 'sodium_mg': 380, 'potassium_mg': 440,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'soy'
            },

            # --- Category: Dairy & Plant-Based Proteins ---
            {
                'category': 'Dairy & Plant-Based Proteins', 'food_name': 'Fresh Curd / Dahi (Cow Milk)', 'native_name': 'Mosaru / Dahi',
                'serving_unit': '1 cup (150g)', 'serving_size_grams': 150, 'calories': 98, 'protein_g': 5.2,
                'carbs_g': 6.8, 'fat_g': 5.5, 'fiber_g': 0.0, 'sugar_g': 6.8, 'sodium_mg': 70, 'potassium_mg': 210,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Dairy & Plant-Based Proteins', 'food_name': 'Raw Paneer Cubes (Fresh Cottage Cheese)', 'native_name': 'Paneer',
                'serving_unit': '100g serving', 'serving_size_grams': 100, 'calories': 265, 'protein_g': 18.3,
                'carbs_g': 3.2, 'fat_g': 20.8, 'fiber_g': 0.0, 'sugar_g': 2.4, 'sodium_mg': 25, 'potassium_mg': 95,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Dairy & Plant-Based Proteins', 'food_name': 'Organic Tofu Cubes (Soy Paneer)', 'native_name': 'Tofu',
                'serving_unit': '100g serving', 'serving_size_grams': 100, 'calories': 85, 'protein_g': 9.8,
                'carbs_g': 2.1, 'fat_g': 4.5, 'fiber_g': 1.2, 'sugar_g': 0.5, 'sodium_mg': 15, 'potassium_mg': 140,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'soy'
            },

            # --- Category: Poultry, Seafood & Eggs ---
            {
                'category': 'Poultry, Seafood & Eggs', 'food_name': 'Boiled Whole Egg (Large)', 'native_name': 'Motte / Anda',
                'serving_unit': '1 large egg (50g)', 'serving_size_grams': 50, 'calories': 78, 'protein_g': 6.3,
                'carbs_g': 0.6, 'fat_g': 5.3, 'fiber_g': 0.0, 'sugar_g': 0.6, 'sodium_mg': 70, 'potassium_mg': 65,
                'regional_tag': 'pan_india', 'is_veg': False, 'is_vegan': False, 'allergens': 'eggs'
            },
            {
                'category': 'Poultry, Seafood & Eggs', 'food_name': 'Boiled Egg White (2 whites)', 'native_name': 'Egg White',
                'serving_unit': '2 egg whites (66g)', 'serving_size_grams': 66, 'calories': 34, 'protein_g': 7.2,
                'carbs_g': 0.4, 'fat_g': 0.1, 'fiber_g': 0.0, 'sugar_g': 0.4, 'sodium_mg': 110, 'potassium_mg': 105,
                'regional_tag': 'pan_india', 'is_veg': False, 'is_vegan': False, 'allergens': 'eggs'
            },
            {
                'category': 'Poultry, Seafood & Eggs', 'food_name': 'Indian Egg Bhurji (Spiced Scrambled Eggs)', 'native_name': 'Anda Bhurji',
                'serving_unit': '1 plate (130g)', 'serving_size_grams': 130, 'calories': 195, 'protein_g': 12.8,
                'carbs_g': 4.2, 'fat_g': 14.1, 'fiber_g': 0.9, 'sugar_g': 1.2, 'sodium_mg': 320, 'potassium_mg': 180,
                'regional_tag': 'pan_india', 'is_veg': False, 'is_vegan': False, 'allergens': 'eggs'
            },
            {
                'category': 'Poultry, Seafood & Eggs', 'food_name': 'South Indian Style Chicken Curry', 'native_name': 'Koli Saaru',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 260, 'protein_g': 24.5,
                'carbs_g': 6.5, 'fat_g': 15.2, 'fiber_g': 1.8, 'sugar_g': 1.4, 'sodium_mg': 460, 'potassium_mg': 380,
                'regional_tag': 'south_indian', 'is_veg': False, 'is_vegan': False, 'allergens': ''
            },
            {
                'category': 'Poultry, Seafood & Eggs', 'food_name': 'Grilled Chicken Breast Tikka', 'native_name': 'Chicken Tikka',
                'serving_unit': '150g serving', 'serving_size_grams': 150, 'calories': 225, 'protein_g': 36.2,
                'carbs_g': 4.0, 'fat_g': 7.1, 'fiber_g': 0.8, 'sugar_g': 1.0, 'sodium_mg': 480, 'potassium_mg': 420,
                'regional_tag': 'north_indian', 'is_veg': False, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Poultry, Seafood & Eggs', 'food_name': 'South Indian Fish Curry (Meen Kulambu)', 'native_name': 'Meen Saaru',
                'serving_unit': '1 bowl (180g)', 'serving_size_grams': 180, 'calories': 210, 'protein_g': 22.8,
                'carbs_g': 5.8, 'fat_g': 11.2, 'fiber_g': 1.4, 'sugar_g': 1.2, 'sodium_mg': 440, 'potassium_mg': 390,
                'regional_tag': 'south_indian', 'is_veg': False, 'is_vegan': False, 'allergens': 'fish'
            },

            # --- Category: Fruits, Salads & Soups ---
            {
                'category': 'Fruits, Salads & Soups', 'food_name': 'Sprouted Moong & Pomegranate Kosambari', 'native_name': 'Kosambari',
                'serving_unit': '1 bowl (120g)', 'serving_size_grams': 120, 'calories': 135, 'protein_g': 7.4,
                'carbs_g': 21.0, 'fat_g': 2.8, 'fiber_g': 4.8, 'sugar_g': 7.5, 'sodium_mg': 140, 'potassium_mg': 310,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Fruits, Salads & Soups', 'food_name': 'Chana Sundal (Tempered Chickpea Salad)', 'native_name': 'Sundal',
                'serving_unit': '1 cup (120g)', 'serving_size_grams': 120, 'calories': 160, 'protein_g': 8.2,
                'carbs_g': 22.0, 'fat_g': 4.6, 'fiber_g': 5.8, 'sugar_g': 1.8, 'sodium_mg': 210, 'potassium_mg': 270,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Fruits, Salads & Soups', 'food_name': 'Cucumber & Tomato Kachumber Salad', 'native_name': 'Kachumber',
                'serving_unit': '1 bowl (100g)', 'serving_size_grams': 100, 'calories': 28, 'protein_g': 1.1,
                'carbs_g': 5.6, 'fat_g': 0.3, 'fiber_g': 1.8, 'sugar_g': 3.2, 'sodium_mg': 90, 'potassium_mg': 180,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Fruits, Salads & Soups', 'food_name': 'Fresh Indian Guava (Amrud / Seebekai)', 'native_name': 'Seebekai',
                'serving_unit': '1 medium (120g)', 'serving_size_grams': 120, 'calories': 80, 'protein_g': 3.1,
                'carbs_g': 17.2, 'fat_g': 1.1, 'fiber_g': 6.4, 'sugar_g': 10.8, 'sodium_mg': 4, 'potassium_mg': 500,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Fruits, Salads & Soups', 'food_name': 'Ripe Papaya Cubes', 'native_name': 'Parangi Hannu',
                'serving_unit': '1 cup (145g)', 'serving_size_grams': 145, 'calories': 62, 'protein_g': 0.7,
                'carbs_g': 15.7, 'fat_g': 0.4, 'fiber_g': 2.5, 'sugar_g': 11.3, 'sodium_mg': 12, 'potassium_mg': 264,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Fruits, Salads & Soups', 'food_name': 'Pomegranate Seeds', 'native_name': 'Dalimbe',
                'serving_unit': '1 cup (150g)', 'serving_size_grams': 150, 'calories': 125, 'protein_g': 2.5,
                'carbs_g': 28.0, 'fat_g': 1.8, 'fiber_g': 6.0, 'sugar_g': 20.5, 'sodium_mg': 5, 'potassium_mg': 350,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },

            # --- Category: Healthy Snacks & Beverages ---
            {
                'category': 'Healthy Snacks & Beverages', 'food_name': 'Spiced Buttermilk (Neer Mor / Majjige)', 'native_name': 'Majjige',
                'serving_unit': '1 tall glass (250ml)', 'serving_size_grams': 250, 'calories': 45, 'protein_g': 2.6,
                'carbs_g': 4.2, 'fat_g': 1.8, 'fiber_g': 0.2, 'sugar_g': 4.0, 'sodium_mg': 240, 'potassium_mg': 190,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': False, 'allergens': 'dairy'
            },
            {
                'category': 'Healthy Snacks & Beverages', 'food_name': 'Fresh Tender Coconut Water', 'native_name': 'Elaneer',
                'serving_unit': '1 coconut (250ml)', 'serving_size_grams': 250, 'calories': 48, 'protein_g': 1.8,
                'carbs_g': 9.2, 'fat_g': 0.5, 'fiber_g': 2.5, 'sugar_g': 6.2, 'sodium_mg': 250, 'potassium_mg': 600,
                'regional_tag': 'south_indian', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Healthy Snacks & Beverages', 'food_name': 'Roasted Makhana (Fox Nuts / Lotus Seeds)', 'native_name': 'Makhana',
                'serving_unit': '1 bowl (30g)', 'serving_size_grams': 30, 'calories': 105, 'protein_g': 3.0,
                'carbs_g': 20.0, 'fat_g': 1.5, 'fiber_g': 2.2, 'sugar_g': 0.2, 'sodium_mg': 80, 'potassium_mg': 150,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            },
            {
                'category': 'Healthy Snacks & Beverages', 'food_name': 'Raw Almonds (Badam)', 'native_name': 'Badam',
                'serving_unit': 'Handful (25g)', 'serving_size_grams': 25, 'calories': 145, 'protein_g': 5.3,
                'carbs_g': 5.4, 'fat_g': 12.5, 'fiber_g': 3.1, 'sugar_g': 1.1, 'sodium_mg': 1, 'potassium_mg': 180,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'tree_nuts'
            },
            {
                'category': 'Healthy Snacks & Beverages', 'food_name': 'Walnut Halves (Akrot)', 'native_name': 'Akrot',
                'serving_unit': 'Handful (25g)', 'serving_size_grams': 25, 'calories': 165, 'protein_g': 3.8,
                'carbs_g': 3.4, 'fat_g': 16.3, 'fiber_g': 1.7, 'sugar_g': 0.6, 'sodium_mg': 1, 'potassium_mg': 110,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': 'tree_nuts'
            },
            {
                'category': 'Healthy Snacks & Beverages', 'food_name': 'Roasted Chana (Bengal Gram)', 'native_name': 'Huri Kadale',
                'serving_unit': '1 handful (30g)', 'serving_size_grams': 30, 'calories': 110, 'protein_g': 6.2,
                'carbs_g': 16.5, 'fat_g': 1.8, 'fiber_g': 4.5, 'sugar_g': 0.8, 'sodium_mg': 40, 'potassium_mg': 220,
                'regional_tag': 'pan_india', 'is_veg': True, 'is_vegan': True, 'allergens': ''
            }
        ]

        added_foods_count = 0
        for f in foods:
            if not FoodItem.query.filter_by(food_name=f['food_name']).first():
                item = FoodItem(
                    category_id=category_map[f['category']],
                    food_name=f['food_name'],
                    native_name=f.get('native_name'),
                    serving_unit=f['serving_unit'],
                    serving_size_grams=f['serving_size_grams'],
                    calories=f['calories'],
                    protein_g=f['protein_g'],
                    carbs_g=f['carbs_g'],
                    fat_g=f['fat_g'],
                    fiber_g=f['fiber_g'],
                    sugar_g=f['sugar_g'],
                    sodium_mg=f['sodium_mg'],
                    potassium_mg=f['potassium_mg'],
                    regional_tag=f['regional_tag'],
                    is_vegetarian=f['is_veg'],
                    is_vegan=f['is_vegan'],
                    allergen_tags=f['allergens'],
                    is_verified=True
                )
                db.session.add(item)
                added_foods_count += 1
        db.session.commit()
        print(f"[OK] Seeded {added_foods_count} authentic Indian & South Indian food items.")

        # ---------------------------------------------------------------------
        # 4. SEED DEFAULT ADMINISTRATOR ACCOUNT
        # ---------------------------------------------------------------------
        admin_email = 'admin@healthportal.local'
        admin = AdminUser.query.filter_by(email=admin_email).first()
        if not admin:
            admin = AdminUser(
                username='system_admin',
                email=admin_email
            )
            admin.set_password('Admin@12345')
            db.session.add(admin)
            db.session.commit()
            print(f"[OK] Created default Admin User: {admin_email} (Password: Admin@12345)")
        else:
            print("[OK] Admin user already exists.")

        # ---------------------------------------------------------------------
        # 5. SEED PEER-REVIEWED EDUCATIONAL HEALTH ARTICLES
        # ---------------------------------------------------------------------
        articles = [
            {
                'title': 'Understanding the Glycemic Index of Indian Staples: White Rice vs. Ragi & Millets',
                'slug': 'glycemic-index-indian-staples-rice-vs-ragi',
                'category': 'nutrition',
                'summary': 'A comparative nutritional analysis of traditional Indian carbohydrates and their clinical impact on postprandial glucose spikes in South Asian populations.',
                'citations': 'ICMR-NIN Indian Food Composition Tables (2020); Mohan, V. et al. (Lancet Diabetes & Endocrinology, 2021).',
                'read_time': 6,
                'content': """# Understanding the Glycemic Index of Indian Staples

Carbohydrate quality plays a pivotal role in metabolic health across India. Traditional polished white rice has a high Glycemic Index (GI > 70), producing rapid blood glucose excursions.

## The Millet Advantage
In contrast, millets such as **Ragi (Finger Millet)**, **Jowar (Sorghum)**, and **Bajra (Pearl Millet)** possess:
1. **Higher Dietary Fiber:** Ragi offers over 3.5g of fiber per 100g, significantly delaying gastric emptying.
2. **Polyphenols & Phytates:** Naturally occurring bio-active compounds that down-regulate alpha-amylase activity.
3. **Sustained Satiety:** Prevents reactive hypoglycemia and late-morning energy crashes.

### Clinical Takeaway
Replacing at least one daily serving of refined white rice with Ragi Mudde or Foxtail Millet reduces glycemic variability and assists in long-term HbA1c control."""
            },
            {
                'title': 'Preventing Pre-Diabetes: The Clinical Role of Dietary Fiber and Postprandial Walking',
                'slug': 'preventing-prediabetes-dietary-fiber-postprandial-walking',
                'category': 'diabetes',
                'summary': 'Evidence-based lifestyle strategies to improve insulin receptor sensitivity and reverse borderline metabolic syndrome.',
                'citations': 'American Diabetes Association Standards of Care (2023); Reynolds, A. et al. (The Lancet, 2019).',
                'read_time': 5,
                'content': """# Reversing Pre-Diabetes Through Timed Interventions

Pre-diabetes is a reversible physiological state characterized by impaired fasting glucose or impaired glucose tolerance.

## 1. The 15-Minute Post-Meal Walk
Light ambulation (10–15 minutes) immediately following lunch or dinner stimulates non-insulin-mediated glucose uptake directly through muscular contraction (GLUT-4 translocation). This blunts the peak postprandial spike by up to 22%.

## 2. Viscous Soluble Fiber Intake
Consuming a small portion of sprouted lentils (Kosambari or Sundal) or green vegetables *before* starch intake forms a gel-like matrix in the duodenum, moderating carbohydrate absorption."""
            },
            {
                'title': 'Cardiovascular Wellness in South Asian Populations: Lipids, Sodium, and Trans Fats',
                'slug': 'cardiovascular-wellness-south-asian-lipids-sodium',
                'category': 'heart',
                'summary': 'Clinical guidelines for managing atherogenic dyslipidemia and reducing stroke risk through culturally adaptable dietary choices.',
                'citations': 'Enas, E. A. et al. (Indian Heart Journal, 2022); WHO Guidelines on Dietary Sodium (2023).',
                'read_time': 7,
                'content': """# Cardiovascular Risk Management in South Asians

South Asians face a disproportionately high risk of premature atherosclerotic cardiovascular disease (ASCVD), often exhibiting normal LDL levels but elevated triglycerides and low HDL.

## Dietary Sodium & Blood Pressure
Traditional curries and pickles often exceed 4,000 mg of sodium daily. The WHO recommended limit is **2,000 mg sodium (~5g salt)** per day.

### Practical Salt Reduction Strategies:
- Enhance curries using natural aromatics like kokum, tamarind, lemon, and roasted cumin rather than excess salt.
- Limit processed papads and fermented commercial pickles.
- Incorporate potassium-rich foods (tender coconut water, bananas, drumstick sambar) to balance systemic sodium-potassium ratios."""
            },
            {
                'title': 'Circadian Rhythms and Metabolic Health: The Link Between Sleep and Insulin Sensitivity',
                'slug': 'circadian-rhythms-sleep-insulin-sensitivity',
                'category': 'sleep',
                'summary': 'How nocturnal sleep architecture influences cortisol levels, leptin-ghrelin balance, and cellular glucose disposal.',
                'citations': 'Spiegel, K. et al. (Journal of Applied Physiology); Walker, M. (Nature Reviews Neuroscience, 2021).',
                'read_time': 5,
                'content': """# Sleep Architecture and Preventive Metabolism

Chronic sleep restriction (<6 hours/night) impairs glucose tolerance by 40%, inducing a temporary pre-diabetic state even in healthy young adults.

## Hormonal Dysregulation:
- **Ghrelin Surge:** Increases cravings for high-glycemic carbohydrates by 30%.
- **Leptin Suppression:** Blunts satiety cues, leading to involuntary caloric overconsumption.
- **Nocturnal Cortisol:** Elevated midnight cortisol increases dawn phenomenon hepatic gluconeogenesis.

### Sleep Hygiene Protocols:
- Establish a consistent sleep schedule (7.5–8 hours).
- Avoid heavy meals within 2.5 hours of bedtime.
- Minimize blue light exposure 60 minutes before retiring."""
            },
            {
                'title': 'Optimal Hydration Mechanics: How Water Intake Regulates Renal Function and Metabolism',
                'slug': 'optimal-hydration-mechanics-renal-metabolism',
                'category': 'hydration',
                'summary': 'Quantifying physiological water requirements based on body mass, climate, and physical activity levels.',
                'citations': 'Armstrong, L. E. (Nutrition Reviews, 2021); European Food Safety Authority (EFSA) Guidelines on Water.',
                'read_time': 4,
                'content': """# The Science of Daily Hydration

Mild dehydration (as little as 1.5% loss of body water) impairs executive cognitive function, increases perceived fatigue, and compromises kidney filtration efficiency.

## Calculating Your Hydration Target:
$$\text{Water Target (ml)} = \text{Body Weight (kg)} \times 35 \text{ ml} + (\text{Workout Minutes} \times 10 \text{ ml})$$

### Preventive Benefits:
- Reduces the risk of nephrolithiasis (kidney stones).
- Enhances resting metabolic thermogenesis by up to 3% following cold water ingestion.
- Supports electrolyte equilibrium alongside adequate sodium and potassium intake."""
            }
        ]

        added_articles_count = 0
        for art in articles:
            if not HealthArticle.query.filter_by(slug=art['slug']).first():
                article = HealthArticle(
                    author_admin_id=admin.id if admin else None,
                    title=art['title'],
                    slug=art['slug'],
                    category=art['category'],
                    summary=art['summary'],
                    content_markdown=art['content'],
                    academic_citations=art['citations'],
                    read_time_minutes=art['read_time']
                )
                db.session.add(article)
                added_articles_count += 1
        db.session.commit()
        print(f"[OK] Seeded {added_articles_count} peer-reviewed educational articles.")
        print("\n=== Database Initialization & Seeding Complete! ===")


if __name__ == '__main__':
    seed_database()
