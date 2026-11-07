"""
Dashboard Routes Blueprint.
Renders the authenticated user's personalized health overview and provides
REST API endpoints for Chart.js time-series analytics.
"""

from flask import (
    Blueprint,
    render_template,
    jsonify,
    request
)
from flask_login import login_required, current_user
from services import DashboardService

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    """Renders the comprehensive health analytics and tracking dashboard."""
    summary = DashboardService.get_daily_summary(current_user.id)
    insights = DashboardService.generate_personalized_insights(current_user.id)

    return render_template(
        'dashboard.html',
        summary=summary,
        insights=insights,
        user=current_user,
        title="Personalized Health Dashboard"
    )


@dashboard_bp.route('/api/v1/dashboard/summary')
@login_required
def api_dashboard_summary():
    """REST API delivering daily aggregations and 7-day Chart.js datasets."""
    summary = DashboardService.get_daily_summary(current_user.id)
    trends = DashboardService.get_seven_day_trends(current_user.id)
    insights = DashboardService.generate_personalized_insights(current_user.id)

    return jsonify({
        'status': 'success',
        'summary': summary,
        'trends': trends,
        'insights': insights
    }), 200
