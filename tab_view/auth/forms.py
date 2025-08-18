from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class SignInForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me signed in', default=False)
    submit = SubmitField('Sign In')
