"""
RecommendationService: Multi-Objective Real-Time Deficit-Filling Engine.
Implements cultural adaptability, strict allergy exclusions, and explainable
nutritional optimization inspired by FR-RANC (IEEE Access 2025).
"""

from datetime import date
from sqlalchemy import or_
from models import (
    db,
    User,
    FoodItem,
    MealType,
    FoodLog,
    Recommendation
)
from services.dashboard_service import DashboardService


class RecommendationService:
    """Computes daily nutrient deficits, scores regional food items, and provides explainable meal suggestions."""

    @classmethod
    def get_remaining_deficits(cls, user_id, target_date=None):
        """Compute the remaining daily gap for calories and macronutrients."""
        if target_date is None:
            target_date = date.today()

        summary = DashboardService.get_daily_summary(user_id, target_date)
        if not summary:
            return None

        nutr = summary['nutrition']
        return {
            'calorie_deficit': nutr['calories']['remaining'],
            'protein_deficit': nutr['protein']['remaining'],
            'carb_deficit': nutr['carbs']['remaining'],
            'fat_deficit': nutr['fat']['remaining'],
            'target_calories': nutr['calories']['target'],
            'consumed_calories': nutr['calories']['consumed'],
            'consumed_protein': nutr['protein']['consumed']
        }

    @classmethod
    def generate_recommendations(cls, user_id, meal_time='lunch', target_date=None, limit=6):
        """
        Evaluate verified food items, filter by dietary constraints and allergies,
        and score candidates based on current nutritional deficit alignment.
        """
        if target_date is None:
            target_date = date.today()

        user = User.query.get(user_id)
        if not user or not user.profile:
            return []

        profile = user.profile
        deficits = cls.get_remaining_deficits(user_id, target_date)
        if not deficits:
            return []

        # 1. Parse User Constraints
        dietary_pref = (profile.dietary_preference or 'vegetarian').lower()
        regional_pref = (profile.regional_preference or 'south_indian').lower()
        allergies = [a.strip().lower() for a in profile.food_allergies.split(',') if a.strip()] if profile.food_allergies else []

        # 2. Query Candidate Food Items
        candidate_query = FoodItem.query.filter(FoodItem.is_verified == True)

        # Dietary preference constraints
        if dietary_pref == 'vegan':
            candidate_query = candidate_query.filter(FoodItem.is_vegan == True)
        elif dietary_pref in ['vegetarian', 'lacto_vegetarian']:
            candidate_query = candidate_query.filter(FoodItem.is_vegetarian == True)
        elif dietary_pref == 'eggetarian':
            # Allows vegetarian OR egg items
            candidate_query = candidate_query.filter(
                or_(
                    FoodItem.is_vegetarian == True,
                    FoodItem.allergen_tags.ilike('%egg%'),
                    FoodItem.food_name.ilike('%egg%')
                )
            )

        candidates = candidate_query.all()
        scored_candidates = []

        # 3. Multi-Objective Scoring Heuristic
        prot_deficit = deficits['protein_deficit']
        cal_deficit = deficits['calorie_deficit']

        for item in candidates:
            # STRICT FILTER: Allergy Exclusion Constraint
            if item.has_allergen(allergies):
                continue

            # Skip items that alone severely overshoot total daily remaining calories by > 250 kcal
            if cal_deficit > 0 and item.calories > (cal_deficit + 250.0):
                continue

            score = 0.50  # Base neutral score
            reasons = []

            # Factor A: Protein Deficit Filling (Higher weight when user is deficient in protein)
            if prot_deficit > 10.0:
                if item.protein_g >= 12.0:
                    score += 0.25
                    reasons.append(f"High protein content ({item.protein_g}g) addresses your remaining {prot_deficit}g protein deficit")
                elif item.protein_g >= 6.0:
                    score += 0.12
                    reasons.append(f"Provides {item.protein_g}g of bio-available protein")
            elif item.protein_g >= 5.0:
                score += 0.08

            # Factor B: Caloric Suitability for Meal Window
            # Allocate approximate budget: Breakfast ~25%, Lunch ~35%, Dinner ~30%, Snacks ~10%
            meal_calorie_targets = {
                'breakfast': deficits['target_calories'] * 0.25,
                'lunch': deficits['target_calories'] * 0.35,
                'dinner': deficits['target_calories'] * 0.30,
                'snacks': deficits['target_calories'] * 0.10
            }
            target_for_window = meal_calorie_targets.get(meal_time.lower(), deficits['target_calories'] * 0.30)
            cal_diff = abs(item.calories - target_for_window)

            if cal_diff < 100:
                score += 0.15
                reasons.append(f"Optimal caloric portion ({item.calories} kcal) for {meal_time.capitalize()}")
            elif cal_diff < 200:
                score += 0.08

            # Factor C: Regional Culinary Affinity
            if item.regional_tag == regional_pref:
                score += 0.10
                reasons.append(f"Aligned with your {regional_pref.replace('_', ' ').title()} culinary preference")
            elif item.regional_tag == 'pan_india':
                score += 0.05

            # Factor D: High Fiber & Low Sugar Bonus (Preventive Cardiometabolic health)
            if item.fiber_g >= 3.5:
                score += 0.08
                reasons.append(f"Rich in dietary fiber ({item.fiber_g}g) to blunt glycemic spikes")

            normalized_score = min(round(score, 2), 0.99)
            primary_reason = reasons[0] if reasons else "Nutritionally balanced meal suggestion"
            clinical_justification = " &bull; ".join(reasons)

            scored_candidates.append({
                'food_item': item,
                'score': normalized_score,
                'reason': primary_reason,
                'justification': clinical_justification,
                'meal_time': meal_time.lower()
            })

        # 4. Sort by score descending and take top candidates
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        top_recommendations = scored_candidates[:limit]

        # 5. Persist recommendations into database for historical tracking
        persisted_recos = []
        for cand in top_recommendations:
            existing = Recommendation.query.filter_by(
                user_id=user.id,
                food_item_id=cand['food_item'].id,
                recommendation_date=target_date,
                meal_time=cand['meal_time']
            ).first()

            if not existing:
                reco = Recommendation(
                    user_id=user.id,
                    food_item_id=cand['food_item'].id,
                    recommendation_date=target_date,
                    meal_time=cand['meal_time'],
                    match_score=cand['score'],
                    recommendation_reason=cand['reason'],
                    clinical_justification=cand['justification'],
                    is_accepted=False
                )
                db.session.add(reco)
                db.session.flush()
                persisted_recos.append(reco)
            else:
                persisted_recos.append(existing)

        db.session.commit()
        return [r.to_dict() for r in persisted_recos]

    @classmethod
    def accept_recommendation(cls, user_id, recommendation_id):
        """
        Accept a recommended meal: marks is_accepted = True and automatically
        creates a corresponding FoodLog entry in the user's journal.
        """
        reco = Recommendation.query.filter_by(id=recommendation_id, user_id=user_id).first()
        if not reco:
            return None, "Recommendation not found."

        food = reco.food_item
        if not food:
            return None, "Associated food item unavailable."

        # Map meal_time to meal_type_id
        meal_type = MealType.query.filter_by(name=reco.meal_time.lower()).first()
        meal_type_id = meal_type.id if meal_type else 1

        food_log = FoodLog(
            user_id=user_id,
            food_item_id=food.id,
            meal_type_id=meal_type_id,
            log_date=reco.recommendation_date,
            quantity_multiplier=1.0,
            calculated_calories=food.calories,
            calculated_protein=food.protein_g,
            calculated_carbs=food.carbs_g,
            calculated_fat=food.fat_g
        )

        reco.is_accepted = True
        db.session.add(food_log)
        db.session.commit()

        return food_log, None
