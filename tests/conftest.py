# tests/conftest.py
import pytest
from tab_view import create_app, db
from tab_view.config import TestingConfig
from tab_view.models import User


@pytest.fixture(scope='module')
def app():
    """
    Creates an application instance for the entire test module.
    Pushes an application context so url_for and other Flask helpers work in tests.
    """
    app = create_app(TestingConfig)
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def client(app):
    """
    A client for testing HTTP endpoints.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='module')
def runner(app):
    """
    Runner for testing CLI commands
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def init_database(app):
    """
    Initializes the database
    """
    with app.app_context():
        db.create_all()
        
        yield db
        
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def new_user(init_database):
    """
    Creates a sample user
    """
    user = User(username='testuser', password='hashed_password_placeholder')
    db.session.add(user)
    db.session.commit()
    return user
