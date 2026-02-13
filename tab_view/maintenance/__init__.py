from flask import Blueprint


maintenance_bp = Blueprint("maintenance", __name__)

from . import routes  # noqa: F401, E402
