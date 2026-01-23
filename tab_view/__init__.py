import logging
from flask import Flask, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler
from flask_limiter import Limiter
from tab_view.utils import wait_for_db, get_user_or_ip, configure_logging
from tab_view.config import ProductionConfig


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()
limiter = Limiter(
    key_func=get_user_or_ip,
    default_limits=["200 per hour"]
)


def create_app(config_class=ProductionConfig):
    """Create and configure the Flask application"""

    app = Flask(__name__)
    app.config.from_object(config_class)

    configure_logging(app)    
    app.logger.info("Application starting up...")

    app.config['SCHEDULER_API_ENABLED'] = False


    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    limiter.init_app(app)


    login_manager.login_view = 'auth.signin'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.unauthorized_handler
    def unauthorized():
        client_ip = request.remote_addr
        requested_path = request.path
        app.logger.warning(f"Unauthorized access attempt to '{requested_path}' from IP: {client_ip}")

        if request.path.startswith('/api/'):
            response = jsonify({
                'error': 'Unauthorized',
                'message': 'Authentication required. Please log in.',
                'status': 401
            })
            response.status_code = 401
            response.headers['WWW-Authenticate'] = 'Session realm="Login Required"'
            return response
            
        return redirect(url_for('auth.signin', next=request.url))

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    

    from .auth import auth_bp
    from .devices import devices_bp
    from .media import media_bp
    from .users import users_bp
    from .events import events_bp
    from .maintenance import maintenance_bp
    from .errors import errors_bp


    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(devices_bp, url_prefix='/devices')
    app.register_blueprint(media_bp, url_prefix='/media')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(events_bp, url_prefix='/api/v1/events')
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    app.register_blueprint(errors_bp)


    csrf.exempt(events_bp)


    @app.route('/')
    @limiter.exempt
    def index():
        return redirect(url_for('devices.get_all_devices'))
    

    if not app.config.get("TESTING"):
        with app.app_context():
            wait_for_db(app)
            app.logger.info("Application initialization complete. Database ready.")


    return app
