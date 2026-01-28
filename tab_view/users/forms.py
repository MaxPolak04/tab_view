from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, Optional


class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20), Regexp(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])[\w!@#$%^&*()\-_=+{}\[\]:;,.?]{6,20}$',
        message='Password must be 6–20 characters long, contain at least one lowercase letter, one uppercase letter, and one special character. Spaces and disallowed characters are not allowed.'
    )])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    is_admin = BooleanField('Is Admin', default=False, validators=[Optional()])
    submit = SubmitField('Add')


class UpdateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=15)])
    password = PasswordField('Password', validators=[Optional(), Length(min=6, max=20), Regexp(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])[\w!@#$%^&*()\-_=+{}\[\]:;,.?]{6,20}$',
        message='Password must be 6–20 characters long, contain at least one lowercase letter, one uppercase letter, and one special character. Spaces and disallowed characters are not allowed.'
    )])
    confirm_password = PasswordField('Confirm Password', validators=[Optional(), EqualTo('password', message='Passwords must match')])
    is_admin = BooleanField('Is Admin', default=False, validators=[Optional()])
    submit = SubmitField('Update')


class DeleteUserForm(FlaskForm):
    submit = SubmitField('Delete')