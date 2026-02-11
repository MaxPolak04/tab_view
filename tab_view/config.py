from dotenv import load_dotenv
import os


load_dotenv(override=False)


class Config:
    """
    Base configuration class.

    Common settings shared across all environments:
    - SECRET_KEY: Flask secret key for sessions and CSRF
    - SQLALCHEMY_DATABASE_URI: Database connection string
    """

    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.getenv('RATELIMIT_STORAGE_URI', 'memory://')

    if not SECRET_KEY:
        raise RuntimeError('SECRET_KEY is not set')

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError('DATABASE_URL is not set')
    

class ProductionConfig(Config):
    """
    Production configuration.

    - Debugging disabled
    - Relies on environment variables
    - Intended to be run via Gunicorn
    """
    
    DEBUG = False
    TESTING = False


class TestingConfig:
    """
    Configuration used for automated tests.

    Uses in-memory SQLite database and disables:
    - CSRF protection
    - Authentication
    - Rate limiting
    - Scheduler
    """

    TESTING = True
    SERVER_NAME = 'localhost.localdomain'
    SECRET_KEY = 'test-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    RATELIMIT_ENABLED = False
    SCHEDULER_API_ENABLED = False
