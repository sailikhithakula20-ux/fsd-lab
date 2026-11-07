from datetime import datetime
import json
from models import db


class HealthAssessment(db.Model):
    """Clinical assessment inputs submitted by the user for ML inference."""
    __tablename__ = 'health_assessments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assessment_type = db.Column(db.String(50), nullable=False)  # diabetes, cardiovascular
    input_payload = db.Column(db.Text, nullable=False)  # JSON-encoded features
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    prediction = db.relationship('MLPredictionResult', backref='assessment', uselist=False, cascade='all, delete-orphan')

    def get_inputs(self):
        try:
            return json.loads(self.input_payload)
        except Exception:
            return {}

    def set_inputs(self, data_dict):
        self.input_payload = json.dumps(data_dict)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'assessment_type': self.assessment_type,
            'inputs': self.get_inputs(),
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<HealthAssessment id={self.id} type='{self.assessment_type}'>"


class MLPredictionResult(db.Model):
    """Output of Scikit-Learn inference pipelines with Explainable AI attribution."""
    __tablename__ = 'ml_prediction_results'

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('health_assessments.id', ondelete='CASCADE'), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    condition_name = db.Column(db.String(50), nullable=False)  # 'diabetes' or 'cardiovascular'
    risk_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0 probability
    risk_category = db.Column(db.String(30), nullable=False)  # 'Low', 'Moderate', 'High'
    top_contributing_features = db.Column(db.Text, nullable=False)  # JSON: [{"feature": "Glucose", "importance": 0.28, "direction": "positive"}]
    model_version = db.Column(db.String(30), default='1.0.0', nullable=False)
    clinical_disclaimer = db.Column(db.Text, nullable=False)
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def get_contributing_features(self):
        try:
            return json.loads(self.top_contributing_features)
        except Exception:
            return []

    def set_contributing_features(self, feat_list):
        self.top_contributing_features = json.dumps(feat_list)

    def to_dict(self):
        return {
            'id': self.id,
            'assessment_id': self.assessment_id,
            'user_id': self.user_id,
            'condition_name': self.condition_name,
            'risk_score': round(self.risk_score, 3),
            'risk_percentage': round(self.risk_score * 100, 1),
            'risk_category': self.risk_category,
            'top_features': self.get_contributing_features(),
            'model_version': self.model_version,
            'clinical_disclaimer': self.clinical_disclaimer,
            'evaluated_at': self.evaluated_at.isoformat()
        }

    def __repr__(self):
        return f"<MLPredictionResult id={self.id} condition='{self.condition_name}' score={self.risk_score}>"


class ChatHistory(db.Model):
    """Conversation exchange between authenticated user and context-aware GenAI Assistant."""
    __tablename__ = 'chat_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    context_used = db.Column(db.Text, nullable=True)  # JSON or text citation summary
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender': self.sender,
            'message': self.message,
            'timestamp': self.timestamp.strftime('%H:%M • %b %d')
        }

    def __repr__(self):
        return f"<ChatHistory id={self.id} sender='{self.sender}'>"


class HealthArticle(db.Model):
    """Peer-reviewed educational preventive healthcare articles."""
    __tablename__ = 'health_articles'

    id = db.Column(db.Integer, primary_key=True)
    author_admin_id = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)
    
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # nutrition, diabetes, heart, sleep, hydration
    summary = db.Column(db.String(350), nullable=False)
    content_markdown = db.Column(db.Text, nullable=False)
    academic_citations = db.Column(db.Text, nullable=True)
    read_time_minutes = db.Column(db.Integer, default=5, nullable=False)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    bookmarks = db.relationship('ArticleBookmark', backref='article', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'slug': self.slug,
            'category': self.category,
            'summary': self.summary,
            'read_time_minutes': self.read_time_minutes,
            'citations': self.academic_citations,
            'published_at': self.published_at.strftime('%B %d, %Y')
        }

    def __repr__(self):
        return f"<HealthArticle id={self.id} slug='{self.slug}'>"


class ArticleBookmark(db.Model):
    """User bookmark of health articles for quick reference."""
    __tablename__ = 'article_bookmarks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('health_articles.id', ondelete='CASCADE'), nullable=False)
    bookmarked_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'article_id', name='uq_user_article_bookmark'),
    )

    def __repr__(self):
        return f"<ArticleBookmark user_id={self.user_id} article_id={self.article_id}>"
