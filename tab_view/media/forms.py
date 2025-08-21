from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError
from flask_wtf.file import FileField, FileAllowed


class MediaUploadForm(FlaskForm):
    file = FileField('File', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'mp4'], 'Images and Videos only!'), Length(max=255)])
    submit = SubmitField('Add')


class MediaUpdateForm(FlaskForm):
    filename = StringField('Filename', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'mp4'], 'Images and Videos only!'), Length(max=255)])
    submit = SubmitField('Update')
    