import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # Defaulting to a local mysql database, user should update this URI.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:password@localhost/flask_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
