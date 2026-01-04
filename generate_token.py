
from app import create_app
from itsdangerous import URLSafeTimedSerializer
from flask import url_for

app = create_app()

email = "tusharsingh222555@gmail.com" # Probable user email

with app.app_context():
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = s.dumps(email, salt='password-reset-salt')
    # We can't generate the full URL easily without request context for absolute URL, 
    # but we can construct it if we assume localhost:5000 or 5005
    print(f"Token: {token}")
    print(f"Manual Link: http://127.0.0.1:5000/reset-password/{token}")
