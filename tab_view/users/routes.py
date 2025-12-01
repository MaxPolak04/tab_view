from werkzeug.security import generate_password_hash
from flask import redirect, url_for, render_template, flash, request
from . import users_bp
from .forms import CreateUserForm, UpdateUserForm, DeleteUserForm
from tab_view import db
from tab_view.models import User
from tab_view.utils import admin_required


@users_bp.route('/')
@admin_required
def get_all_users():
    form = DeleteUserForm()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = User.query \
        .order_by(User.id) \
        .paginate(page=page, per_page=per_page)
    
    users = pagination.items
    return render_template('users/users.html',
                           users=users,
                           pagination=pagination,
                           form=form)


@users_bp.route('/new', methods=['GET', 'POST'])
@admin_required
def create_user():
    form = CreateUserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = generate_password_hash(form.username.data)
        is_admin = form.is_admin.data

        new_user = User(username=username, password=password, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('users.get_all_users'))
    return render_template('users/new-user.html', form=form)


@users_bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data

        if form.password.data:
            user.password = generate_password_hash(form.password.data)

        user.is_admin = form.is_admin.data

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('users.get_all_users'))
    return render_template('users/update-user.html', form=form, user=user)


@users_bp.route('/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users.get_all_users'))