from flask_wtf import FlaskForm
from wtforms import IntegerField, BooleanField, SubmitField
from wtforms.validators import NumberRange


class CleanupEventsForm(FlaskForm):
    years = IntegerField('Years', 
                        validators=[NumberRange(min=0, message='Years must be 0 or more.')],
                        default=1)
    months = IntegerField('Months', 
                         validators=[NumberRange(min=0, max=11, message='Months must be 0-11.')],
                         default=0)
    dry_run = BooleanField('Preview only (show what would be deleted)')
    submit = SubmitField('Run cleanup')

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.years.data == 0 and self.months.data == 0:
            self.years.errors.append('Provide at least one non-zero value for years or months.')
            self.months.errors.append('')
            return False
        return True

