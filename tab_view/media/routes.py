from werkzeug.utils import secure_filename
from flask import redirect, url_for, render_template, current_app
from . import media_bp
from .forms import MediaUploadForm
from tab_view import db
from tab_view.models import Media
from tab_view.utils import detect_type
import os


@media_bp.route('/new', methods=['GET', 'POST'])
def new_media():
    form = MediaUploadForm()

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.static_folder, 'uploads', filename))

        media = Media(filename=filename, media_type=detect_type(filename))
        db.session.add(media)
        db.session.commit()
        return redirect(url_for('devices'))
    return render_template('new-media.html', form=form)


# ! Next step: adding media. Check why PDFs are passing.