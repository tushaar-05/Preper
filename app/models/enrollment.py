from app.extensions import db
from datetime import datetime


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    
    # Enrollment Details
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Payment Status
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, completed, refunded
    amount_paid = db.Column(db.Float, default=0.0)
    total_amount = db.Column(db.Float, nullable=False)
    
    # Progress
    completion_percentage = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    completed_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('Payment', backref='enrollment', lazy='dynamic', cascade='all, delete-orphan')
    
    # Unique constraint: one student can enroll in a batch only once
    __table_args__ = (
        db.UniqueConstraint('student_id', 'batch_id', name='unique_student_batch'),
        db.Index('idx_enrollment_student_status', 'student_id', 'payment_status'),
    )
    
    @property
    def remaining_amount(self):
        """Calculate remaining payment amount"""
        return self.total_amount - self.amount_paid
    
    def __repr__(self):
        return f'<Enrollment Student:{self.student_id} Batch:{self.batch_id}>'
