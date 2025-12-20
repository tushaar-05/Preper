from app.extensions import db
from datetime import datetime


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.id'))
    
    # Payment Details
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    
    # Payment Method
    payment_method = db.Column(db.String(50))  # card, upi, netbanking, wallet, cash
    
    # Transaction Information
    transaction_id = db.Column(db.String(100), unique=True)
    order_id = db.Column(db.String(100))
    
    # Payment Gateway
    gateway = db.Column(db.String(50))  # razorpay, paytm, stripe, etc.
    gateway_response = db.Column(db.Text)  # JSON response from gateway
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed, refunded
    
    # Additional Information
    description = db.Column(db.String(500))
    receipt_url = db.Column(db.String(500))
    
    # Refund Information
    refund_amount = db.Column(db.Float, default=0.0)
    refund_reason = db.Column(db.Text)
    refunded_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'completed'
    
    @property
    def is_refunded(self):
        """Check if payment was refunded"""
        return self.status == 'refunded'
    
    def __repr__(self):
        return f'<Payment {self.transaction_id} - {self.status}>'
