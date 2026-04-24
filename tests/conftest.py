from unittest.mock import patch

import pytest
from werkzeug.security import generate_password_hash

from tab_view import create_app, db
from tab_view.config import TestingConfig
from tab_view.models import User


@pytest.fixture(scope="session", autouse=True)
def prevent_scheduler_crash():
    """
    Global patch for APScheduler to prevent threading crashes during the test session.

    APScheduler operates as a background singleton. Calling `create_app` multiple
    times across a test suite attempts to spawn duplicate background threads,
    resulting in a fatal `SchedulerAlreadyRunningError`. This mock ensures
    `init_app` and `start` are silently bypassed.
    """
    with (
        patch("flask_apscheduler.APScheduler.init_app"),
        patch("flask_apscheduler.APScheduler.start"),
    ):
        yield


@pytest.fixture(scope="function")
def app(tmp_path):
    """
    Yields a fresh, isolated Flask application context for each test.

    Overrides `app.static_folder` using Pytest's `tmp_path` to guarantee a sterile
    `/uploads` directory per test. This strictly prevents file state leakage
    (Test Pollution) where artifacts from Test A affect Test B.
    """
    temp_uploads_dir = tmp_path / "uploads"
    temp_uploads_dir.mkdir()

    app = create_app(TestingConfig)
    app.static_folder = str(tmp_path)

    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def client(app):
    """
    Provides a Flask test client for HTTP endpoint simulation.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope="function")
def runner(app):
    """
    Provides a Flask CLI test runner for custom commands.
    """
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def init_database(app):
    """
    Initializes a sterile database schema before each test
    and safely destroys it afterward.

    CRITICAL: `db.session.rollback()` must execute before
    `db.drop_all()`. If a test fails mid-execution, an open,
    uncommitted transaction will lock
    the SQLite database, causing cascade `IntegrityError`
    failures in all subsequent tests.
    """
    with app.app_context():
        db.create_all()

        yield db

        db.session.rollback()
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def new_user(init_database):
    """
    Seeds the database with a standard non-admin user.

    Dynamically attaches `raw_password` to the model instance to allow test
    functions to authenticate easily without hardcoding credentials.
    """
    password = "test_password"  # nosec
    hashed = generate_password_hash(password)

    user = User(username="testuser", password=hashed, is_admin=False)

    init_database.session.add(user)
    init_database.session.commit()

    user.raw_password = password

    return user


@pytest.fixture(scope="function")
def auth_client(client, new_user):
    """
    Returns an HTTP test client pre-authenticated as a standard user.
    """
    client.post(
        "/auth/signin",
        data={"username": new_user.username, "password": new_user.raw_password},
        follow_redirects=True,
    )

    return client


@pytest.fixture(scope="function")
def admin_client(client, init_database):
    """
    Returns an HTTP test client pre-authenticated as a System Administrator.
    """
    password = "admin_password"  # nosec
    hashed = generate_password_hash(password)

    admin = User(username="admin", password=hashed, is_admin=True)

    init_database.session.add(admin)
    init_database.session.commit()

    client.post(
        "/auth/signin",
        data={"username": "admin", "password": password},
        follow_redirects=True,
    )

    return client
