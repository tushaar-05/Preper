import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # XAMPP MySQL default configuration (root user with no password)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///app.db'
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
    
    # Flask-Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
    # If SSL is True, default TLS to False unless explicitly set to True
    if MAIL_USE_SSL:
        MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False').lower() in ['true', '1', 't']
    else:
        MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')
    
    # Resend Configuration
    RESEND_API_KEY = os.environ.get('RESEND_API_KEY')

    # MojoAuth Configuration
    MOJOAUTH_API_KEY = os.environ.get('MOJOAUTH_API_KEY')

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

    # Caching Configuration
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'RedisCache' if os.environ.get('REDIS_URL') else 'SimpleCache')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    
    # Static File Configuration
    # Set to 1 year (31536000 seconds) for production performance
    SEND_FILE_MAX_AGE_DEFAULT = int(os.environ.get('SEND_FILE_MAX_AGE_DEFAULT', 31536000))
