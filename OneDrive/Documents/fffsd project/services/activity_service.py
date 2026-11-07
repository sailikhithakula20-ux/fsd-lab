"""
ActivityService: Scientific Lifestyle, Movement & Metabolic Energy Expenditure Engine.
Implements the Compendium of Physical Activities (MET) formulation, step kinematics,
weight-adjusted hydration targets, and circadian sleep analytics.
"""

from datetime import date, datetime, timedelta
from sqlalchemy import func
from models import (
    db,
    User,
    UserProfile,
    ActivityLog,
    WaterLog,
    SleepLog,
    ExerciseLog,
    UserGoal
)

# Standardized Compendium of Physical Activities (Ainsworth et al.)
# Formula: Calories = Duration(min) * [MET * 3.5 * Weight(kg) / 200]
MET_ACTIVITIES = {
    'walking': {
        'name': 'Moderate Walking (4.8 km/h)',
        'met': 3.5,
        'category': 'Cardio',
        'icon': 'bi-person-walking'
    },
    'brisk_walking': {
        'name': 'Brisk Walking (6.0 km/h)',
        'met': 4.5,
        'category': 'Cardio',
        'icon': 'bi-person-walking'
    },
    'running_jog': {
        'name': 'Running / Jogging (8.0 km/h)',
        'met': 8.0,
        'category': 'Cardio',
        'icon': 'bi-lightning-charge'
    },
    'running_fast': {
        'name': 'Vigorous Running (11.0 km/h)',
        'met': 11.0,
        'category': 'Cardio',
        'icon': 'bi-lightning-charge-fill'
    },
    'cycling': {
        'name': 'Cycling (Moderate 16-19 km/h)',
        'met': 6.0,
        'category': 'Cardio',
        'icon': 'bi-bicycle'
    },
    'cycling_vigorous': {
        'name': 'Cycling (Vigorous >20 km/h)',
        'met': 8.5,
        'category': 'Cardio',
        'icon': 'bi-bicycle'
    },
    'swimming': {
        'name': 'Swimming (Freestyle, Moderate)',
        'met': 6.0,
        'category': 'Aquatics',
        'icon': 'bi-water'
    },
    'swimming_vigorous': {
        'name': 'Swimming (Vigorous Lap Training)',
        'met': 8.0,
        'category': 'Aquatics',
        'icon': 'bi-water'
    },
    'yoga': {
        'name': 'Gentle / Hatha Yoga',
        'met': 2.5,
        'category': 'Mind-Body',
        'icon': 'bi-flower1'
    },
    'vinyasa_yoga': {
        'name': 'Power / Vinyasa Yoga',
        'met': 4.0,
        'category': 'Mind-Body',
        'icon': 'bi-flower2'
    },
    'strength_training': {
        'name': 'Resistance & Weight Training',
        'met': 5.0,
        'category': 'Strength',
        'icon': 'bi-shield-shaded'
    },
    'hiit': {
        'name': 'HIIT / Functional Circuit',
        'met': 8.5,
        'category': 'Conditioning',
        'icon': 'bi-fire'
    },
    'badminton': {
        'name': 'Badminton (Singles/Doubles)',
        'met': 5.5,
        'category': 'Sports',
        'icon': 'bi-circle-half'
    },
    'jump_rope': {
        'name': 'Jump Rope / Skipping (Moderate)',
        'met': 10.0,
        'category': 'Conditioning',
        'icon': 'bi-arrow-repeat'
    },
    'pilates': {
        'name': 'Pilates / Core Matwork',
        'met': 3.5,
        'category': 'Mind-Body',
        'icon': 'bi-heart'
    },
    'cricket': {
        'name': 'Cricket (Batting / Bowling / Fielding)',
        'met': 5.0,
        'category': 'Sports',
        'icon': 'bi-trophy'
    }
}


class ActivityService:
    """Core domain service for physical activity, hydration, sleep, and MET calculation."""

    @staticmethod
    def calculate_met_calories(met_value, duration_minutes, weight_kg=70.0):
        """
        Calculate metabolic energy expenditure in kcal:
        Calories = Duration (min) * [MET * 3.5 * Weight (kg) / 200]
        """
        if duration_minutes <= 0 or weight_kg <= 0 or met_value <= 0:
            return 0.0
        calories = duration_minutes * (met_value * 3.5 * weight_kg / 200.0)
        return round(float(calories), 1)

    @classmethod
    def get_user_weight(cls, user_id):
        """Safely retrieve user weight in kg from profile, fallback to 70.0 kg."""
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if profile and profile.weight_kg and profile.weight_kg > 0:
            return float(profile.weight_kg)
        return 70.0

    @classmethod
    def get_hydration_target(cls, user_id):
        """
        Calculate recommended daily water intake:
        Clinical standard: ~35 ml per kg body weight, clamped between 2000 ml and 4500 ml.
        """
        weight = cls.get_user_weight(user_id)
        target_ml = int(round(weight * 35))
        return max(2000, min(target_ml, 4500))

    # =========================================================================
    # Step & Movement Tracking
    # =========================================================================

    @classmethod
    def log_steps(cls, user_id, steps, log_date=None, append=False):
        """
        Log or increment daily step count.
        Calculates distance (0.00078 km/step) and step-based calories (0.04 kcal/step approx).
        Syncs total daily calories burned with any existing exercise sessions.
        """
        if log_date is None:
            log_date = date.today()
        elif isinstance(log_date, str):
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()

        steps = max(0, int(steps))
        user_weight = cls.get_user_weight(user_id)

        activity_entry = ActivityLog.query.filter_by(user_id=user_id, log_date=log_date).first()
        if not activity_entry:
            activity_entry = ActivityLog(
                user_id=user_id,
                log_date=log_date,
                step_count=0,
                distance_km=0.0,
                calories_burned=0.0
            )
            db.session.add(activity_entry)

        if append:
            activity_entry.step_count += steps
        else:
            activity_entry.step_count = steps

        # Kinematic estimations
        activity_entry.distance_km = round(activity_entry.step_count * 0.00078, 2)
        step_calories = round(activity_entry.step_count * (user_weight * 0.045 / 70.0), 1)

        # Include structured exercise calories for that day
        exercise_burn = db.session.query(
            func.coalesce(func.sum(ExerciseLog.estimated_calories_burned), 0.0)
        ).filter(
            ExerciseLog.user_id == user_id,
            ExerciseLog.log_date == log_date
        ).scalar() or 0.0

        activity_entry.calories_burned = round(step_calories + float(exercise_burn), 1)
        db.session.commit()

        return activity_entry

    # =========================================================================
    # Structured Exercise Logging (MET Engine)
    # =========================================================================

    @classmethod
    def log_exercise(cls, user_id, exercise_type, duration_minutes, log_date=None):
        """
        Log structured physical workout using MET formulation.
        Appends session to ExerciseLog and updates daily ActivityLog active burn.
        """
        if log_date is None:
            log_date = date.today()
        elif isinstance(log_date, str):
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()

        duration_minutes = max(1, int(duration_minutes))
        met_data = MET_ACTIVITIES.get(exercise_type, MET_ACTIVITIES['walking'])
        weight = cls.get_user_weight(user_id)

        calories_burned = cls.calculate_met_calories(
            met_value=met_data['met'],
            duration_minutes=duration_minutes,
            weight_kg=weight
        )

        exercise_entry = ExerciseLog(
            user_id=user_id,
            log_date=log_date,
            exercise_type=exercise_type,
            duration_minutes=duration_minutes,
            estimated_calories_burned=calories_burned
        )
        db.session.add(exercise_entry)
        db.session.commit()

        # Recalculate and update daily ActivityLog total active burn
        cls._refresh_daily_activity_burn(user_id, log_date)

        return exercise_entry

    @classmethod
    def delete_exercise(cls, user_id, exercise_id):
        """Delete an exercise log and sync active burn in ActivityLog."""
        exercise = ExerciseLog.query.filter_by(id=exercise_id, user_id=user_id).first()
        if not exercise:
            return False

        log_date = exercise.log_date
        db.session.delete(exercise)
        db.session.commit()

        cls._refresh_daily_activity_burn(user_id, log_date)
        return True

    @classmethod
    def _refresh_daily_activity_burn(cls, user_id, log_date):
        """Recalculate step burn + exercise burn and update ActivityLog."""
        activity_entry = ActivityLog.query.filter_by(user_id=user_id, log_date=log_date).first()
        if not activity_entry:
            activity_entry = ActivityLog(
                user_id=user_id,
                log_date=log_date,
                step_count=0,
                distance_km=0.0,
                calories_burned=0.0
            )
            db.session.add(activity_entry)

        user_weight = cls.get_user_weight(user_id)
        step_calories = round(activity_entry.step_count * (user_weight * 0.045 / 70.0), 1)

        exercise_burn = db.session.query(
            func.coalesce(func.sum(ExerciseLog.estimated_calories_burned), 0.0)
        ).filter(
            ExerciseLog.user_id == user_id,
            ExerciseLog.log_date == log_date
        ).scalar() or 0.0

        activity_entry.calories_burned = round(step_calories + float(exercise_burn), 1)
        db.session.commit()

    # =========================================================================
    # Hydration Tracking
    # =========================================================================

    @classmethod
    def log_water(cls, user_id, amount_ml, log_date=None):
        """Record an intake of water in milliliters."""
        if log_date is None:
            log_date = date.today()
        elif isinstance(log_date, str):
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()

        amount_ml = max(1, int(amount_ml))
        water_entry = WaterLog(
            user_id=user_id,
            log_date=log_date,
            amount_ml=amount_ml
        )
        db.session.add(water_entry)
        db.session.commit()
        return water_entry

    @classmethod
    def delete_water_log(cls, user_id, log_id):
        """Delete an individual water intake entry."""
        entry = WaterLog.query.filter_by(id=log_id, user_id=user_id).first()
        if not entry:
            return False
        db.session.delete(entry)
        db.session.commit()
        return True

    # =========================================================================
    # Sleep Tracking & Circadian Quality Assessment
    # =========================================================================

    @classmethod
    def log_sleep(cls, user_id, sleep_hours, sleep_quality_score=75, log_date=None):
        """
        Record or update sleep duration and subjective quality score (1-100).
        Upserts SleepLog on unique constraint (user_id, log_date).
        """
        if log_date is None:
            log_date = date.today()
        elif isinstance(log_date, str):
            log_date = datetime.strptime(log_date, '%Y-%m-%d').date()

        sleep_hours = max(0.0, min(float(sleep_hours), 24.0))
        quality = max(1, min(int(sleep_quality_score), 100))

        sleep_entry = SleepLog.query.filter_by(user_id=user_id, log_date=log_date).first()
        if not sleep_entry:
            sleep_entry = SleepLog(
                user_id=user_id,
                log_date=log_date,
                sleep_hours=sleep_hours,
                sleep_quality_score=quality
            )
            db.session.add(sleep_entry)
        else:
            sleep_entry.sleep_hours = sleep_hours
            sleep_entry.sleep_quality_score = quality

        db.session.commit()
        return sleep_entry

    @staticmethod
    def get_sleep_evaluation(hours, quality_score):
        """Return qualitative circadian sleep assessment and feedback."""
        if hours < 6.0:
            status = 'Sleep Deficit'
            badge_class = 'bg-danger'
            advice = 'Your sleep duration is below the recommended 7-9 hours. Chronic debt affects insulin sensitivity and cortisol.'
        elif hours > 9.5:
            status = 'Prolonged Rest'
            badge_class = 'bg-warning text-dark'
            advice = 'Slightly elevated sleep duration; ensure daytime physical activity and circadian sunlight exposure.'
        elif quality_score >= 80:
            status = 'Deep & Restorative'
            badge_class = 'bg-success'
            advice = 'Optimal regenerative sleep architecture supporting cellular recovery and metabolic homeostasis.'
        else:
            status = 'Adequate Duration'
            badge_class = 'bg-info text-dark'
            advice = 'Good sleep duration. Consider winding down screen time 45 minutes before sleep to elevate delta wave quality.'

        return {
            'status': status,
            'badge_class': badge_class,
            'advice': advice
        }

    # =========================================================================
    # Aggregated Daily & Temporal Summaries
    # =========================================================================

    @classmethod
    def get_daily_activity_summary(cls, user_id, target_date=None):
        """
        Consolidate all lifestyle markers for a given date:
        - Steps, distance, active calories burned
        - Hydration total vs target
        - Sleep duration and quality score
        - List of structured workouts
        - List of individual water intake logs
        """
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        # 1. Activity Log
        activity = ActivityLog.query.filter_by(user_id=user_id, log_date=target_date).first()
        steps = activity.step_count if activity else 0
        distance_km = activity.distance_km if activity else 0.0
        calories_burned = activity.calories_burned if activity else 0.0

        step_target = 10000
        step_percent = min(100, int((steps / step_target) * 100)) if step_target > 0 else 0

        # 2. Water Logs
        water_logs = WaterLog.query.filter_by(
            user_id=user_id,
            log_date=target_date
        ).order_by(WaterLog.logged_at.desc()).all()

        water_consumed_ml = sum(w.amount_ml for w in water_logs)
        water_target_ml = cls.get_hydration_target(user_id)
        water_percent = min(100, int((water_consumed_ml / water_target_ml) * 100)) if water_target_ml > 0 else 0

        # 3. Sleep Log
        sleep = SleepLog.query.filter_by(user_id=user_id, log_date=target_date).first()
        sleep_hours = sleep.sleep_hours if sleep else 0.0
        sleep_quality = sleep.sleep_quality_score if sleep else 0
        sleep_target_hours = 8.0
        sleep_percent = min(100, int((sleep_hours / sleep_target_hours) * 100)) if sleep_hours > 0 else 0
        sleep_eval = cls.get_sleep_evaluation(sleep_hours, sleep_quality) if sleep_hours > 0 else {
            'status': 'Not Logged',
            'badge_class': 'bg-secondary',
            'advice': 'Record last night\'s rest to evaluate circadian restoration.'
        }

        # 4. Exercise Sessions
        exercises = ExerciseLog.query.filter_by(
            user_id=user_id,
            log_date=target_date
        ).order_by(ExerciseLog.logged_at.desc()).all()

        exercise_minutes_total = sum(e.duration_minutes for e in exercises)
        exercise_calories_total = sum(e.estimated_calories_burned for e in exercises)

        formatted_exercises = []
        for ex in exercises:
            meta = MET_ACTIVITIES.get(ex.exercise_type, {
                'name': ex.exercise_type.replace('_', ' ').title(),
                'category': 'General',
                'icon': 'bi-activity'
            })
            formatted_exercises.append({
                'id': ex.id,
                'type_key': ex.exercise_type,
                'name': meta['name'],
                'category': meta['category'],
                'icon': meta['icon'],
                'duration_minutes': ex.duration_minutes,
                'calories_burned': ex.estimated_calories_burned,
                'logged_at': ex.logged_at.strftime('%H:%M')
            })

        return {
            'target_date': target_date.isoformat(),
            'target_date_formatted': target_date.strftime('%A, %B %d, %Y'),
            'steps': {
                'count': steps,
                'target': step_target,
                'percent': step_percent,
                'distance_km': distance_km
            },
            'calories_burned': {
                'total': calories_burned,
                'from_exercise': round(exercise_calories_total, 1),
                'total_exercise_minutes': exercise_minutes_total
            },
            'hydration': {
                'consumed_ml': water_consumed_ml,
                'target_ml': water_target_ml,
                'percent': water_percent,
                'remaining_ml': max(0, water_target_ml - water_consumed_ml),
                'logs': [w.to_dict() for w in water_logs]
            },
            'sleep': {
                'hours': sleep_hours,
                'quality_score': sleep_quality,
                'percent': sleep_percent,
                'status': sleep_eval['status'],
                'badge_class': sleep_eval['badge_class'],
                'advice': sleep_eval['advice'],
                'is_logged': sleep is not None
            },
            'exercises': formatted_exercises
        }

    @classmethod
    def get_weekly_lifestyle_trends(cls, user_id, days=7):
        """
        Generate chronological 7-day time series data for Steps, Water, Sleep, and Active Calories.
        Returns labels and parallel numerical arrays suitable for Chart.js visualization.
        """
        today = date.today()
        start_date = today - timedelta(days=days - 1)

        labels = []
        step_data = []
        water_data = []
        sleep_data = []
        calorie_data = []

        for i in range(days):
            current_date = start_date + timedelta(days=i)
            labels.append(current_date.strftime('%a (%b %d)'))

            # Steps and calories
            act = ActivityLog.query.filter_by(user_id=user_id, log_date=current_date).first()
            step_data.append(act.step_count if act else 0)
            calorie_data.append(act.calories_burned if act else 0.0)

            # Water
            w_sum = db.session.query(
                func.coalesce(func.sum(WaterLog.amount_ml), 0)
            ).filter(
                WaterLog.user_id == user_id,
                WaterLog.log_date == current_date
            ).scalar() or 0
            water_data.append(int(w_sum))

            # Sleep
            slp = SleepLog.query.filter_by(user_id=user_id, log_date=current_date).first()
            sleep_data.append(slp.sleep_hours if slp else 0.0)

        return {
            'labels': labels,
            'steps': step_data,
            'water_ml': water_data,
            'sleep_hours': sleep_data,
            'active_calories': calorie_data
        }
