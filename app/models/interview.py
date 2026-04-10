from app.extensions import db
from datetime import datetime


class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=True)
    target_audience = db.Column(db.String(50), nullable=True)  # all_registered, all_enrolled, individual, etc.
    
    # Interview Details
    interview_type = db.Column(db.String(20), nullable=False)  # personal, group, mock
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Schedule
    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    
    # Interviewer
    interviewer_name = db.Column(db.String(100))
    interviewer_email = db.Column(db.String(120))
    
    # Status
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled, rescheduled
    
    # Feedback
    feedback = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 rating
    
    # Meeting Details
    meeting_link = db.Column(db.String(500))
    meeting_platform = db.Column(db.String(50))  # zoom, meet, teams, etc.
    image_url = db.Column(db.String(500)) # Poster image URL
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.Index('idx_interview_student_status', 'student_id', 'status'),
        db.Index('idx_interview_audience', 'target_audience', 'status'),
    )

    def __repr__(self):
        return f'<Interview {self.title} - {self.status}>'
