from flask import Blueprint


devices_bp = Blueprint('devices', __name__)

from . import routes
