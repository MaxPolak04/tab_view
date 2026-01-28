import pytest
from werkzeug.security import generate_password_hash
from tab_view import create_app, db
from tab_view.config import TestingConfig
from tab_view.models import User


@pytest.fixture(scope='module')
def app(tmp_path_factory):
    """
    Creates an application instance using a temporary directory for static files.
    """
    temp_static_dir = tmp_path_factory.mktemp("static")
    temp_uploads_dir = temp_static_dir / "uploads"
    temp_uploads_dir.mkdir()

    app = create_app(TestingConfig)
    app.static_folder = str(temp_static_dir)
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
    Creates a sample user with a known password.
    Returns the user object.
    """
    password = 'test_password'
    hashed = generate_password_hash(password)
    
    user = User(username='testuser', password=hashed, is_admin=False)
    
    init_database.session.add(user)
    init_database.session.commit()
    
    user.raw_password = password
    
    return user


@pytest.fixture(scope='function')
def auth_client(client, new_user):
    """
    Returns a test client logged in as 'new_user'.
    Notice how we request 'new_user' as an argument!
    """
    client.post('/auth/signin', data={
        'username': new_user.username,
        'password': new_user.raw_password
    }, follow_redirects=True)

    return client


@pytest.fixture(scope='function')
def admin_client(client, init_database):
    """
    Returns a test client logged in as an Administrator.
    """
    password = 'admin_password'
    hashed = generate_password_hash(password)
    
    admin = User(username='admin', password=hashed, is_admin=True)
    
    init_database.session.add(admin)
    init_database.session.commit()

    client.post('/auth/signin', data={
        'username': 'admin',
        'password': password
    }, follow_redirects=True)

    return client
