from flask import Blueprint


errors_bp = Blueprint("errors", __name__)


from . import handlers  # noqa: F401, E402
