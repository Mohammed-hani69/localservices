import os

class Config:
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev_key_for_development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///local_services.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
