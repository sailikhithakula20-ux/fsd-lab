"""
Nutrition Routes Blueprint.
Manages interactive food database search, proportional meal logging,
meal category subtotals, and custom food additions.
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
from models import FoodCategory, MealType
from services import NutritionService, DashboardService

nutrition_bp = Blueprint('nutrition', __name__)


@nutrition_bp.route('/nutrition')
@login_required
def index():
    """Renders the comprehensive nutrition tracking interface."""
    date_str = request.args.get('date')
    try:
        target_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        target_date = date.today()

    categories = FoodCategory.query.order_by(FoodCategory.name.asc()).all()
    meal_types = MealType.query.order_by(MealType.id.asc()).all()
    meals_by_type = NutritionService.get_meals_by_category(current_user.id, target_date)
    daily_summary = DashboardService.get_daily_summary(current_user.id, target_date)

    return render_template(
        'nutrition.html',
        target_date=target_date,
        categories=categories,
        meal_types=meal_types,
        meals_by_type=meals_by_type,
        daily_summary=daily_summary,
        title="Smart Nutrition & Food Tracker"
    )


@nutrition_bp.route('/api/v1/nutrition/search')
@login_required
def search_foods():
    """Dynamic REST search API for food items with dietary & regional filters."""
    query = request.args.get('q', '')
    cat_id = request.args.get('category_id')
    regional_tag = request.args.get('regional_tag')
    veg_only = request.args.get('veg_only')

    is_veg = True if veg_only == 'true' else None
    category_id = int(cat_id) if cat_id and cat_id.isdigit() else None

    items = NutritionService.search_foods(
        query=query,
        category_id=category_id,
        regional_tag=regional_tag,
        is_vegetarian=is_veg,
        limit=25
    )

    return jsonify({
        'status': 'success',
        'count': len(items),
        'items': [item.to_dict() for item in items]
    }), 200


@nutrition_bp.route('/api/v1/nutrition/log', methods=['POST'])
@login_required
def log_meal():
    """REST API endpoint to log a consumed food item."""
    data = request.get_json() or request.form

    try:
        food_item_id = int(data.get('food_item_id'))
        meal_type_id = int(data.get('meal_type_id'))
        quantity_multiplier = float(data.get('quantity_multiplier', 1.0))
        date_str = data.get('log_date')
        log_date = date.fromisoformat(date_str) if date_str else date.today()

        food_log, error = NutritionService.log_meal(
            user_id=current_user.id,
            food_item_id=food_item_id,
            meal_type_id=meal_type_id,
            quantity_multiplier=quantity_multiplier,
            log_date=log_date
        )

        if error:
            return jsonify({'status': 'error', 'message': error}), 400

        # If submitted via HTML form, redirect back
        if request.form:
            flash(f"Successfully logged {food_log.food_item.food_name} ({food_log.calculated_calories} kcal).", "success")
            return redirect(url_for('nutrition.index', date=log_date.isoformat()))

        return jsonify({
            'status': 'success',
            'log': food_log.to_dict(),
            'message': 'Meal successfully recorded'
        }), 201

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@nutrition_bp.route('/api/v1/nutrition/log/<int:log_id>', methods=['DELETE', 'POST'])
@login_required
def delete_log(log_id):
    """Delete an individual food log entry."""
    success, error = NutritionService.delete_meal_log(current_user.id, log_id)

    if request.form or request.method == 'POST':
        if success:
            flash("Meal entry removed successfully.", "info")
        else:
            flash(f"Failed to remove entry: {error}", "danger")
        return redirect(url_for('nutrition.index'))

    if success:
        return jsonify({'status': 'success', 'message': 'Log deleted'}), 200
    return jsonify({'status': 'error', 'message': error}), 404


@nutrition_bp.route('/api/v1/nutrition/custom', methods=['POST'])
@login_required
def add_custom_food():
    """Endpoint allowing users to add custom dishes to the database."""
    data = request.get_json() or request.form

    item, error = NutritionService.create_custom_food(current_user.id, data)
    if error:
        if request.form:
            flash(f"Failed to create custom dish: {error}", "danger")
            return redirect(url_for('nutrition.index'))
        return jsonify({'status': 'error', 'message': error}), 400

    if request.form:
        flash(f"Custom dish '{item.food_name}' created successfully.", "success")
        return redirect(url_for('nutrition.index'))

    return jsonify({'status': 'success', 'item': item.to_dict()}), 201
