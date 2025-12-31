from app import create_app
from app.extensions import db
from app.models import Batch, Enrollment, Payment

def run_fixes():
    app = create_app()
    with app.app_context():
        print("🔍 Checking and updating prices...")
        
        # 1. Update Batches
        batches = Batch.query.filter_by(discounted_price=399.0).all()
        for batch in batches:
            batch.discounted_price = 599.0
            print(f"✅ Updated Batch: {batch.name}")
            
        # 2. Update Enrollments
        enrollments = Enrollment.query.filter_by(total_amount=399.0).all()
        for enrollment in enrollments:
            enrollment.total_amount = 599.0
            print(f"✅ Updated Enrollment ID: {enrollment.id}")
            
        # 3. Update Payments
        payments = Payment.query.filter_by(amount=399.0).all()
        for payment in payments:
            payment.amount = 599.0
            print(f"✅ Updated Payment ID: {payment.id}")
            
        if batches or enrollments or payments:
            db.session.commit()
            print("🎉 Database updated successfully!")
        else:
            print("ℹ️ No records with price 399 found.")

if __name__ == "__main__":
    run_fixes()
