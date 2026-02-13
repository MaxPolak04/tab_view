from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, BooleanField, StringField
from wtforms.validators import DataRequired


class SignInForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Keep me signed in", default=False)
    submit = SubmitField("Sign In")
