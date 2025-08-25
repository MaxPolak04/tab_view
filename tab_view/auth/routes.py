from flask import render_template, url_for, redirect, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from . import auth_bp
from tab_view.auth.forms import SignInForm
from tab_view.models import User, db
from datetime import timedelta


@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    form = SignInForm()

    if form.validate_on_submit():
        password = form.password.data
        remember_me = form.remember_me.data
        user = User.query.filter_by(username='admin').first()

        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('auth.signin'))
        if not check_password_hash(user.password, password):
            flash('Incorrect password!', 'danger')
            return redirect(url_for('auth.signin'))
        
        session.permanent = True
        if remember_me:
            current_app.permanent_session_lifetime = timedelta(days=7)
        else:
            current_app.permanent_session_lifetime = timedelta(minutes=15)
        
        login_user(user, remember=remember_me, fresh=True)
        user.last_login_at = db.func.now()
        db.session.commit()

        flash('Logged in successfully!', 'success')
        return redirect(url_for('devices.get_all_devices'))
    return render_template('sign-in.html', form=form)


@auth_bp.route('/signout')
@login_required
def signout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))
