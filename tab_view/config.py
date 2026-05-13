import os

from dotenv import load_dotenv

load_dotenv(override=False)


class Config:
    """
    Base configuration class.

    Common settings shared across all environments:
    - SECRET_KEY: Flask secret key for sessions and CSRF
    - SQLALCHEMY_DATABASE_URI: Database connection string
    - MAX_CONTENT_LENGTH: Maximum upload size (500 MB) to prevent server overload
    """

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024
    WEATHER_LATITUDE = 52.4069
    WEATHER_LONGITUDE = 16.9299
    WEATHER_CACHE_MINUTES = 20

    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set")

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URL is not set")


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
    SERVER_NAME = "localhost.localdomain"
    SECRET_KEY = "test-secret"  # nosec
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    RATELIMIT_ENABLED = False
    SCHEDULER_API_ENABLED = False
