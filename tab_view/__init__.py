from flasgger import Swagger
from flask import Flask, jsonify, redirect, request, url_for
from flask_apscheduler import APScheduler
from flask_limiter import Limiter
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix

from tab_view.config import ProductionConfig
from tab_view.utils import configure_logging, get_user_or_ip, wait_for_db

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler()
limiter = Limiter(key_func=get_user_or_ip, default_limits=["200 per hour"])


def create_app(config_class=ProductionConfig):
    """Create and configure the Flask application"""

    app = Flask(__name__)
    app.config.from_object(config_class)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    configure_logging(app)
    app.logger.info("Application starting up...")

    app.config["SCHEDULER_API_ENABLED"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    limiter.init_app(app)

    Swagger(
        app,
        template={
            "swagger": "2.0",
            "info": {
                "title": "TabView API",
                "description": "API documentation for the \
                    TabView Event Management System.",
                "version": "1.0.0",
            },
        },
    )

    login_manager.login_view = "auth.signin"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.unauthorized_handler
    def unauthorized():
        client_ip = request.remote_addr
        requested_path = request.path
        app.logger.warning(
            f"Unauthorized access attempt to '{requested_path}' from IP: {client_ip}"
        )

        if request.path.startswith("/api/"):
            response = jsonify(
                {
                    "error": "Unauthorized",
                    "message": "Authentication required. Please log in.",
                    "status": 401,
                }
            )
            response.status_code = 401
            response.headers["WWW-Authenticate"] = 'Session realm="Login Required"'
            return response

        return redirect(url_for("auth.signin", next=request.url))

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/health")
    def health_check():
        """A silent endpoint for Docker Healthcheck"""
        return {"status": "healthy"}, 200

    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .devices import devices_bp
    from .errors import errors_bp
    from .events import events_bp
    from .media import media_bp
    from .settings import settings_bp
    from .users import users_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(devices_bp, url_prefix="/devices")
    app.register_blueprint(media_bp, url_prefix="/media")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(events_bp, url_prefix="/api/v1/events")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(errors_bp)

    csrf.exempt(events_bp)

    from .commands import create_user_command, seed_db_command

    app.cli.add_command(create_user_command)
    app.cli.add_command(seed_db_command)

    if not app.config.get("TESTING"):
        with app.app_context():
            wait_for_db(app)
            app.logger.info("Application initialization complete. Database ready.")

    return app
