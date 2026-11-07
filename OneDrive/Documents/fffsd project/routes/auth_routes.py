"""
Authentication and Profile Management Routes Blueprint.
Handles user registration, login, logout, profile updates, and password changes.
"""

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from forms import (
    LoginForm,
    RegistrationForm,
    ProfileUpdateForm,
    ChangePasswordForm
)
from services import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration view with full physiological onboarding."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user, error = AuthService.register_user(form.data)
        if user:
            login_user(user, remember=True)
            flash(
                f"Welcome to your Preventive Healthcare Portal, {user.full_name}! "
                "Your personalized nutritional baseline has been initialized.",
                "success"
            )
            return redirect(url_for('dashboard.index'))
        else:
            flash(f"Registration failed: {error}", "danger")

    return render_template('register.html', form=form, title="Create Account")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User authentication view."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.authenticate_user(form.email.data, form.password.data)
        if user:
            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.full_name}.", "success")
            next_page = request.args.get('next')
            # Ensure next_page is safe relative URL
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash("Invalid email address or password. Please verify your credentials.", "danger")

    return render_template('login.html', form=form, title="Sign In")


@auth_bp.route('/logout')
@login_required
def logout():
    """User session termination."""
    logout_user()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User physiological profile view and update controller."""
    profile_form = ProfileUpdateForm(obj=current_user.profile)
    password_form = ChangePasswordForm()

    if request.method == 'GET':
        profile_form.full_name.data = current_user.full_name

    if profile_form.submit.data and profile_form.validate_on_submit():
        success, error = AuthService.update_user_profile(current_user.id, profile_form.data)
        if success:
            flash("Your health profile and nutritional targets have been updated successfully.", "success")
            return redirect(url_for('auth.profile'))
        else:
            flash(f"Failed to update profile: {error}", "danger")

    return render_template(
        'profile.html',
        profile_form=profile_form,
        password_form=password_form,
        user=current_user,
        title="Health Profile & Settings"
    )


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Controller for updating account password."""
    password_form = ChangePasswordForm()
    if password_form.validate_on_submit():
        success, error = AuthService.change_password(
            user=current_user,
            current_password=password_form.current_password.data,
            new_password=password_form.new_password.data
        )
        if success:
            flash("Your password has been updated successfully.", "success")
        else:
            flash(f"Password update failed: {error}", "danger")
    else:
        for field, errors in password_form.errors.items():
            for err in errors:
                flash(f"{field.replace('_', ' ').title()}: {err}", "danger")

    return redirect(url_for('auth.profile'))


@auth_bp.route('/api/v1/auth/status')
def auth_status():
    """REST API endpoint to verify current user authentication state."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict(),
            'profile': current_user.profile.to_dict() if current_user.profile else None
        }), 200
    return jsonify({'authenticated': False}), 200
