import os

class Config:
    """
    Flask application configuration
    """
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key')