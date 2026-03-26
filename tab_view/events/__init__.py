from flask import Blueprint, jsonify, request
from flask_restful import Api

from .api import EventAvailabilityResource, EventResource

events_bp = Blueprint("events", __name__)
events_api = Api(events_bp)

events_api.add_resource(EventResource, "/", "/<int:event_id>")
events_api.add_resource(EventAvailabilityResource, "/availability")


@events_bp.before_request
def validate_content_type():
    """
    Validate Content-Type for POST/PUT/PATCH requests.
    Returns 415 if Content-Type is not application/json.
    """
    if request.method in ["POST", "PUT", "PATCH"]:
        if not request.is_json:
            content_type = request.headers.get("Content-Type", "Not provided")
            return jsonify(
                {
                    "error": "Unsupported Media Type",
                    "message": "Content-Type must be application/json",
                    "received": content_type,
                    "status": 415,
                }
            ), 415
