"""
Database Initialization Script
Creates all tables and seeds initial data for NST Prep application
"""

from app import create_app
from app.extensions import db
from app.models import (
    User, Student, Batch, Enrollment, Interview,
    MockTest, Question, TestAttempt, Announcement, Resource, Payment
)
from datetime import datetime, timedelta
import json

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
        admin = User(
            username='admin',
            email='admin@nstprep.com',
            role='admin',
            is_active=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create Sample Student Users
        student_user1 = User(
            username='rahul_sharma',
            email='rahul@example.com',
            role='student',
            is_active=True,
            is_active=True
        )
        student_user1.set_password('password123')
        db.session.add(student_user1)
        
        student_user2 = User(
            username='priya_singh',
            email='priya@example.com',
            role='student',
            is_active=True,
            is_active=True
        )
        student_user2.set_password('password123')
        db.session.add(student_user2)
        
        db.session.commit()
        
        # Create Student Profiles
        student1 = Student(
            user_id=student_user1.id,
            full_name='Rahul Sharma',
            phone='9876543210',
            city='Mumbai',
            state='Maharashtra',
            education_level='Graduate',
            enrollment_status='active'
        )
        db.session.add(student1)
        
        student2 = Student(
            user_id=student_user2.id,
            full_name='Priya Singh',
            phone='9876543211',
            city='Delhi',
            state='Delhi',
            education_level='12th',
            enrollment_status='active'
        )
        db.session.add(student2)
        
        db.session.commit()
        
        # Create Sample Batches
        batch1 = Batch(
            name='NST Foundation Batch - January 2025',
            description='Complete preparation course for Navy Service Test with comprehensive study material and mock tests.',
            original_price=15000,
            discounted_price=9999,
            gst_included=True,
            max_students=50,
            current_enrollment=12,
            start_date=datetime(2025, 1, 15).date(),
            end_date=datetime(2025, 6, 15).date(),
            status='active',
            color='violet'
        )
        batch1.features = [
            '100+ Hours of Live Classes',
            '50+ Mock Tests',
            'Personal Interview Preparation',
            'Study Material & Notes',
            'Doubt Clearing Sessions'
        ]
        db.session.add(batch1)
        
        batch2 = Batch(
            name='NST Advanced Batch - February 2025',
            description='Advanced level preparation for serious NST aspirants with intensive training.',
            original_price=20000,
            discounted_price=14999,
            gst_included=True,
            max_students=30,
            current_enrollment=8,
            start_date=datetime(2025, 2, 1).date(),
            end_date=datetime(2025, 7, 1).date(),
            status='upcoming',
            color='blue'
        )
        batch2.features = [
            '150+ Hours of Live Classes',
            '75+ Mock Tests',
            'One-on-One Mentorship',
            'Complete Study Package',
            'Interview & SSB Preparation'
        ]
        db.session.add(batch2)
        
        batch3 = Batch(
            name='NST Crash Course - March 2025',
            description='Intensive crash course for quick revision and exam preparation.',
            original_price=8000,
            discounted_price=5999,
            gst_included=True,
            max_students=100,
            current_enrollment=45,
            start_date=datetime(2025, 3, 1).date(),
            end_date=datetime(2025, 4, 30).date(),
            status='upcoming',
            color='green'
        )
        batch3.features = [
            '60+ Hours of Live Classes',
            '30+ Mock Tests',
            'Quick Revision Notes',
            'Previous Year Papers'
        ]
        db.session.add(batch3)
        
        db.session.commit()
        
        # Create Sample Enrollments
        enrollment1 = Enrollment(
            student_id=student1.id,
            batch_id=batch1.id,
            payment_status='completed',
            amount_paid=9999,
            total_amount=9999,
            completion_percentage=25.5
        )
        db.session.add(enrollment1)
        
        enrollment2 = Enrollment(
            student_id=student2.id,
            batch_id=batch1.id,
            payment_status='partial',
            amount_paid=5000,
            total_amount=9999,
            completion_percentage=10.0
        )
        db.session.add(enrollment2)
        
        db.session.commit()
        
        # Create Sample Mock Test
        mock_test1 = MockTest(
            title='NST Practice Test - Mathematics',
            description='Comprehensive mathematics test covering all topics',
            duration_minutes=90,
            total_marks=100,
            passing_marks=40,
            difficulty_level='medium',
            category='Mathematics',
            is_active=True,
            is_free=False
        )
        db.session.add(mock_test1)
        
        db.session.commit()
        
        # Create Sample Questions
        question1 = Question(
            mock_test_id=mock_test1.id,
            question_text='What is the value of √144?',
            question_type='mcq',
            correct_answer='12',
            marks=2,
            negative_marks=0.5,
            question_number=1
        )
        question1.options = ['10', '11', '12', '13']
        db.session.add(question1)
        
        question2 = Question(
            mock_test_id=mock_test1.id,
            question_text='If x + 5 = 12, what is the value of x?',
            question_type='mcq',
            correct_answer='7',
            marks=2,
            negative_marks=0.5,
            question_number=2
        )
        question2.options = ['5', '6', '7', '8']
        db.session.add(question2)
        
        db.session.commit()
        
        # Create Sample Interview
        interview1 = Interview(
            student_id=student1.id,
            interview_type='personal',
            title='Personal Interview - Round 1',
            description='Initial screening interview for NST preparation',
            scheduled_date=datetime.now() + timedelta(days=7),
            duration_minutes=30,
            interviewer_name='Cdr. Rajesh Kumar',
            status='scheduled',
            meeting_platform='zoom'
        )
        db.session.add(interview1)
        
        db.session.commit()
        
        # Create Sample Announcements
        announcement1 = Announcement(
            created_by=admin.id,
            title='Welcome to NST Prep Platform!',
            content='We are excited to have you on board. Start your preparation journey with us today!',
            priority='high',
            target_audience='all',
            is_pinned=True
        )
        db.session.add(announcement1)
        
        announcement2 = Announcement(
            created_by=admin.id,
            title='New Mock Test Available',
            content='A new mathematics mock test has been added. Attempt it now to test your skills!',
            priority='medium',
            target_audience='students'
        )
        db.session.add(announcement2)
        
        db.session.commit()
        
        # Create Sample Resources
        resource1 = Resource(
            uploaded_by=admin.id,
            title='NST Mathematics Complete Notes',
            description='Comprehensive notes covering all mathematics topics for NST',
            category='notes',
            resource_type='file',
            file_path='/uploads/resources/math_notes.pdf',
            file_type='pdf',
            access_level='free',
            subject='Mathematics',
            is_active=True
        )
        db.session.add(resource1)
        
        resource2 = Resource(
            uploaded_by=admin.id,
            title='English Grammar Video Lectures',
            description='Complete video series on English grammar for NST preparation',
            category='videos',
            resource_type='url',
            file_url='https://example.com/english-lectures',
            access_level='paid',
            subject='English',
            is_active=True
        )
        db.session.add(resource2)
        
        db.session.commit()
        
        # Create Sample Payment
        payment1 = Payment(
            student_id=student1.id,
            enrollment_id=enrollment1.id,
            amount=9999,
            currency='INR',
            payment_method='upi',
            transaction_id='TXN' + datetime.now().strftime('%Y%m%d%H%M%S'),
            gateway='razorpay',
            status='completed',
            description='Payment for NST Foundation Batch - January 2025',
            completed_at=datetime.now()
        )
        db.session.add(payment1)
        
        db.session.commit()
        
        print("\n✅ Sample data seeded successfully!")
        print("\n👤 Admin Credentials:")
        print("   Username: admin")
        print("   Email: admin@nstprep.com")
        print("   Password: admin123")
        print("\n👨‍🎓 Sample Student Credentials:")
        print("   Username: rahul_sharma")
        print("   Email: rahul@example.com")
        print("   Password: password123")
        print("\n📊 Sample Data Summary:")
        print(f"   - {User.query.count()} users created")
        print(f"   - {Student.query.count()} students created")
        print(f"   - {Batch.query.count()} batches created")
        print(f"   - {Enrollment.query.count()} enrollments created")
        print(f"   - {MockTest.query.count()} mock tests created")
        print(f"   - {Question.query.count()} questions created")
        print(f"   - {Interview.query.count()} interviews scheduled")
        print(f"   - {Announcement.query.count()} announcements created")
        print(f"   - {Resource.query.count()} resources added")
        print(f"   - {Payment.query.count()} payments recorded")
        
        print("\n🎉 Database initialization complete!")
        print("\n⚠️  Note: Make sure your XAMPP MySQL server is running")
        print("   and the database 'nst_prep_db' exists.")

if __name__ == '__main__':
    init_database()
