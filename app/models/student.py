from app.extensions import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    
    # Academic Information
    education_level = db.Column(db.String(50))
    institution_name = db.Column(db.String(200))
    
    # NST Specific
    target_exam_date = db.Column(db.Date)
    preferred_batch = db.Column(db.String(100))
    
    # Status
    enrollment_status = db.Column(db.String(20), default='pending')  # pending, active, completed, dropped
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    interviews = db.relationship('Interview', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    test_attempts = db.relationship('TestAttempt', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.full_name}>'
