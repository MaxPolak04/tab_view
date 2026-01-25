from flask import current_app
from tab_view.config import TestingConfig


def test_app_exists(app):
    """Checks whether the application instance has been created."""
    assert app is not None

def test_app_is_testing(app):
    """Checks whether the application is running in TESTING mode."""
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    assert app.config['WTF_CSRF_ENABLED'] is False
    