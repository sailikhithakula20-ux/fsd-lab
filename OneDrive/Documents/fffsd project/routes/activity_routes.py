"""
Activity & Lifestyle Routes: Endpoints for step counting, MET workout logging,
hydration tracking, circadian sleep metrics, and lifestyle trend visualization.
"""

from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user

from services.activity_service import ActivityService, MET_ACTIVITIES

activity_bp = Blueprint('activity', __name__)


@activity_bp.route('/activity')
@login_required
def index():
    """Main Activity & Lifestyle Hub displaying today's progress, logs, and trend charts."""
    date_str = request.args.get('date')
    target_date = date.today()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()

    summary = ActivityService.get_daily_activity_summary(current_user.id, target_date)
    weekly_trends = ActivityService.get_weekly_lifestyle_trends(current_user.id, days=7)
    user_weight = ActivityService.get_user_weight(current_user.id)

    return render_template(
        'activity.html',
        summary=summary,
        weekly_trends=weekly_trends,
        met_activities=MET_ACTIVITIES,
        user_weight=user_weight,
        selected_date=target_date.isoformat()
    )


# =============================================================================
# RESTful JSON Endpoints
# =============================================================================

@activity_bp.route('/api/v1/activity/steps', methods=['POST'])
@login_required
def api_log_steps():
    """Log or increment daily steps."""
    data = request.get_json(silent=True) or {}
    steps = data.get('steps', 0)
    mode = data.get('mode', 'set')  # 'set' or 'add'
    log_date = data.get('date', None)

    try:
        steps_val = int(steps)
        if steps_val < 0:
            return jsonify({'success': False, 'error': 'Step count must be non-negative.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid step count provided.'}), 400

    entry = ActivityService.log_steps(
        user_id=current_user.id,
        steps=steps_val,
        log_date=log_date,
        append=(mode == 'add')
    )

    summary = ActivityService.get_daily_activity_summary(current_user.id, entry.log_date)
    return jsonify({
        'success': True,
        'message': f"Updated steps to {entry.step_count:,}.",
        'data': entry.to_dict(),
        'summary': summary['steps'],
        'calories_burned': summary['calories_burned']
    })


@activity_bp.route('/api/v1/activity/water', methods=['POST'])
@login_required
def api_log_water():
    """Log water intake in milliliters."""
    data = request.get_json(silent=True) or {}
    amount_ml = data.get('amount_ml', 0)
    log_date = data.get('date', None)

    try:
        amount_val = int(amount_ml)
        if amount_val <= 0 or amount_val > 5000:
            return jsonify({'success': False, 'error': 'Water amount must be between 1 and 5000 ml.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid water volume provided.'}), 400

    entry = ActivityService.log_water(
        user_id=current_user.id,
        amount_ml=amount_val,
        log_date=log_date
    )

    summary = ActivityService.get_daily_activity_summary(current_user.id, entry.log_date)
    return jsonify({
        'success': True,
        'message': f"Logged +{amount_val} ml of hydration.",
        'entry': entry.to_dict(),
        'hydration': summary['hydration']
    })


@activity_bp.route('/api/v1/activity/water/<int:log_id>', methods=['DELETE'])
@login_required
def api_delete_water(log_id):
    """Delete a specific water intake entry."""
    success = ActivityService.delete_water_log(current_user.id, log_id)
    if not success:
        return jsonify({'success': False, 'error': 'Water log not found or unauthorized.'}), 404

    summary = ActivityService.get_daily_activity_summary(current_user.id)
    return jsonify({
        'success': True,
        'message': 'Hydration log removed.',
        'hydration': summary['hydration']
    })


@activity_bp.route('/api/v1/activity/sleep', methods=['POST'])
@login_required
def api_log_sleep():
    """Log sleep duration and quality score."""
    data = request.get_json(silent=True) or {}
    sleep_hours = data.get('sleep_hours', 0)
    quality_score = data.get('quality_score', 75)
    log_date = data.get('date', None)

    try:
        hours_val = float(sleep_hours)
        if hours_val < 0 or hours_val > 24:
            return jsonify({'success': False, 'error': 'Sleep duration must be between 0 and 24 hours.'}), 400
        quality_val = int(quality_score)
        if quality_val < 1 or quality_val > 100:
            return jsonify({'success': False, 'error': 'Quality score must be between 1 and 100.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid sleep values provided.'}), 400

    entry = ActivityService.log_sleep(
        user_id=current_user.id,
        sleep_hours=hours_val,
        sleep_quality_score=quality_val,
        log_date=log_date
    )

    summary = ActivityService.get_daily_activity_summary(current_user.id, entry.log_date)
    return jsonify({
        'success': True,
        'message': f"Recorded {hours_val}h sleep with quality score of {quality_val}.",
        'data': entry.to_dict(),
        'sleep': summary['sleep']
    })


@activity_bp.route('/api/v1/activity/exercise', methods=['POST'])
@login_required
def api_log_exercise():
    """Log structured workout session with MET energy calculation."""
    data = request.get_json(silent=True) or {}
    exercise_type = data.get('exercise_type', '').strip()
    duration_minutes = data.get('duration_minutes', 0)
    log_date = data.get('date', None)

    if exercise_type not in MET_ACTIVITIES:
        return jsonify({
            'success': False,
            'error': f"Unknown exercise type '{exercise_type}'. Must be one of available activities."
        }), 400

    try:
        duration_val = int(duration_minutes)
        if duration_val <= 0 or duration_val > 600:
            return jsonify({'success': False, 'error': 'Duration must be between 1 and 600 minutes.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid duration specified.'}), 400

    entry = ActivityService.log_exercise(
        user_id=current_user.id,
        exercise_type=exercise_type,
        duration_minutes=duration_val,
        log_date=log_date
    )

    summary = ActivityService.get_daily_activity_summary(current_user.id, entry.log_date)
    return jsonify({
        'success': True,
        'message': f"Logged {duration_val} mins of {MET_ACTIVITIES[exercise_type]['name']} (~{entry.estimated_calories_burned} kcal).",
        'entry': entry.to_dict(),
        'exercises': summary['exercises'],
        'calories_burned': summary['calories_burned']
    })


@activity_bp.route('/api/v1/activity/exercise/<int:exercise_id>', methods=['DELETE'])
@login_required
def api_delete_exercise(exercise_id):
    """Delete a recorded workout session."""
    success = ActivityService.delete_exercise(current_user.id, exercise_id)
    if not success:
        return jsonify({'success': False, 'error': 'Exercise entry not found or unauthorized.'}), 404

    summary = ActivityService.get_daily_activity_summary(current_user.id)
    return jsonify({
        'success': True,
        'message': 'Exercise session removed.',
        'exercises': summary['exercises'],
        'calories_burned': summary['calories_burned']
    })


@activity_bp.route('/api/v1/activity/met-preview', methods=['GET'])
@login_required
def api_met_preview():
    """Real-time calculation preview for MET workouts given duration and activity."""
    exercise_type = request.args.get('type', 'walking')
    try:
        duration = int(request.args.get('duration', 30))
    except (ValueError, TypeError):
        duration = 30

    met_item = MET_ACTIVITIES.get(exercise_type, MET_ACTIVITIES['walking'])
    weight = ActivityService.get_user_weight(current_user.id)
    calories = ActivityService.calculate_met_calories(
        met_value=met_item['met'],
        duration_minutes=duration,
        weight_kg=weight
    )

    return jsonify({
        'success': True,
        'exercise_type': exercise_type,
        'met': met_item['met'],
        'user_weight_kg': weight,
        'duration_minutes': duration,
        'estimated_calories': calories
    })


@activity_bp.route('/api/v1/activity/trends', methods=['GET'])
@login_required
def api_trends():
    """Retrieve 7-day lifestyle chronological dataset for client-side visualizations."""
    try:
        days = int(request.args.get('days', 7))
        days = min(30, max(3, days))
    except (ValueError, TypeError):
        days = 7

    trends = ActivityService.get_weekly_lifestyle_trends(current_user.id, days=days)
    return jsonify({'success': True, 'trends': trends})
