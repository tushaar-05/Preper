"""
Database Initialization Script
Creates all tables and seeds initial data for NST Prep application
"""

from app import create_app
from app.extensions import db
from app.models import User, Student, Batch, Enrollment, Interview, MockTest, Question, TestAttempt, Announcement, Resource, Payment
from datetime import datetime, timedelta

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Dropping all existing tables...")
        db.drop_all()
        
        print("🏗️  Creating all tables...")
        db.create_all()
        
        print("✅ All tables created successfully!")
        print("\n📊 Tables created:")
        print("   - users")
        print("   - students")
        print("   - batches")
        print("   - enrollments")
        print("   - interviews")
        print("   - mock_tests")
        print("   - questions")
        print("   - test_attempts")
        print("   - announcements")
        print("   - resources")
        print("   - payments")
        
        print("\n🌱 Seeding initial data...")
        
        # Create Admin User
        print("   Creating Admin User...")
        admin = User(
            username='admin',
            email='admin@nstprep.com',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        db.session.commit()
        
        print("\n✅ Database initialized successfully!")
        print("\n👤 Admin Credentials:")
        print("   Username: admin")
        print("   Email: admin@nstprep.com")
        print("   Password: admin123")
        
        print("\n⚠️  All other data (Batches, Students, etc.) has been cleared.")

if __name__ == '__main__':
    init_database()
