from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError
from tab_view.models import Device


class NewDevice(FlaskForm):
    name = StringField('Device Name', validators=[DataRequired(), Length(max=50)])
    device_url = StringField('Adres URL', validators=[DataRequired(), Regexp(
            r'^[a-zA-Z0-9_-]+$',
            message='The URL can only contain letters, numbers, hyphens, and underscores.'
        )])
    media_id = SelectField('Select media for this device:', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add')

    def validate_device_url(self, field):
        if Device.query.filter_by(device_url=field.data).first():
            raise ValidationError('This URL is already in use by another device.')


class UpdateDevice(FlaskForm):
    name = StringField('Device Name', validators=[DataRequired(), Length(max=50)])
    device_url = StringField('Adres URL', validators=[DataRequired(), Regexp(
            r'^[a-zA-Z0-9_-]+$',
            message='The URL can only contain letters, numbers, hyphens, and underscores.'
        )])
    media_id = SelectField('Select media for this device:', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update')

    def validate_device_url(self, field):
        if Device.query.filter_by(device_url=field.data).first():
            raise ValidationError('This URL is already in use by another device.')
