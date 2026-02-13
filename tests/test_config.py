from tab_view.config import ProductionConfig
from tab_view import create_app


def test_checking_config(app):
    """
    Check if TestingConfig loads correctly.
    """
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    assert app.config["WTF_CSRF_ENABLED"] is False
    assert app.config["SCHEDULER_API_ENABLED"] is False


def test_production_config(mocker):
    """
    Check if ProductionConfig is used correctly by create_app.
    """
    mocker.patch("tab_view.wait_for_db")

    fake_db_url = "mysql+pymysql://user:pass@localhost/prod_db"
    fake_secret = "prod-secret-key"

    mocker.patch.object(ProductionConfig, "SQLALCHEMY_DATABASE_URI", fake_db_url)
    mocker.patch.object(ProductionConfig, "SECRET_KEY", fake_secret)

    prod_app = create_app(ProductionConfig)

    assert prod_app.config["TESTING"] is False
    assert prod_app.config["DEBUG"] is False
    assert prod_app.config["SQLALCHEMY_DATABASE_URI"] == fake_db_url
    assert prod_app.config["SECRET_KEY"] == fake_secret
