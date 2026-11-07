"""
Flask Application Factory for Preventive Healthcare & Nutrition Management System.
Implements modular Blueprints, Flask-Login authentication, CSRF protection,
and database lifecycle management.
"""

import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect

from config import config_by_name
from models import db, User

# Global extension instances
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Application factory for initializing the Flask application."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, 'default'))

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)

    # Initialize LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please sign in to access this healthcare module."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        """User loader callback for Flask-Login."""
        return User.query.get(int(user_id))

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.nutrition_routes import nutrition_bp
    from routes.recommendation_routes import recommendation_bp
    from routes.activity_routes import activity_bp
    from routes.prediction_routes import prediction_bp
    from routes.ai_routes import ai_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(activity_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(ai_bp)

    # Root / Landing page route with 3D DNA hero & storytelling rail
    @app.route('/')
    def landing():
        return render_template('index.html')

    # Context processors for global template variables
    @app.context_processor
    def inject_global_template_vars():
        return {
            'app_name': app.config.get('APP_NAME', 'AuraHealth AI'),
            'current_year': 2026
        }

    # Global Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', title="Page Not Found"), 404

    @app.errorhandler(403)
    def forbidden_access(e):
        return render_template('base.html', title="Access Forbidden"), 403

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('base.html', title="Server Error"), 500

    return app


if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
