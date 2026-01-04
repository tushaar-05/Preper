
from app import create_app
from app.models import User
import sys

app = create_app()

with app.app_context():
    print(f"--- Email Configuration ---")
    print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    print(f"RESEND_API_KEY: {'[SET]' if app.config.get('RESEND_API_KEY') else '[NOT SET]'}")
    
    print(f"\n--- User Check ---")
    # Prompt for email or just list all for debugging (masked)
    users = User.query.all()
    print(f"Found {len(users)} users.")
    for u in users:
        print(f"User: {u.email} (Role: {u.role})")
