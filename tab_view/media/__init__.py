from flask import Blueprint

media_bp = Blueprint("media", __name__)

from . import routes  # noqa: F401, E402
