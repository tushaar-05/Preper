from app.extensions import db
from datetime import datetime


class Doubt(db.Model):
    __tablename__ = 'doubts'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # Doubt Details
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default='General Query')  # General Query, Mock Interview, Logical Reasoning, Technical
    
    # Status & Metadata
    status = db.Column(db.String(20), default='pending')  # pending, answered, closed
    views = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='doubts', foreign_keys=[student_id])
    replies = db.relationship('DoubtReply', backref='doubt', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Doubt {self.title}>'


class DoubtReply(db.Model):
    __tablename__ = 'doubt_replies'
    
    id = db.Column(db.Integer, primary_key=True)
    doubt_id = db.Column(db.Integer, db.ForeignKey('doubts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Reply Details
    content = db.Column(db.Text, nullable=False)
    is_staff_reply = db.Column(db.Boolean, default=False)  # True if replied by admin/mentor
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='doubt_replies')
    
    def __repr__(self):
        return f'<DoubtReply for Doubt {self.doubt_id}>'
