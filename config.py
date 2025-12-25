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
    # Aiven requires SSL. This block finds the system certificate bundle on Vercel/Linux.
    _ssl_ca_paths = [
        "/etc/pki/tls/certs/ca-bundle.crt", # Amazon Linux / RHEL
        "/etc/ssl/certs/ca-certificates.crt", # Debian / Ubuntu
        "/etc/ssl/cert.pem", # Generic / macOS
    ]
    _ca_path = next((p for p in _ssl_ca_paths if os.path.exists(p)), None)
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {
                "ca": _ca_path,
                "check_hostname": False # Required for Aiven free tier certificates
            } if _ca_path else {"check_hostname": False}
        }
    } if os.environ.get('DATABASE_URL') and 'aivencloud.com' in os.environ.get('DATABASE_URL') else {}

    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
