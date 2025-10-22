from flask import abort, jsonify
from sqlalchemy import select, literal
from sqlalchemy.exc import OperationalError
from flask_login import current_user, login_required
from functools import wraps
import time


def wait_for_db(app):
    from tab_view import db
    with app.app_context():
        connected = False
        while not connected:
            try:
                db.session.execute(select(literal(1)))
                connected = True
            except OperationalError:
                print("Database not ready, waiting...")
                time.sleep(2)


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def str_to_bool(value):
    return str(value).lower() in ('true', '1', 'yes')


def detect_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return 'image' if ext in ['jpg', 'jpeg', 'png', 'gif'] else 'video'


def error_response(message, status_code):
    response = jsonify({'error': message})
    response.status_code = status_code
    return response
