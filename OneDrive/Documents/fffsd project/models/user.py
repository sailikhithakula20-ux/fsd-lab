from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class User(UserMixin, db.Model):
    """Core user account model."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' or 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 1:1 relationship with UserProfile
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    # 1:1 relationship with NutritionTarget
    nutrition_targets = db.relationship('NutritionTarget', backref='user', uselist=False, cascade='all, delete-orphan')

    # 1:N relationships
    food_logs = db.relationship('FoodLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    water_logs = db.relationship('WaterLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    sleep_logs = db.relationship('SleepLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    exercise_logs = db.relationship('ExerciseLog', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    goals = db.relationship('UserGoal', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    assessments = db.relationship('HealthAssessment', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    predictions = db.relationship('MLPredictionResult', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    recommendations = db.relationship('Recommendation', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatHistory', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    bookmarks = db.relationship('ArticleBookmark', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set user password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify user password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user has administrative privileges."""
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"


class UserProfile(db.Model):
    """Detailed health, dietary, and physical profile of a user."""
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)  # 'male', 'female', 'other'
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    bmi = db.Column(db.Float, nullable=True)
    
    # Lifestyle & Dietary attributes
    activity_level = db.Column(db.String(30), default='sedentary')  # sedentary, light, moderate, active, very_active
    dietary_preference = db.Column(db.String(30), default='vegetarian')  # vegetarian, vegan, eggetarian, non_vegetarian
    regional_preference = db.Column(db.String(30), default='south_indian')  # south_indian, north_indian, etc.
    budget_preference = db.Column(db.String(20), default='medium')  # low, medium, high
    
    # Allergies and Medical flags (stored as comma-separated or JSON string)
    food_allergies = db.Column(db.Text, default='')  # e.g. "nuts, dairy, gluten"
    dietary_restrictions = db.Column(db.Text, default='')  # e.g. "low_sodium, no_sugar"
    existing_conditions = db.Column(db.Text, default='')  # e.g. "pre_diabetes, hypertension"
    data_sharing_consent = db.Column(db.Boolean, default=True, nullable=False)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def calculate_bmi(self):
        """Calculate BMI = weight(kg) / (height(m))^2."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = self.height_cm / 100.0
            self.bmi = round(self.weight_kg / (height_m * height_m), 2)
            return self.bmi
        return None

    def get_bmi_category(self):
        """Return clinical BMI category description."""
        if not self.bmi:
            self.calculate_bmi()
        if not self.bmi:
            return "Unknown"
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25.0 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obese"

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'age': self.age,
            'gender': self.gender,
            'height_cm': self.height_cm,
            'weight_kg': self.weight_kg,
            'bmi': self.bmi or self.calculate_bmi(),
            'bmi_category': self.get_bmi_category(),
            'activity_level': self.activity_level,
            'dietary_preference': self.dietary_preference,
            'regional_preference': self.regional_preference,
            'food_allergies': [a.strip() for a in self.food_allergies.split(',') if a.strip()] if self.food_allergies else [],
            'dietary_restrictions': self.dietary_restrictions,
            'existing_conditions': self.existing_conditions
        }

    def __repr__(self):
        return f"<UserProfile user_id={self.user_id} bmi={self.bmi}>"


class AdminUser(db.Model):
    """Administrator credentials and audit log."""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    articles = db.relationship('HealthArticle', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<AdminUser username='{self.username}'>"
