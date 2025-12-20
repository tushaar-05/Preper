from app import create_app
from app.extensions import db
# Ensure all models are imported so db.create_all() knows about them
from app.models import * 

def update_database():
    app = create_app()
    with app.app_context():
        print("🔍 Checking for missing tables...")
        # db.create_all() creates tables that don't exist yet
        # It does NOT drop or modify existing tables
        db.create_all()
        print("✅ Database tables synchronized successfully!")

if __name__ == "__main__":
    update_database()
