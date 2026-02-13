from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class MediaUploadForm(FlaskForm):
    file = FileField("File", validators=[DataRequired()])
    tag_id = SelectField("Existing Tag", coerce=int, validators=[Optional()])
    new_tag_name = StringField("Or create new tag", validators=[Optional()])
    submit = SubmitField("Upload")


class TagForm(FlaskForm):
    name = StringField("Tag Name", validators=[DataRequired()])
    submit = SubmitField("Save")


class MediaUpdateForm(FlaskForm):
    tag_id = SelectField("Tag", coerce=int, validators=[DataRequired()])
    filename = StringField("Filename", validators=[DataRequired()])
    submit = SubmitField("Update")


class MediaDeleteForm(FlaskForm):
    submit = SubmitField("Delete")
