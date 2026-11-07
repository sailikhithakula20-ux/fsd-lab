from datetime import datetime, date
from models import db


class ActivityLog(db.Model):
    """Daily physical step count and movement tracker."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    
    step_count = db.Column(db.Integer, default=0, nullable=False)
    distance_km = db.Column(db.Float, default=0.0, nullable=False)
    calories_burned = db.Column(db.Float, default=0.0, nullable=False)
    
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'log_date', name='uq_user_activity_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'log_date': self.log_date.isoformat(),
            'step_count': self.step_count,
            'distance_km': self.distance_km,
            'calories_burned': self.calories_burned
        }

    def __repr__(self):
        return f"<ActivityLog user_id={self.user_id} date={self.log_date} steps={self.step_count}>"


class WaterLog(db.Model):
    """Hydration tracker recording water intake in milliliters."""
    __tablename__ = 'water_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    
    amount_ml = db.Column(db.Integer, default=0, nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'log_date': self.log_date.isoformat(),
            'amount_ml': self.amount_ml,
            'logged_at': self.logged_at.isoformat()
        }

    def __repr__(self):
        return f"<WaterLog user_id={self.user_id} date={self.log_date} ml={self.amount_ml}>"


class SleepLog(db.Model):
    """Sleep duration and quality tracker."""
    __tablename__ = 'sleep_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    
    sleep_hours = db.Column(db.Float, default=7.0, nullable=False)
    sleep_quality_score = db.Column(db.Integer, default=75, nullable=False)  # 1 to 100
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'log_date', name='uq_user_sleep_date'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'log_date': self.log_date.isoformat(),
            'sleep_hours': self.sleep_hours,
            'sleep_quality_score': self.sleep_quality_score
        }

    def __repr__(self):
        return f"<SleepLog user_id={self.user_id} date={self.log_date} hours={self.sleep_hours}>"


class ExerciseLog(db.Model):
    """Specific structured workout / exercise sessions."""
    __tablename__ = 'exercise_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    log_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    
    exercise_type = db.Column(db.String(50), nullable=False)  # walking, running, yoga, strength, cycling
    duration_minutes = db.Column(db.Integer, nullable=False)
    estimated_calories_burned = db.Column(db.Float, default=0.0, nullable=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'log_date': self.log_date.isoformat(),
            'exercise_type': self.exercise_type,
            'duration_minutes': self.duration_minutes,
            'estimated_calories_burned': self.estimated_calories_burned
        }

    def __repr__(self):
        return f"<ExerciseLog user_id={self.user_id} type='{self.exercise_type}' min={self.duration_minutes}>"


class UserGoal(db.Model):
    """Personalized health and weight goals."""
    __tablename__ = 'user_goals'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    goal_type = db.Column(db.String(50), default='maintenance', nullable=False)  # weight_loss, weight_gain, maintenance, muscle_building
    target_weight_kg = db.Column(db.Float, nullable=True)
    target_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)  # active, achieved, paused
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_type': self.goal_type,
            'target_weight_kg': self.target_weight_kg,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'status': self.status
        }

    def __repr__(self):
        return f"<UserGoal user_id={self.user_id} type='{self.goal_type}'>"
