from app.extensions import db
from datetime import datetime


class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Content
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Priority & Targeting
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    target_audience = db.Column(db.String(50), default='all')  # all, students, specific_batch
    target_batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    
    # Display Settings
    is_pinned = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    
    # Schedule
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    target_batch = db.relationship('Batch', backref='announcements', foreign_keys=[target_batch_id])
    
    @property
    def is_active(self):
        """Check if announcement is currently active"""
        now = datetime.utcnow()
        if not self.is_published:
            return False
        if self.expires_at and now > self.expires_at:
            return False
        return True
    
    def __repr__(self):
        return f'<Announcement {self.title} - {self.priority}>'


class AnnouncementRead(db.Model):
    __tablename__ = 'announcement_reads'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='announcement_reads')
    announcement = db.relationship('Announcement', backref=db.backref('read_records', cascade='all, delete-orphan'))
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'announcement_id', name='unique_student_announcement_read'),
    )

    def __repr__(self):
        return f'<AnnouncementRead student={self.student_id} announcement={self.announcement_id}>'
