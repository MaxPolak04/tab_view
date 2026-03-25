from flask_wtf import FlaskForm
from wtforms import MultipleFileField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Optional


class MediaUploadForm(FlaskForm):
    file = MultipleFileField(
        "File", validators=[DataRequired()], render_kw={"multiple": True}
    )
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
