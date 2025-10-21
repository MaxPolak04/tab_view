from flask import Blueprint
from flask_restful import Api
from .routes import EventResource


events_bp = Blueprint('events', __name__)
events_api = Api(events_bp)

events_api.add_resource(EventResource, '/', '/<int:event_id>')
