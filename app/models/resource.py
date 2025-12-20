from app.extensions import db
from datetime import datetime


class Resource(db.Model):
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Resource Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Category & Type
    category = db.Column(db.String(50), nullable=False)  # notes, videos, pdfs, links, practice_papers
    resource_type = db.Column(db.String(20), default='file')  # file, url, video
    
    # File/URL Information
    file_path = db.Column(db.String(500))  # Path to uploaded file
    file_url = db.Column(db.String(500))  # External URL
    file_size = db.Column(db.Integer)  # Size in bytes
    file_type = db.Column(db.String(50))  # pdf, mp4, docx, etc.
    
    # Access Control
    access_level = db.Column(db.String(20), default='free')  # free, paid, batch_specific
    target_batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    
    # Subject/Topic
    subject = db.Column(db.String(100))  # Mathematics, English, Reasoning, etc.
    topic = db.Column(db.String(100))
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    download_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    target_batch = db.relationship('Batch', backref='resources', foreign_keys=[target_batch_id])
    
    def increment_download(self):
        """Increment download counter"""
        self.download_count += 1
        db.session.commit()
    
    def increment_view(self):
        """Increment view counter"""
        self.view_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<Resource {self.title} - {self.category}>'
