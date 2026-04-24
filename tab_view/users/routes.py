import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from tab_view import db
from tab_view.models import User
from tab_view.utils import admin_required, log_audit_action

from . import users_bp
from .forms import CreateUserForm, DeleteUserForm, UpdateUserForm

logger = logging.getLogger(__name__)


@users_bp.route("/")
@admin_required
def get_all_users():
    form = DeleteUserForm()

    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = User.query.order_by(User.id).paginate(page=page, per_page=per_page)

    users = pagination.items
    return render_template(
        "users/users.html", users=users, pagination=pagination, form=form
    )


@users_bp.route("/new", methods=["GET", "POST"])
@admin_required
def create_user():
    form = CreateUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.password.data)
        is_admin = form.is_admin.data

        if User.query.filter_by(username=username).first():
            logger.warning(
                f"Create user failed - username '{username}' exists "
                f"(Admin: {current_user.id})"
            )
            flash("Username already exists.", "danger")
            return render_template("users/new-user.html", form=form)

        try:
            new_user = User(username=username, password=password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()

            logger.info(
                f"User created: {username} (ID: {new_user.id}, Admin: "
                f"{is_admin}) by Admin {current_user.id}"
            )

            # --- AUDIT LOG ---
            log_audit_action(
                "CREATE",
                "User",
                f"Created account for '{username}' (Admin privileges: {is_admin}).",
            )

            flash("User created successfully!", "success")
            return redirect(url_for("users.get_all_users"))

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error creating user '{username}': {str(e)} (Admin: {current_user.id})"
            )
            flash(f"Error creating user: {str(e)}", "danger")

    return render_template("users/new-user.html", form=form)


@users_bp.route("/update/<int:user_id>", methods=["GET", "POST"])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(obj=user)

    if form.validate_on_submit():
        # --- SECURITY CHECK 1: Prevent admin from revoking their own privileges ---
        if user.id == current_user.id and not form.is_admin.data:
            logger.warning(
                f"Admin {current_user.id} attempted to revoke their own admin rights."
            )
            flash("You cannot revoke your own administrator privileges.", "danger")
            return redirect(url_for("users.update_user", user_id=user.id))

        # --- SECURITY CHECK 2: Protect the built-in 'admin' account ---
        if user.username == "admin":
            if not form.is_admin.data:
                logger.warning(
                    f"Admin {current_user.id} attempted to revoke built-in "
                    "'admin' privileges."
                )
                flash(
                    "You cannot revoke privileges from the built-in 'admin' account.",
                    "danger",
                )
                return redirect(url_for("users.update_user", user_id=user.id))

            if form.username.data != "admin":
                logger.warning(
                    f"Admin {current_user.id} attempted to "
                    "rename the built-in 'admin' account."
                )
                flash("You cannot rename the built-in 'admin' account.", "danger")
                return redirect(url_for("users.update_user", user_id=user.id))

        old_username = user.username
        user.username = form.username.data
        password_changed = False

        if form.password.data:
            user.password = generate_password_hash(form.password.data)
            password_changed = True
            logger.info(
                f"Password changed for user ID {user.id} by Admin {current_user.id}"
            )

        user.is_admin = form.is_admin.data

        try:
            db.session.commit()

            logger.info(
                f"User updated: {old_username} -> {user.username} "
                f"(ID: {user.id}) by Admin {current_user.id}"
            )

            # --- AUDIT LOG ---
            audit_details = f"Updated user '{old_username}'."
            if old_username != user.username:
                audit_details += f" Renamed to '{user.username}'."
            if password_changed:
                audit_details += " Password was reset."
            audit_details += f" Admin privileges: {user.is_admin}."

            log_audit_action("UPDATE", "User", audit_details.strip())

            flash("User updated successfully!", "success")
            return redirect(url_for("users.get_all_users"))

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error updating user ID {user_id}: {str(e)} (Admin: {current_user.id})"
            )
            flash(f"Error updating user: {str(e)}", "danger")

    elif request.method == "GET":
        form.username.data = user.username
        form.is_admin.data = user.is_admin

    return render_template("users/update-user.html", form=form, user=user)


@users_bp.route("/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        logger.warning(
            f"Admin {current_user.id} attempted to delete their own account "
            "- Action blocked"
        )
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("users.get_all_users"))

    user = User.query.get_or_404(user_id)

    # --- SECURITY CHECK: Prevent deleting the built-in 'admin' account ---
    if user.username == "admin":
        logger.warning(
            f"Admin {current_user.id} attempted to delete the built-in 'admin' account "
            "- Action blocked"
        )
        flash("You cannot delete the built-in 'admin' account.", "danger")
        return redirect(url_for("users.get_all_users"))

    username = user.username

    try:
        db.session.delete(user)
        db.session.commit()

        logger.info(
            f"User deleted: {username} (ID: {user_id}) by Admin {current_user.id}"
        )

        # --- AUDIT LOG ---
        log_audit_action("DELETE", "User", f"Permanently deleted account '{username}'.")

        flash("User deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error deleting user ID {user_id}: {str(e)} (Admin: {current_user.id})"
        )
        flash(f"Error deleting user: {str(e)}", "danger")

    return redirect(url_for("users.get_all_users"))
