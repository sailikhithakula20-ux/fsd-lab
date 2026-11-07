"""
DashboardService: Analytical Aggregation Engine for Real-Time Health Metrics,
7-Day Temporal Trajectories, and Rule-Based Clinical Insights.
"""

from datetime import date, timedelta
from sqlalchemy import func
from models import (
    db,
    User,
    FoodLog,
    ActivityLog,
    WaterLog,
    SleepLog,
    NutritionTarget
)


class DashboardService:
    """Computes daily totals, 7-day trends, and personalized clinical insights."""

    @classmethod
    def get_daily_summary(cls, user_id, target_date=None):
        """
        Aggregate nutritional consumption, water, activity, and sleep
        for a specific user on a given date (defaults to today).
        """
        if target_date is None:
            target_date = date.today()

        user = User.query.get(user_id)
        if not user:
            return None

        # 1. Nutrition Aggregation
        nutrition_totals = db.session.query(
            func.coalesce(func.sum(FoodLog.calculated_calories), 0.0).label('calories'),
            func.coalesce(func.sum(FoodLog.calculated_protein), 0.0).label('protein'),
            func.coalesce(func.sum(FoodLog.calculated_carbs), 0.0).label('carbs'),
            func.coalesce(func.sum(FoodLog.calculated_fat), 0.0).label('fat')
        ).filter(
            FoodLog.user_id == user_id,
            FoodLog.log_date == target_date
        ).first()

        consumed_calories = round(float(nutrition_totals.calories), 1)
        consumed_protein = round(float(nutrition_totals.protein), 1)
        consumed_carbs = round(float(nutrition_totals.carbs), 1)
        consumed_fat = round(float(nutrition_totals.fat), 1)

        # 2. Water Aggregation
        water_total = db.session.query(
            func.coalesce(func.sum(WaterLog.amount_ml), 0)
        ).filter(
            WaterLog.user_id == user_id,
            WaterLog.log_date == target_date
        ).scalar() or 0

        # 3. Activity (Steps)
        activity = ActivityLog.query.filter_by(
            user_id=user_id,
            log_date=target_date
        ).first()
        steps = activity.step_count if activity else 0
        active_calories = activity.calories_burned if activity else 0.0

        # 4. Sleep
        sleep = SleepLog.query.filter_by(
            user_id=user_id,
            log_date=target_date
        ).first()
        sleep_hours = sleep.sleep_hours if sleep else 0.0
        sleep_quality = sleep.sleep_quality_score if sleep else 0

        # 5. Targets
        targets = user.nutrition_targets
        target_cal = targets.target_calories if targets else 2000.0
        target_prot = targets.target_protein_g if targets else 60.0
        target_carb = targets.target_carbs_g if targets else 250.0
        target_fat = targets.target_fats_g if targets else 65.0
        target_water = targets.target_water_ml if targets else 2500.0

        # 6. Percentages & Remaining Deficits
        cal_pct = min(round((consumed_calories / target_cal) * 100, 1) if target_cal > 0 else 0, 100)
        prot_pct = min(round((consumed_protein / target_prot) * 100, 1) if target_prot > 0 else 0, 100)
        carb_pct = min(round((consumed_carbs / target_carb) * 100, 1) if target_carb > 0 else 0, 100)
        fat_pct = min(round((consumed_fat / target_fat) * 100, 1) if target_fat > 0 else 0, 100)
        water_pct = min(round((water_total / target_water) * 100, 1) if target_water > 0 else 0, 100)
        steps_pct = min(round((steps / 10000.0) * 100, 1), 100)

        # 7. Recent Logged Meals (up to 5 items)
        recent_logs = FoodLog.query.filter_by(
            user_id=user_id,
            log_date=target_date
        ).order_by(FoodLog.logged_at.desc()).limit(5).all()

        return {
            'date': target_date.isoformat(),
            'nutrition': {
                'calories': {'consumed': consumed_calories, 'target': target_cal, 'percentage': cal_pct, 'remaining': max(0.0, round(target_cal - consumed_calories, 1))},
                'protein': {'consumed': consumed_protein, 'target': target_prot, 'percentage': prot_pct, 'remaining': max(0.0, round(target_prot - consumed_protein, 1))},
                'carbs': {'consumed': consumed_carbs, 'target': target_carb, 'percentage': carb_pct, 'remaining': max(0.0, round(target_carb - consumed_carbs, 1))},
                'fat': {'consumed': consumed_fat, 'target': target_fat, 'percentage': fat_pct, 'remaining': max(0.0, round(target_fat - consumed_fat, 1))}
            },
            'hydration': {
                'consumed_ml': water_total,
                'target_ml': target_water,
                'percentage': water_pct,
                'remaining_ml': max(0, int(target_water - water_total))
            },
            'activity': {
                'steps': steps,
                'target_steps': 10000,
                'percentage': steps_pct,
                'calories_burned': active_calories
            },
            'sleep': {
                'hours': sleep_hours,
                'target_hours': 8.0,
                'quality_score': sleep_quality
            },
            'recent_meals': [log.to_dict() for log in recent_logs]
        }

    @classmethod
    def get_seven_day_trends(cls, user_id, end_date=None):
        """
        Extract daily time-series data for the past 7 days to drive Chart.js visualizations.
        """
        if end_date is None:
            end_date = date.today()

        dates = [(end_date - timedelta(days=i)) for i in range(6, -1, -1)]
        date_labels = [d.strftime('%a (%b %d)') for d in dates]

        user = User.query.get(user_id)
        target_calories = user.nutrition_targets.target_calories if user and user.nutrition_targets else 2000.0

        daily_calories = []
        daily_protein = []
        daily_carbs = []
        daily_fat = []
        daily_water = []
        daily_steps = []
        daily_sleep = []

        for d in dates:
            # Calories & Macros
            nutr = db.session.query(
                func.coalesce(func.sum(FoodLog.calculated_calories), 0.0),
                func.coalesce(func.sum(FoodLog.calculated_protein), 0.0),
                func.coalesce(func.sum(FoodLog.calculated_carbs), 0.0),
                func.coalesce(func.sum(FoodLog.calculated_fat), 0.0)
            ).filter(FoodLog.user_id == user_id, FoodLog.log_date == d).first()

            daily_calories.append(round(float(nutr[0]), 1))
            daily_protein.append(round(float(nutr[1]), 1))
            daily_carbs.append(round(float(nutr[2]), 1))
            daily_fat.append(round(float(nutr[3]), 1))

            # Water
            water = db.session.query(
                func.coalesce(func.sum(WaterLog.amount_ml), 0)
            ).filter(WaterLog.user_id == user_id, WaterLog.log_date == d).scalar() or 0
            daily_water.append(water)

            # Activity Steps
            act = ActivityLog.query.filter_by(user_id=user_id, log_date=d).first()
            daily_steps.append(act.step_count if act else 0)

            # Sleep
            slp = SleepLog.query.filter_by(user_id=user_id, log_date=d).first()
            daily_sleep.append(slp.sleep_hours if slp else 0.0)

        return {
            'labels': date_labels,
            'target_calories_line': [target_calories] * 7,
            'calories': daily_calories,
            'protein': daily_protein,
            'carbs': daily_carbs,
            'fat': daily_fat,
            'water_ml': daily_water,
            'steps': daily_steps,
            'sleep_hours': daily_sleep
        }

    @classmethod
    def generate_personalized_insights(cls, user_id):
        """
        Evaluates user's actual 7-day intake and lifestyle data against clinical rules
        to generate actionable, explainable preventive health feedback.
        """
        user = User.query.get(user_id)
        if not user:
            return []

        insights = []
        summary = cls.get_daily_summary(user_id)
        trends = cls.get_seven_day_trends(user_id)

        # 1. Protein Gap Insight
        avg_protein = sum(trends['protein']) / len(trends['protein']) if trends['protein'] else 0
        target_prot = user.nutrition_targets.target_protein_g if user.nutrition_targets else 60.0

        if avg_protein > 0 and avg_protein < (target_prot * 0.80):
            deficit = round(target_prot - avg_protein, 1)
            insights.append({
                'type': 'warning',
                'category': 'Nutrition',
                'icon': 'bi-egg-fried',
                'title': 'Sub-Optimal Protein Intake Observed',
                'observation': f"Your 7-day average protein intake is {round(avg_protein, 1)}g, which is {deficit}g below your ICMR recommended target ({target_prot}g).",
                'action': "Consider incorporating protein-dense regional staples like Sprouted Moong Kosambari, Sundal, Soya Chunks, or Paneer into your lunch and snacks."
            })
        elif avg_protein >= target_prot:
            insights.append({
                'type': 'success',
                'category': 'Nutrition',
                'icon': 'bi-check-circle-fill',
                'title': 'Nutritional Protein Target Consistently Achieved',
                'observation': f"Your 7-day average protein consumption ({round(avg_protein, 1)}g) meets your baseline metabolic requirements.",
                'action': "Maintain this balanced dietary distribution to support muscle integrity and stable blood sugar levels."
            })

        # 2. Hydration Consistency Insight
        avg_water = sum(trends['water_ml']) / len(trends['water_ml']) if trends['water_ml'] else 0
        target_water = user.nutrition_targets.target_water_ml if user.nutrition_targets else 2500.0

        if avg_water > 0 and avg_water < (target_water * 0.75):
            insights.append({
                'type': 'info',
                'category': 'Hydration',
                'icon': 'bi-droplet-half',
                'title': 'Hydration Below Recommended Volume',
                'observation': f"You averaged {int(avg_water)} ml of water daily over the past week (Target: {int(target_water)} ml).",
                'action': "Add a glass of spiced buttermilk (Majjige) or tender coconut water during morning and mid-afternoon hours."
            })

        # 3. Sleep Consistency Insight
        avg_sleep = sum(trends['sleep_hours']) / len(trends['sleep_hours']) if trends['sleep_hours'] else 0
        if avg_sleep > 0 and avg_sleep < 6.5:
            insights.append({
                'type': 'danger',
                'category': 'Sleep & Circadian',
                'icon': 'bi-moon-stars',
                'title': 'Chronic Sleep Restriction Flagged',
                'observation': f"Your average sleep duration is {round(avg_sleep, 1)} hours. Insufficient sleep (&lt;6.5 hrs) is clinically correlated with increased insulin resistance and elevated morning cortisol.",
                'action': "Aim to establish a fixed sleep window of 7.5 hours and refrain from heavy carbohydrate meals within 2 hours of bedtime."
            })

        # 4. Default welcoming insight if user has newly registered
        if not insights:
            insights.append({
                'type': 'info',
                'category': 'System Onboarding',
                'icon': 'bi-stars',
                'title': 'Baseline Profile Active',
                'observation': 'Your physiological baseline targets are initialized. As you log meals, activity, and sleep, the analytical engine will generate trend insights.',
                'action': 'Begin by logging today\'s breakfast or hydration using the Nutrition Tracker.'
            })

        return insights
