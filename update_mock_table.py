import os
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        # Check if column exists
        result = db.session.execute(text("SHOW COLUMNS FROM mock_tests LIKE 'is_anytime'"))
        exists = result.fetchone()
        
        if not exists:
            db.session.execute(text("ALTER TABLE mock_tests ADD COLUMN is_anytime BOOLEAN DEFAULT FALSE"))
            db.session.commit()
            print("Successfully added is_anytime column to mock_tests table.")
        else:
            print("is_anytime column already exists.")
            
    except Exception as e:
        print(f"Error updating database: {e}")
        db.session.rollback()
