from flask import Flask
from app.extensions import db
from app.models.mock_test import MockTest, Question
from datetime import datetime, timedelta
from app.routes.admin import _update_mock_total_marks
import os

def run_verification():
    # Setup minimal app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root@localhost/nst_prep_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("Starting Verification...")
        
        # 1. Create a test Mock
        start_time = datetime.now()
        mock = MockTest(
            title="Verification Test", 
            duration_minutes=120,
            total_marks=0, 
            passing_marks=40,
            available_from=start_time,
            available_until=start_time + timedelta(minutes=120),
            category="NSAT",
            sections=["General Aptitude", "English", "Mathematics"]
        )
        # Note: In a unit test we'd trust the route logic, but here we are using models directly. 
        # The logic was moved to the ROUTE (admin.py), not the MODEL. 
        # So testing Model directly won't trigger the auto-calc unless we put it in before_save or similar.
        # However, for this script checking strict model behavior, we just want to ensure DB accepts it.
        
        db.session.add(mock)
        db.session.commit()
        mock_id = mock.id
        print(f"Created Mock ID: {mock_id}, Total Marks: {mock.total_marks}, Duration: {mock.duration_minutes} min")
        assert mock.duration_minutes == 120, f"Expected 120 mins duration, got {mock.duration_minutes}"
        
        try:
            # 2. Add Question 1 (4 marks)
            q1 = Question(
                mock_test_id=mock_id,
                question_text="Q1",
                correct_answer="1",
                marks=4,
                question_number=1
            )
            db.session.add(q1)
            db.session.commit()
            _update_mock_total_marks(mock_id)
            
            mock = MockTest.query.get(mock_id)
            print(f"After adding Q1 (4 marks): Mock Total Marks = {mock.total_marks}")
            assert mock.total_marks == 4, f"Expected 4, got {mock.total_marks}"
            
            # 3. Add Question 2 (2 marks)
            q2 = Question(
                mock_test_id=mock_id,
                question_text="Q2",
                correct_answer="1",
                marks=2,
                question_number=2
            )
            db.session.add(q2)
            db.session.commit()
            _update_mock_total_marks(mock_id)
            
            mock = MockTest.query.get(mock_id)
            print(f"After adding Q2 (2 marks): Mock Total Marks = {mock.total_marks}")
            assert mock.total_marks == 6, f"Expected 6, got {mock.total_marks}"
            
            # 4. Edit Q1 to 5 marks
            q1.marks = 5
            db.session.commit()
            _update_mock_total_marks(mock_id)
            
            mock = MockTest.query.get(mock_id)
            print(f"After editing Q1 to 5 marks: Mock Total Marks = {mock.total_marks}")
            assert mock.total_marks == 7, f"Expected 7, got {mock.total_marks}"
            
            # 5. Delete Q2
            db.session.delete(q2)
            db.session.commit()
            _update_mock_total_marks(mock_id)
            
            mock = MockTest.query.get(mock_id)
            print(f"After deleting Q2: Mock Total Marks = {mock.total_marks}")
            assert mock.total_marks == 5, f"Expected 5, got {mock.total_marks}"
            
            print("\nSUCCESS: All verifications passed!")
            
        except Exception as e:
            print(f"\nFAILURE: {str(e)}")
        finally:
            # Cleanup with cascade
            mock_to_delete = MockTest.query.get(mock_id)
            if mock_to_delete:
                db.session.delete(mock_to_delete)
            db.session.commit()
            print("Cleanup done.")

if __name__ == '__main__':
    run_verification()
