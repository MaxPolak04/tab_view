# tests/conftest.py
import pytest
from werkzeug.security import generate_password_hash
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


@pytest.fixture(scope='function')
def auth_client(client, init_database):
    """
    Returns a test client that is already logged in as a regular user.
    """
    # 1. Create a user
    password = 'test_password'
    hashed = generate_password_hash(password)
    user = User(username='api_tester', password=hashed, is_admin=False)
    init_database.session.add(user)
    init_database.session.commit()

    # 2. Login
    # We use the existing auth route to establish a session
    client.post('/auth/signin', data={
        'username': 'api_tester',
        'password': password
    }, follow_redirects=True)

    return client
