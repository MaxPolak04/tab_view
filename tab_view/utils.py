from sqlalchemy import select, literal
from sqlalchemy.exc import OperationalError
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


def str_to_bool(value):
    return str(value).lower() in ('true', '1', 'yes')


def detect_type(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    return 'image' if ext in ['jpg', 'jpeg', 'png'] else 'video'

