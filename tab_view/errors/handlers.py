from flask import render_template
from werkzeug.exceptions import HTTPException
from . import errors_bp


@errors_bp.app_errorhandler(HTTPException)
def handle_http_error(error):
    return render_template(f"errors/{error.code}.html", error=error), error.code

@errors_bp.app_errorhandler(Exception)
def handle_generic_error(error):
    return render_template("errors/500.html", error=error), 500