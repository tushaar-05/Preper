from app import create_app
from app.extensions import db
from app.models import AnnouncementRead

def update_database():
    app = create_app()
    with app.app_context():
        print("Checking for missing database tables...")
        # create_all() will only create tables that don't exist
        db.create_all()
        print("Database schema update complete!")

if __name__ == '__main__':
    update_database()
