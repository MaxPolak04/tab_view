import pytest
from tab_view import create_app, db
from tab_view.config import TestingConfig


@pytest.fixture()
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        yield app


@pytest.fixture
def database(app):
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
