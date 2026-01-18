from dotenv import load_dotenv
from tab_view.utils import str_to_bool
import os


load_dotenv()


class Config:
    """Base Configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = str_to_bool(os.getenv('DATABASE_TRACK_MODIFICATIONS', 'False'))


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = True
    RATELIMIT_ENABLED = False
    SCHEDULER_API_ENABLED = False
