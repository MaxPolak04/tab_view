from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import BooleanField, FileField, IntegerField, SubmitField, TextAreaField
from wtforms.validators import Length, NumberRange, Optional


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


class ExportDataForm(FlaskForm):
    export_db = BooleanField("Export Database (JSON)", default=True)
    export_media = BooleanField("Export Media Files (Uploads)", default=True)
    submit = SubmitField("Export Data")


class ImportDataForm(FlaskForm):
    file = FileField(
        "Upload ZIP Archive",
        validators=[
            FileRequired(message="Please select a ZIP file."),
            FileAllowed(["zip"], "ZIP Archives only!"),
        ],
    )
    submit = SubmitField("Import and Restore")


class UploadMessageForm(FlaskForm):
    message = TextAreaField(
        "Upload Instructions Message", validators=[Optional(), Length(max=1000)]
    )
    submit = SubmitField("Save Message")
