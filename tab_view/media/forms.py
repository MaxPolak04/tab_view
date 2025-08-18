from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, ValidationError
from flask_wtf.file import FileField, FileAllowed


class MediaUploadForm(FlaskForm):
    file = FileField('File', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'mp4'], 'Images and Videos only!')])
    submit = SubmitField('Add')
