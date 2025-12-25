import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # XAMPP MySQL default configuration (root user with no password)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root@localhost/nst_prep_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Engine options for Aiven SSL support
    # Aiven free tier uses self-signed certificates which often fail in serverless.
    # Setting ssl: {} or True with check_hostname: False handles this for PyMySQL.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {"ssl_mode": "DISABLED"} # This effectively tells the driver to ignore cert verification
        }
    } if os.environ.get('DATABASE_URL') and 'aivencloud.com' in os.environ.get('DATABASE_URL') else {}

    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
