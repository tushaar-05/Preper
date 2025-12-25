"""
Database Viewer Script
Prints the contents of all tables in the database
"""

from app import create_app
from app.extensions import db
from app.models import User, Student, Batch, Enrollment, Interview, MockTest, Question, Announcement, Resource, Payment

def view_data():
    app = create_app()
    with app.app_context():
        print("="*50)
        print("          DATABASE CONTENTS REPORT")
        print("="*50)

        # 1. USERS
        users = User.query.all()
        print(f"\n[ USERS ({len(users)}) ]")
        for u in users:
            print(f"  ID: {u.id} | User: {u.username} | Email: {u.email} | Role: {u.role}")

        # 2. STUDENTS
        students = Student.query.all()
        print(f"\n[ STUDENTS ({len(students)}) ]")
        for s in students:
            print(f"  ID: {s.id} | Name: {s.full_name} | UserID: {s.user_id}")

        # 3. BATCHES
        batches = Batch.query.all()
        print(f"\n[ BATCHES ({len(batches)}) ]")
        for b in batches:
            print(f"  ID: {b.id} | Name: {b.name} | Status: {b.status} | Price: {b.discounted_price}")

        # 4. ENROLLMENTS
        enrollments = Enrollment.query.all()
        print(f"\n[ ENROLLMENTS ({len(enrollments)}) ]")
        for e in enrollments:
            print(f"  ID: {e.id} | StudentID: {e.student_id} | BatchID: {e.batch_id} | Status: {e.payment_status}")

        # 5. PAYMENTS
        payments = Payment.query.all()
        print(f"\n[ PAYMENTS ({len(payments)}) ]")
        for p in payments:
            print(f"  ID: {p.id} | Amount: {p.amount} | Status: {p.status} | date: {p.created_at}")

        # 6. MOCK TESTS
        mocks = MockTest.query.all()
        print(f"\n[ MOCK TESTS ({len(mocks)}) ]")
        for m in mocks:
            print(f"  ID: {m.id} | Title: {m.title} | Active: {m.is_active}")

        print("\n" + "="*50)

if __name__ == '__main__':
    view_data()
