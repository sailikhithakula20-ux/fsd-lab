from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.nutrition_routes import nutrition_bp
from routes.recommendation_routes import recommendation_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'nutrition_bp',
    'recommendation_bp'
]
