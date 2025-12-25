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
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {"check_hostname": False} if os.environ.get('DATABASE_URL') and 'aivencloud.com' in os.environ.get('DATABASE_URL') else None
        }
    }
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# Debug print to verify if config is loaded
print("Config loaded: SQLAlchemy URI set to {}".format(Config.SQLALCHEMY_DATABASE_URI))
