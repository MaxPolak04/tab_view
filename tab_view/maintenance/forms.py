from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SubmitField
from wtforms.validators import NumberRange


class CleanupEventsForm(FlaskForm):
    months = IntegerField(
        "Months",
        validators=[NumberRange(min=1, message="Months must be at least 1.")],
        default=1,
    )
    dry_run = BooleanField("Preview only (show what would be deleted)", default=True)
    submit = SubmitField("Run cleanup")
