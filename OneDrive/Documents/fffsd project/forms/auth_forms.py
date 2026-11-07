"""
WTForms for User Authentication and Profile Management.
Includes strict validation, custom sanitization, and health profile inputs.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    FloatField,
    IntegerField,
    SelectField,
    SelectMultipleField,
    TextAreaField,
    SubmitField
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    NumberRange,
    Optional,
    ValidationError
)
from models import User


class LoginForm(FlaskForm):
    """User login form with remember-me capability."""
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message="Email address is required."),
            Email(message="Please provide a valid email address.")
        ],
        render_kw={"placeholder": "e.g. name@example.com", "autocomplete": "email"}
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message="Password is required.")],
        render_kw={"placeholder": "Enter your password", "autocomplete": "current-password"}
    )
    remember_me = BooleanField('Keep me signed in for 30 days')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """
    Comprehensive User Registration Form.
    Collects account credentials along with baseline physiological,
    dietary, regional, and allergy metrics for preventive healthcare.
    """
    # 1. Account Credentials
    full_name = StringField(
        'Full Name',
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
        ],
        render_kw={"placeholder": "e.g. Aarav Sharma"}
    )
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message="Email address is required."),
            Email(message="Please provide a valid email address.")
        ],
        render_kw={"placeholder": "e.g. aarav@example.com", "autocomplete": "email"}
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must contain at least 8 characters.")
        ],
        render_kw={"placeholder": "Minimum 8 characters", "autocomplete": "new-password"}
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo('password', message="Passwords do not match.")
        ],
        render_kw={"placeholder": "Re-enter your password", "autocomplete": "new-password"}
    )

    # 2. Physiological Attributes
    age = IntegerField(
        'Age (Years)',
        validators=[
            DataRequired(message="Age is required for metabolic calculations."),
            NumberRange(min=12, max=110, message="Age must be between 12 and 110.")
        ],
        render_kw={"placeholder": "e.g. 24"}
    )
    gender = SelectField(
        'Biological Gender',
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other / Prefer not to say')
        ],
        validators=[DataRequired(message="Please select your biological gender.")]
    )
    height_cm = FloatField(
        'Height (in cm)',
        validators=[
            DataRequired(message="Height is required for BMI computation."),
            NumberRange(min=100.0, max=250.0, message="Height must be between 100 and 250 cm.")
        ],
        render_kw={"placeholder": "e.g. 175"}
    )
    weight_kg = FloatField(
        'Current Weight (in kg)',
        validators=[
            DataRequired(message="Weight is required for calorie estimation."),
            NumberRange(min=30.0, max=250.0, message="Weight must be between 30 and 250 kg.")
        ],
        render_kw={"placeholder": "e.g. 68.5"}
    )

    # 3. Lifestyle & Activity Multiplier
    activity_level = SelectField(
        'Physical Activity Level',
        choices=[
            ('sedentary', 'Sedentary (Little or no exercise, desk job)'),
            ('light', 'Lightly Active (Light exercise/sports 1-3 days/week)'),
            ('moderate', 'Moderately Active (Moderate exercise/sports 3-5 days/week)'),
            ('active', 'Very Active (Hard exercise/sports 6-7 days/week)'),
            ('very_active', 'Extremely Active (Physical labor or athlete training)')
        ],
        default='sedentary'
    )

    # 4. Dietary & Regional Preferences
    dietary_preference = SelectField(
        'Dietary Classification',
        choices=[
            ('vegetarian', 'Vegetarian (Lacto-vegetarian)'),
            ('vegan', 'Vegan (Strictly plant-based)'),
            ('eggetarian', 'Eggetarian (Vegetarian + Eggs)'),
            ('non_vegetarian', 'Non-Vegetarian (Includes Poultry/Meat/Fish)')
        ],
        default='vegetarian'
    )
    regional_preference = SelectField(
        'Primary Regional Cuisine Preference',
        choices=[
            ('south_indian', 'South Indian (Idli, Dosa, Ragi Mudde, Sambar, Rasam)'),
            ('north_indian', 'North Indian (Rotis, Dals, Sabzis, Paneer)'),
            ('pan_india', 'Pan-Indian / Continental Mix')
        ],
        default='south_indian'
    )
    budget_preference = SelectField(
        'Grocery & Food Budget Tier',
        choices=[
            ('low', 'Economy / Student-friendly'),
            ('medium', 'Balanced / Moderate'),
            ('high', 'Premium / Organic produce')
        ],
        default='medium'
    )

    # 5. Food Allergies & Intolerances
    food_allergies = StringField(
        'Known Food Allergies (Comma-separated)',
        validators=[Optional()],
        render_kw={"placeholder": "e.g. peanuts, dairy, gluten, shellfish"}
    )

    # 6. Consent
    consent = BooleanField(
        'I consent to using my physiological information for preventive nutritional calculations.',
        validators=[DataRequired(message="Consent is required to generate personalized health plans.")]
    )

    submit = SubmitField('Create Personalized Account')

    def validate_email(self, field):
        """Ensure email is unique across the platform."""
        existing_user = User.query.filter_by(email=field.data.lower().strip()).first()
        if existing_user:
            raise ValidationError("An account with this email address already exists.")


class ProfileUpdateForm(FlaskForm):
    """Form allowing users to modify physiological and dietary preferences."""
    full_name = StringField(
        'Full Name',
        validators=[DataRequired(), Length(min=2, max=100)]
    )
    age = IntegerField(
        'Age',
        validators=[DataRequired(), NumberRange(min=12, max=110)]
    )
    gender = SelectField(
        'Gender',
        choices=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('other', 'Other')
        ],
        validators=[DataRequired()]
    )
    height_cm = FloatField(
        'Height (cm)',
        validators=[DataRequired(), NumberRange(min=100.0, max=250.0)]
    )
    weight_kg = FloatField(
        'Weight (kg)',
        validators=[DataRequired(), NumberRange(min=30.0, max=250.0)]
    )
    activity_level = SelectField(
        'Activity Level',
        choices=[
            ('sedentary', 'Sedentary'),
            ('light', 'Lightly Active'),
            ('moderate', 'Moderately Active'),
            ('active', 'Very Active'),
            ('very_active', 'Extremely Active')
        ]
    )
    dietary_preference = SelectField(
        'Dietary Preference',
        choices=[
            ('vegetarian', 'Vegetarian'),
            ('vegan', 'Vegan'),
            ('eggetarian', 'Eggetarian'),
            ('non_vegetarian', 'Non-Vegetarian')
        ]
    )
    regional_preference = SelectField(
        'Regional Preference',
        choices=[
            ('south_indian', 'South Indian'),
            ('north_indian', 'North Indian'),
            ('pan_india', 'Pan-Indian')
        ]
    )
    food_allergies = StringField(
        'Food Allergies (comma-separated)',
        validators=[Optional()]
    )
    dietary_restrictions = StringField(
        'Dietary Restrictions (e.g. low_sodium, low_sugar)',
        validators=[Optional()]
    )

    submit = SubmitField('Update Health Profile')


class ChangePasswordForm(FlaskForm):
    """Form to change user password."""
    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired(message="Please provide your current password.")]
    )
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message="New password is required."),
            Length(min=8, message="Password must be at least 8 characters long.")
        ]
    )
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message="Please confirm your new password."),
            EqualTo('new_password', message="Passwords do not match.")
        ]
    )
    submit = SubmitField('Update Password')
