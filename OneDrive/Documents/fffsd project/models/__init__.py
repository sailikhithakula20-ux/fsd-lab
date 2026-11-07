from flask_sqlalchemy import SQLAlchemy

# Initialize shared SQLAlchemy database instance
db = SQLAlchemy()

# Import all models to ensure declarative mappings are registered
from models.user import User, UserProfile, AdminUser
from models.nutrition import (
    FoodCategory,
    FoodItem,
    MealType,
    FoodLog,
    NutritionTarget,
    Recommendation
)
from models.activity import (
    ActivityLog,
    WaterLog,
    SleepLog,
    ExerciseLog,
    UserGoal
)
from models.health import (
    HealthAssessment,
    MLPredictionResult,
    ChatHistory,
    HealthArticle,
    ArticleBookmark
)

__all__ = [
    'db',
    'User',
    'UserProfile',
    'AdminUser',
    'FoodCategory',
    'FoodItem',
    'MealType',
    'FoodLog',
    'NutritionTarget',
    'Recommendation',
    'ActivityLog',
    'WaterLog',
    'SleepLog',
    'ExerciseLog',
    'UserGoal',
    'HealthAssessment',
    'MLPredictionResult',
    'ChatHistory',
    'HealthArticle',
    'ArticleBookmark'
]
