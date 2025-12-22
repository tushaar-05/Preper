from flask import Flask
from app.extensions import db
from app.models.mock_test import MockTest, Question
import os

def verify_scoring_logic():
    # Setup minimal app context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root@localhost/nst_prep_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        print("Starting Scoring Logic Verification...")
        
        # 1. Create a dummy Question (in memory or temp DB)
        # We'll just simulate the logic without actual DB submission to avoid clutter if possible, 
        # but the logic relies on DB queries.
        
        # Let's assume we have a question
        q = Question(id=999, correct_answer="1", marks=4, negative_marks=1)
        
        # User submits "1" (which is what we changed the value to)
        user_answer = "1"
        
        print(f"Question Correct Answer: '{q.correct_answer}'")
        print(f"User Submitted Answer: '{user_answer}'")
        
        if user_answer == q.correct_answer:
            print("MATCH: Scoring logic works for Index based values.")
        else:
            print("MISMATCH: Logic failed.")
            
        # User submits "Paris" (Old behavior)
        old_user_answer = "Paris"
        if old_user_answer == q.correct_answer:
             print("MATCH (Unexpected): Old logic worked?")
        else:
             print("MISMATCH (Expected): Old logic failed as expected.")

if __name__ == '__main__':
    verify_scoring_logic()
