from app.extensions import db
from datetime import datetime
import json


class Batch(db.Model):
    __tablename__ = 'batches'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Pricing
    original_price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float, nullable=False)
    gst_included = db.Column(db.Boolean, default=True)
    
    # Capacity
    max_students = db.Column(db.Integer, nullable=False, default=50)
    current_enrollment = db.Column(db.Integer, default=0)
    
    # Schedule
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    
    # Status
    status = db.Column(db.String(20), default='upcoming')  # upcoming, active, completed, cancelled
    
    # Features (stored as JSON)
    features_json = db.Column(db.Text)  # JSON array of features
    
    # Metadata
    color = db.Column(db.String(20), default='violet')  # For UI display
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='batch', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def features(self):
        """Get features as a Python list"""
        if self.features_json:
            return json.loads(self.features_json)
        return []
    
    @features.setter
    def features(self, features_list):
        """Set features from a Python list"""
        self.features_json = json.dumps(features_list)
    
    @property
    def enrollment_percentage(self):
        """Calculate enrollment percentage"""
        if self.max_students == 0:
            return 0
        return (self.current_enrollment / self.max_students) * 100
    
    @property
    def is_full(self):
        """Check if batch is full"""
        return self.current_enrollment >= self.max_students
    
    def __repr__(self):
        return f'<Batch {self.name} ({self.status})>'
