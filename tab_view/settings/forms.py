from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import BooleanField, FileField, IntegerField, PasswordField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class CleanupEventsForm(FlaskForm):
    months = IntegerField(
        "Months",
        validators=[NumberRange(min=1, message="Months must be at least 1.")],
        default=1,
    )
    dry_run = BooleanField("Preview only (show what would be deleted)", default=True)
    submit = SubmitField("Run cleanup")


class DefaultImageForm(FlaskForm):
    file = FileField(
        "Upload new default image",
        validators=[
            FileRequired(message="Please select an image file."),
            FileAllowed(["jpg", "jpeg", "png", "gif"], "Images only (JPG, PNG, GIF)!"),
        ],
    )
    submit = SubmitField("Upload and Replace")


class DeleteSystemTagForm(FlaskForm):
    password = PasswordField("Admin Password", validators=[DataRequired()])
    submit = SubmitField("Confirm Deletion")
