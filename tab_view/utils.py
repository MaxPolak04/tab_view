from flask import abort, jsonify
from sqlalchemy import select, literal
from sqlalchemy.exc import OperationalError
from flask_login import current_user, login_required
from flask_limiter.util import get_remote_address
import logging
from functools import wraps
import time
import sys


def wait_for_db(app):
    from tab_view import db

    with app.app_context():
        connected = False
        attempt = 1
        while not connected:
            try:
                db.session.execute(select(literal(1)))
                connected = True
                if attempt > 1:
                    app.logger.info("Database connection established successfully.")
            except OperationalError:
                app.logger.warning(
                    f"Database not ready (attempt {attempt}), waiting 2s..."
                )
                time.sleep(2)
                attempt += 1


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            logging.getLogger("tab_view.access").warning(
                f"Forbidden access attempt to admin area by User {current_user.id}"
            )
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def str_to_bool(value):
    return str(value).lower() in ("true", "1", "yes")


def detect_type(filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return "image" if ext in ["jpg", "jpeg", "png", "gif"] else "video"


def error_response(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def get_user_or_ip():
    if current_user.is_authenticated:
        return str(current_user.id)
    return get_remote_address()


def configure_logging(app):
    """
    Configure application logging to syslog.
    """
    if app.config.get("TESTING"):
        return

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    handler.setFormatter(formatter)

    handler.setLevel(logging.INFO)

    app.logger.handlers.clear()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
