import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from werkzeug.security import generate_password_hash

from tab_view import db
from tab_view.models import User
from tab_view.utils import admin_required

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
                f"Create user failed - username '{username}' exists \
                    (Admin: {current_user.id})"
            )
            flash("Username already exists.", "danger")
            return render_template("users/new-user.html", form=form)

        try:
            new_user = User(username=username, password=password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()

            logger.info(
                f"User created: {username} (ID: {new_user.id}, Admin: \
                    {is_admin}) by Admin {current_user.id}"
            )
            flash("User created successfully!", "success")
            return redirect(url_for("users.get_all_users"))

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error creating user '{username}': {str(e)} \
                    (Admin: {current_user.id})"
            )
            flash(f"Error creating user: {str(e)}", "danger")

    return render_template("users/new-user.html", form=form)


@users_bp.route("/update/<int:user_id>", methods=["GET", "POST"])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(obj=user)

    if form.validate_on_submit():
        old_username = user.username
        user.username = form.username.data

        if form.password.data:
            user.password = generate_password_hash(form.password.data)
            logger.info(
                f"Password changed for user ID {user.id} \
                    by Admin {current_user.id}"
            )

        user.is_admin = form.is_admin.data

        try:
            db.session.commit()

            logger.info(
                f"User updated: {old_username} -> {user.username} \
                    (ID: {user.id}) by Admin {current_user.id}"
            )
            flash("User updated successfully!", "success")
            return redirect(url_for("users.get_all_users"))

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error updating user ID {user_id}: {str(e)} \
                    (Admin: {current_user.id})"
            )
            flash(f"Error updating user: {str(e)}", "danger")

    return render_template("users/update-user.html", form=form, user=user)


@users_bp.route("/delete/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        logger.warning(
            f"Admin {current_user.id} attempted to delete their own account \
              - Action blocked"
        )
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("users.get_all_users"))

    user = User.query.get_or_404(user_id)
    username = user.username

    try:
        db.session.delete(user)
        db.session.commit()

        logger.info(
            f"User deleted: {username} (ID: {user_id}) by Admin {current_user.id}"
        )
        flash("User deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error deleting user ID {user_id}: {str(e)} (Admin: {current_user.id})"
        )
        flash(f"Error deleting user: {str(e)}", "danger")

    return redirect(url_for("users.get_all_users"))
