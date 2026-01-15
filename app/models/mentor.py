from app.extensions import db
from datetime import datetime

class Mentor(db.Model):
    __tablename__ = 'mentors'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), default='Guide')
    email = db.Column(db.String(120), unique=True)
    rating = db.Column(db.Float, default=5.0)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Mentor {self.full_name}>'
