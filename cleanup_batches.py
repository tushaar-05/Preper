from app import create_app
from app.extensions import db
from app.models import Batch, Enrollment
import json

def cleanup():
    app = create_app()
    with app.app_context():
        # 1. Ensure a "NEUMANN" batch exists or create it
        neumann = Batch.query.filter(Batch.name.ilike('%neumann%')).first()
        
        if not neumann:
            print("Creating NEUMANN batch...")
            neumann = Batch(
                name="Batch NEUMANN",
                description="Our flagship batch for comprehensive preparation.",
                original_price=899.0,
                discounted_price=499.0,
                status="active",
                max_students=100,
                color="violet"
            )
            neumann.features = [
                "10+ Full-length Mock Tests",
                "Personalized 1-on-1 Mentorship",
                "Advanced Interview Preparation",
                "Comprehensive Resource Library"
            ]
            db.session.add(neumann)
            db.session.flush() # Get ID
        else:
            print(f"Updating NEUMANN batch (ID: {neumann.id})...")
            neumann.name = "Batch NEUMANN" # Ensure exact name
            neumann.original_price = 899.0
            neumann.discounted_price = 499.0
            neumann.status = "active"
            neumann.color = "violet"
            # Keep features if they exist or set defaults
            if not neumann.features:
                neumann.features = [
                    "10+ Full-length Mock Tests",
                    "Personalized 1-on-1 Mentorship",
                    "Advanced Interview Preparation",
                    "Comprehensive Resource Library"
                ]

        # 2. Move all existing enrollments to this batch
        other_batches = Batch.query.filter(Batch.id != neumann.id).all()
        for other in other_batches:
            print(f"Moving students from batch '{other.name}' to NEUMANN...")
            # We need to handle potential uniqueness constraints if a student is in both
            # But the requirement is ONLY NEUMANN, so we just reassign.
            enrolls = Enrollment.query.filter_by(batch_id=other.id).all()
            for e in enrolls:
                # Check if the student is already in NEUMANN
                existing = Enrollment.query.filter_by(student_id=e.student_id, batch_id=neumann.id).first()
                if existing:
                    # Delete the duplicate enrollment for the old batch
                    db.session.delete(e)
                else:
                    e.batch_id = neumann.id
                    e.total_amount = neumann.discounted_price
            
            # 3. Delete the other batch
            db.session.delete(other)
            
        db.session.commit()
        print("Cleanup complete. Only Batch NEUMANN remains.")

if __name__ == "__main__":
    cleanup()
