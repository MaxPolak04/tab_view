import logging
from datetime import datetime, timedelta
from flask import (
    render_template,
    url_for,
    redirect,
    session,
    flash,
    current_app,
    request,
)
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from tab_view import limiter
from tab_view.auth.forms import SignInForm
from tab_view.models import User, db


logger = logging.getLogger(__name__)


@auth_bp.route("/signin", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def signin():
    form = SignInForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember_me = form.remember_me.data
        client_ip = request.remote_addr

        logger.info(f"Login attempt for user '{username}' from IP: {client_ip}")

        user = User.query.filter_by(username=username).first()

        if not user:
            logger.warning(
                f"Login failed - user not found: '{username}' (IP: {client_ip})"
            )
            flash("User not found!", "danger")
            return redirect(url_for("auth.signin"))

        if not check_password_hash(user.password, password):
            logger.warning(
                f"Login failed - invalid password for user '{username}' (ID: {user.id}) from IP: {client_ip}"
            )
            flash("Incorrect password!", "danger")
            return redirect(url_for("auth.signin"))

        session.permanent = True
        if remember_me:
            current_app.permanent_session_lifetime = timedelta(days=7)
        else:
            current_app.permanent_session_lifetime = timedelta(minutes=15)

        login_user(user, remember=remember_me, fresh=True)

        try:
            user.last_login_at = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating last_login_at for user {user.id}: {str(e)}")

        logger.info(
            f"User logged in successfully: {user.username} (ID: {user.id}) from IP: {client_ip}"
        )

        flash("Logged in successfully!", "success")
        return redirect(url_for("devices.get_all_devices"))

    return render_template("sign-in.html", form=form)


@auth_bp.route("/signout")
@login_required
def signout():
    user_id = current_user.id
    username = current_user.username

    logout_user()

    logger.info(f"User logged out: {username} (ID: {user_id})")

    flash("Logged out successfully!", "success")
    return redirect(url_for("index"))
