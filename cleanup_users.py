from app import create_app
from app.extensions import db
from app.models import User, Student, Enrollment, Payment, Interview, TestAttempt

def cleanup_database():
    app = create_app()
    with app.app_context():
        print("🧼 Starting database cleanup...")
        
        # 1. Identify all student users
        student_users = User.query.filter_by(role='student').all()
        student_user_ids = [u.id for u in student_users]
        
        if not student_user_ids:
            print("✨ No student users found. Database is already clean or only contains admins.")
            return

        print(f"📦 Found {len(student_user_ids)} student users to remove.")

        # 2. Delete dependent data first to respect foreign keys (if not using cascade)
        # Note: Models like Enrollment, Interview, etc. belong to Students. 
        # Students belong to Users.
        
        students = Student.query.filter(Student.user_id.in_(student_user_ids)).all()
        student_ids = [s.id for s in students]

        print(f"🗑️  Removing data for {len(student_ids)} student profiles...")

        if student_ids:
            # Delete transactions/attempts first
            Payment.query.filter(Payment.student_id.in_(student_ids)).delete(synchronize_session=False)
            TestAttempt.query.filter(TestAttempt.student_id.in_(student_ids)).delete(synchronize_session=False)
            Interview.query.filter(Interview.student_id.in_(student_ids)).delete(synchronize_session=False)
            Enrollment.query.filter(Enrollment.student_id.in_(student_ids)).delete(synchronize_session=False)
            
            # Delete profiles
            Student.query.filter(Student.id.in_(student_ids)).delete(synchronize_session=False)
        
        # 3. Delete student users
        User.query.filter(User.id.in_(student_user_ids)).delete(synchronize_session=False)
        
        db.session.commit()
        print("✅ Cleanup complete! All student-related data has been removed.")
        print("🛡️  Admin accounts and Course Batches were preserved.")

if __name__ == "__main__":
    cleanup_database()
