from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp


class CreateUserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=15)]
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=6, max=20),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]+$",
                message="Password must be 6-20 characters long, contain at least one \
                    lowercase letter, one uppercase letter, one digit, and one special \
                    character. Allowed special characters are strictly: \
                        ! @ # $ % ^ & *",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    show_password = BooleanField("Show Password")
    is_admin = BooleanField("Is Admin", default=False, validators=[Optional()])
    submit = SubmitField("Add")


class UpdateUserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=3, max=15)]
    )
    password = PasswordField(
        "Password",
        validators=[
            Optional(),
            Length(min=6, max=20),
            Regexp(
                r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]+$",
                message="Password must be 6-20 characters long, contain at least one \
                    lowercase letter, one uppercase letter, one digit, and one special \
                    character. Allowed special characters are strictly: \
                        ! @ # $ % ^ & *",
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[Optional(), EqualTo("password", message="Passwords must match")],
    )
    show_password = BooleanField("Show Password")
    is_admin = BooleanField("Is Admin", default=False, validators=[Optional()])
    submit = SubmitField("Update")


class DeleteUserForm(FlaskForm):
    submit = SubmitField("Delete")
