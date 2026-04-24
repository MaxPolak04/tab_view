import logging

from flask import jsonify, render_template, request
from flask_login import current_user
from werkzeug.exceptions import HTTPException

from tab_view.utils import log_audit_action

from . import errors_bp

logger = logging.getLogger(__name__)


def wants_json_response():
    return (
        request.path.startswith("/api/")
        or request.accept_mimetypes["application/json"]
        >= request.accept_mimetypes["text/html"]
    )


@errors_bp.app_errorhandler(HTTPException)
def handle_http_error(error):
    """
    Handling HTTP errors (400, 401, 403, 404, 405, etc.)
    """
    user_info = (
        f"User: {current_user.id}"
        if current_user.is_authenticated
        else f"IP: {request.remote_addr}"
    )
    logger.warning(
        f"HTTP {error.code}: {error.name} - Path: {request.path} ({user_info})"
    )

    if error.code in [401, 403] and current_user.is_authenticated:
        log_audit_action(
            "SECURITY",
            "System",
            f"Blocked unauthorized access attempt to '{request.path}' \
                (HTTP {error.code}).",
        )

    if wants_json_response():
        return jsonify(
            {"error": error.name, "message": error.description, "code": error.code}
        ), error.code

    return render_template(
        "errors/error.html",
        error_code=error.code,
        error_name=error.name,
        error_desc=error.description,
    ), error.code


@errors_bp.app_errorhandler(Exception)
def handle_exception(error):
    """
    Handling critical errors (500)
    """
    user_info = (
        f"User: {current_user.id}"
        if current_user.is_authenticated
        else f"IP: {request.remote_addr}"
    )
    logger.error(
        f"Critical Exception: {str(error)} - Path: {request.path} ({user_info})",
        exc_info=True,
    )

    if wants_json_response():
        return jsonify(
            {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred.",
                "code": 500,
            }
        ), 500

    return render_template(
        "errors/error.html",
        error_code=500,
        error_name="Internal Server Error",
        error_desc="Something went wrong on our end. \
            Administrators have been notified.",
    ), 500
