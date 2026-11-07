"""
Recommendation Routes Blueprint.
Serves real-time deficit-filling food recommendations, cultural meal plans,
and handles one-click recommendation acceptance directly into the food log.
"""

from datetime import date
from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash
)
from flask_login import login_required, current_user
from services import RecommendationService

recommendation_bp = Blueprint('recommendation', __name__)


@recommendation_bp.route('/recommendations')
@login_required
def index():
    """Renders the Food Recommendation Engine interface."""
    meal_time = request.args.get('meal_time', 'lunch').lower()
    date_str = request.args.get('date')
    try:
        target_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        target_date = date.today()

    recommendations = RecommendationService.generate_recommendations(
        user_id=current_user.id,
        meal_time=meal_time,
        target_date=target_date,
        limit=6
    )
    deficits = RecommendationService.get_remaining_deficits(current_user.id, target_date)

    return render_template(
        'food_recommendations.html',
        recommendations=recommendations,
        deficits=deficits,
        active_meal_time=meal_time,
        target_date=target_date,
        user=current_user,
        title="Personalized Food Recommendation Engine"
    )


@recommendation_bp.route('/api/v1/recommendations/daily')
@login_required
def api_daily_recommendations():
    """REST API delivering scored regional meal recommendations."""
    meal_time = request.args.get('meal_time', 'lunch').lower()
    date_str = request.args.get('date')
    try:
        target_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        target_date = date.today()

    recommendations = RecommendationService.generate_recommendations(
        user_id=current_user.id,
        meal_time=meal_time,
        target_date=target_date,
        limit=8
    )

    return jsonify({
        'status': 'success',
        'count': len(recommendations),
        'meal_time': meal_time,
        'recommendations': recommendations
    }), 200


@recommendation_bp.route('/api/v1/recommendations/accept/<int:recommendation_id>', methods=['POST'])
@login_required
def accept_recommendation(recommendation_id):
    """Logs the recommended dish directly into the user's FoodLog."""
    food_log, error = RecommendationService.accept_recommendation(current_user.id, recommendation_id)

    if error:
        if request.form or not request.is_json:
            flash(f"Failed to log recommendation: {error}", "danger")
            return redirect(url_for('recommendation.index'))
        return jsonify({'status': 'error', 'message': error}), 400

    if request.form or not request.is_json:
        flash(f"Accepted & Logged '{food_log.food_item.food_name}' into your journal!", "success")
        return redirect(url_for('nutrition.index'))

    return jsonify({
        'status': 'success',
        'message': 'Recommendation accepted and logged into food journal',
        'log': food_log.to_dict()
    }), 201
