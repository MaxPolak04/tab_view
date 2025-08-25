from werkzeug.utils import secure_filename
from flask import redirect, url_for, render_template, current_app, flash, request
from flask_login import login_required
from . import media_bp
from .forms import MediaUploadForm, MediaUpdateForm, MediaDeleteForm
from tab_view import db, csrf
from tab_view.models import Media, Device
from tab_view.utils import detect_type
import os


@media_bp.route('/')
@login_required
def get_all_media():
    form = MediaDeleteForm()

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Media.query \
        .order_by(Media.id) \
        .paginate(page=page, per_page=per_page)
    
    media = pagination.items
    return render_template('media/media.html',
                           media=media,
                           pagination=pagination,
                           form=form)


@media_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_media():
    form = MediaUploadForm()

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        if len(filename) > 255:
            flash('Filename is too long (max 255 characters).', 'danger')
            return render_template('media/new-media.html', form=form)

        existing = Media.query.filter_by(filename=filename).first()
        if not existing:
            file.save(os.path.join(current_app.static_folder, 'uploads', filename))

            media = Media(filename=filename, media_type=detect_type(filename))
            db.session.add(media)
            db.session.commit()
            flash('Media added successfully!', 'success')
            return redirect(url_for('media.get_all_media'))
        else:
            flash('A file with this name already exists in the database.', 'danger')
    return render_template('media/new-media.html', form=form)


@media_bp.route('/update/<int:media_id>', methods=['GET', 'POST'])
@login_required
def update_media(media_id):
    media = Media.query.get_or_404(media_id)
    form = MediaUpdateForm()

    filename_no_ext, file_ext = os.path.splitext(media.filename)
    file_ext = file_ext.lstrip('.')

    if form.validate_on_submit():
        filename_no_ext = secure_filename(form.filename.data)
        full_filename = f"{filename_no_ext}.{file_ext}"

        existing = Media.query.filter_by(filename=full_filename).first()
        if existing and existing.id != media.id:
            flash('A file with this name already exists.', 'danger')
            return redirect(url_for('media.update_media', media_id=media.id))

        old_path = os.path.join(current_app.static_folder, 'uploads', media.filename)
        new_path = os.path.join(current_app.static_folder, 'uploads', full_filename)

        try:
            os.rename(old_path, new_path)
        except FileNotFoundError:
            flash('Nie znaleziono pliku fizycznego do zmiany nazwy.', 'warning')
            return redirect(url_for('media.update_media', media_id=media.id))

        media.filename = full_filename
        db.session.commit()
        flash('Media updated successfully!', 'success')
        return redirect(url_for('media.get_all_media'))
    return render_template('media/update-media.html', form=form, media=media, 
                           file_ext=file_ext, filename_no_ext=filename_no_ext)


@media_bp.route('/delete/<int:media_id>', methods=['POST'])
@login_required
def delete_media(media_id):
    if media_id == 1:
        flash('The default image cannot be deleted.', 'danger')
        return redirect(url_for('media.get_all_media'))
    
    media = Media.query.get_or_404(media_id)
    file_path = os.path.join(current_app.static_folder, 'uploads', media.filename)

    devices_using_media = Device.query.filter_by(media_id=media.id).all()
    if devices_using_media:
        for device in devices_using_media:
            device.media_id = 1

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            flash('Plik fizyczny nie istnieje — usunięto tylko z bazy.', 'warning')
            db.session.delete(media)
            db.session.commit()
            return redirect(url_for('media.get_all_media'))
    except Exception as e:
        flash(f'Błąd podczas usuwania pliku: {str(e)}', 'danger')
        return redirect(url_for('media.get_all_media'))

    db.session.delete(media)
    db.session.commit()
    flash('Media deleted successfully!', 'success')
    return redirect(url_for('media.get_all_media'))
