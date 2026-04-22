import logging
import sys
import time
from functools import wraps

from flask import abort, jsonify, request
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_required
from sqlalchemy import literal, select
from sqlalchemy.exc import OperationalError


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


def log_audit_action(action, entity_type, details):
    """
    Records the event in the audit log (AuditLog).
    Example usage: log_audit_action("UPDATE", "Media",
    "The tag for the video.mp4 file was changed")
    """
    from tab_view import db
    from tab_view.models import AuditLog

    ip_address = None
    if request:
        ip_address = request.remote_addr

    user_id = (
        current_user.id if current_user and current_user.is_authenticated else None
    )

    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            details=details,
            ip_address=ip_address,
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        import logging

        logging.getLogger(__name__).error(f"Failed to save audit log: {e}")
