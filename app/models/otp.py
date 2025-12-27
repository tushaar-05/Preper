from app.extensions import db
from datetime import datetime, timedelta
import random
import string

class OTP(db.Model):
    __tablename__ = 'otps'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # 'login' or 'register'
    
    def __init__(self, email, purpose, expiry_minutes=10):
        self.email = email
        self.purpose = purpose
        self.otp_code = self.generate_otp()
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(minutes=expiry_minutes)
        self.is_used = False
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=6))
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
    
    @staticmethod
    def cleanup_expired():
        """Delete expired OTPs (can be called periodically)"""
        expired_otps = OTP.query.filter(OTP.expires_at < datetime.utcnow()).all()
        for otp in expired_otps:
            db.session.delete(otp)
        db.session.commit()
        return len(expired_otps)
    
    def __repr__(self):
        return f'<OTP {self.email} - {self.purpose}>'
