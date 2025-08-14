from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from tab_view.utils import wait_for_db
from tab_view.config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    """Create and configure the Flask application"""

    app = Flask(__name__)
    app.config.from_object(Config)


    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)


    login_manager.login_view = 'auth.signin'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    

    from .auth import auth_bp
    from .errors import errors_bp


    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(auth_bp, url_prefix='/error')


    @app.route('/')
    def index():
        return redirect(url_for('')) # TODO: Fill this
    

    with app.app_context():
        wait_for_db(app)


    return app
