import logging
import os
from werkzeug.utils import secure_filename
from flask import redirect, url_for, render_template, current_app, flash, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from . import media_bp
from .forms import MediaUploadForm, MediaUpdateForm, MediaDeleteForm
from tab_view import db
from tab_view.models import Media, Device
from tab_view.utils import detect_type


logger = logging.getLogger(__name__)


@media_bp.route('/')
@login_required
def get_all_media():
    form = MediaDeleteForm()

    page = request.args.get('page', 1, type=int)
    per_page = 9
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
        
        logger.info(f"User {current_user.id} attempting to upload file: {filename}")

        if len(filename) > 255:
            msg = f'Filename is too long: {filename} (User: {current_user.id})'
            logger.warning(msg)
            flash('Filename is too long (max 255 characters).', 'danger')
            return render_template('media/new-media.html', form=form)

        existing = Media.query.filter_by(filename=filename).first()
        if not existing:
            try:
                save_path = os.path.join(current_app.static_folder, 'uploads', filename)
                file.save(save_path)

                media = Media(filename=filename, media_type=detect_type(filename))
                db.session.add(media)
                db.session.commit()
                
                logger.info(f"Media added successfully: {filename} (ID: {media.id}) by User {current_user.id}")
                flash('Media added successfully!', 'success')
                return redirect(url_for('media.get_all_media'))
            except Exception as e:
                logger.error(f"Error saving file {filename}: {str(e)} (User: {current_user.id})")
                flash(f'Error saving file: {str(e)}', 'danger')
        else:
            logger.warning(f"Upload failed - duplicate filename: {filename} (User: {current_user.id})")
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
        new_filename_base = secure_filename(form.filename.data)
        full_filename = f"{new_filename_base}.{file_ext}"

        logger.info(f"User {current_user.id} attempting to rename media ID {media_id} from '{media.filename}' to '{full_filename}'")

        existing = Media.query.filter_by(filename=full_filename).first()
        if existing and existing.id != media.id:
            logger.warning(f"Rename failed - target filename exists: {full_filename} (User: {current_user.id})")
            flash('A file with this name already exists.', 'danger')
            return redirect(url_for('media.update_media', media_id=media.id))

        old_path = os.path.join(current_app.static_folder, 'uploads', media.filename)
        new_path = os.path.join(current_app.static_folder, 'uploads', full_filename)

        try:
            os.rename(old_path, new_path)
            
            old_name = media.filename
            media.filename = full_filename
            db.session.commit()
            
            logger.info(f"Media renamed successfully: {old_name} -> {full_filename} (ID: {media.id}) by User {current_user.id}")
            flash('Media updated successfully!', 'success')
            return redirect(url_for('media.get_all_media'))
            
        except FileNotFoundError:
            logger.warning(f"Rename failed - physical file missing: {old_path} (User: {current_user.id})")
            flash('Nie znaleziono pliku fizycznego do zmiany nazwy.', 'warning')
            return redirect(url_for('media.update_media', media_id=media.id))
        except Exception as e:
            logger.error(f"Error renaming file {media.filename}: {str(e)} (User: {current_user.id})")
            flash(f'Error renaming file: {str(e)}', 'danger')

    return render_template('media/update-media.html', form=form, media=media, 
                           file_ext=file_ext, filename_no_ext=filename_no_ext)


@media_bp.route('/delete/<int:media_id>', methods=['POST'])
@login_required
def delete_media(media_id):
    logger.info(f"User {current_user.id} requesting deletion of media ID {media_id}")

    if media_id == 1:
        logger.warning(f"User {current_user.id} attempted to delete DEFAULT media (ID 1) - Action blocked")
        flash('Nie można usunąć domyślnego obrazka.', 'danger')
        return redirect(url_for('media.get_all_media'))
    
    media = Media.query.get_or_404(media_id)
    filename = media.filename
    file_path = os.path.join(current_app.static_folder, 'uploads', filename)

    devices_using_media = Device.query.filter_by(media_id=media.id).all()
    if devices_using_media:
        count = len(devices_using_media)
        logger.info(f"Resetting media to default for {count} devices linked to media ID {media_id}")
        for device in devices_using_media:
            device.media_id = 1

    try:
        db.session.delete(media)
        db.session.commit()

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Physical file deleted: {filename}")
        else:
            logger.warning(f"Physical file not found: {filename}")
        
        logger.info(f"Media deleted successfully: {filename} (ID: {media_id})")
        flash('Plik został usunięty pomyślnie.', 'success')

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Delete failed: Media {media_id} is in use elsewhere (IntegrityError).")
        flash('Nie można usunąć tego pliku, ponieważ jest on przypisany do Wydarzenia (Events). Usuń powiązanie w wydarzeniu najpierw.', 'danger')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Critical error during media deletion ID {media_id}: {str(e)}")
        flash(f'Wystąpił nieoczekiwany błąd: {str(e)}', 'danger')

    return redirect(url_for('media.get_all_media'))
