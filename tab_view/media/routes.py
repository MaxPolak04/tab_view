from werkzeug.utils import secure_filename
from flask import redirect, url_for, render_template, current_app, flash, request
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from . import media_bp
from .forms import MediaUploadForm, TagForm, MediaUpdateForm, MediaDeleteForm
from tab_view import db
from tab_view.models import Media, Tag, Device
from tab_view.utils import detect_type, admin_required
import logging
import os


logger = logging.getLogger(__name__)


@media_bp.route('/')
@login_required
def get_all_media():
    form = MediaDeleteForm()

    # Filter and sort parameters
    tag_filter = request.args.get('tag', type=int)
    sort_by = request.args.get('sort', 'name_asc')
    page = request.args.get('page', 1, type=int)

    query = Media.query

    # Filtering by tag
    if tag_filter:
        query = query.filter_by(tag_id=tag_filter)

    # Alphabetical sorting
    if sort_by == 'name_asc':
        query = query.order_by(Media.filename.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(Media.filename.desc())
    else:
        query = query.order_by(Media.id)

    pagination = query.paginate(page=page, per_page=12)
    tags = Tag.query.all()

    return render_template('media/media.html',
                           media=pagination.items,
                           pagination=pagination,
                           tags=tags,
                           form=form,
                           current_tag=tag_filter,
                           current_sort=sort_by)


@media_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_media():
    form = MediaUploadForm()
    
    all_tags = Tag.query.order_by(Tag.name).all()
    form.tag_id.choices = [(0, '--- Select Existing Tag ---')] + [(t.id, t.name) for t in all_tags]

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        
        logger.info(f"User {current_user.id} attempting to upload file: {filename}")

        if len(filename) > 255:
            msg = f'Filename is too long: {filename} (User: {current_user.id})'
            logger.warning(msg)
            flash('Filename is too long (max 255 characters).', 'danger')
            return render_template('media/new-media.html', form=form)

        final_tag_id = None
        new_tag_input = form.new_tag_name.data
        selected_tag_id = form.tag_id.data

        # Scenario A: The user entered a new tag
        if new_tag_input and new_tag_input.strip():
            clean_tag_name = new_tag_input.strip()
            
            existing_tag = Tag.query.filter_by(name=clean_tag_name).first()
            if existing_tag:
                final_tag_id = existing_tag.id
                flash(f'Tag "{clean_tag_name}" already exists. Selected automatically.', 'info')
            else:
                try:
                    new_tag = Tag(name=clean_tag_name)
                    db.session.add(new_tag)
                    db.session.commit()
                    final_tag_id = new_tag.id
                    logger.info(f"Created new tag '{clean_tag_name}' (ID: {new_tag.id}) during upload by User {current_user.id}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error creating tag '{clean_tag_name}': {e}")
                    flash(f"Error creating new tag: {e}", "danger")
                    return render_template('media/new-media.html', form=form)
        
        # Scenario B: The user selected a tag from the list
        elif selected_tag_id and selected_tag_id != 0:
            final_tag_id = selected_tag_id
        
        # Scenario C: No choice
        else:
            flash('Please select an existing tag OR create a new one.', 'danger')
            return render_template('media/new-media.html', form=form)

        existing_file = Media.query.filter_by(filename=filename).first()
        if not existing_file:
            try:
                save_path = os.path.join(current_app.static_folder, 'uploads', filename)
                file.save(save_path)

                media = Media(
                    filename=filename, 
                    media_type=detect_type(filename),
                    tag_id=final_tag_id
                )
                db.session.add(media)
                db.session.commit()
                
                logger.info(f"Media added successfully: {filename} (ID: {media.id}) with Tag ID {final_tag_id} by User {current_user.id}")
                flash('Media added successfully!', 'success')
                return redirect(url_for('media.get_all_media'))
            
            except Exception as e:
                db.session.rollback()
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
    form.tag_id.choices = [(t.id, t.name) for t in Tag.query.all()]

    filename_no_ext, file_ext = os.path.splitext(media.filename)
    file_ext = file_ext.lstrip('.')

    if form.validate_on_submit():
        media.tag_id = form.tag_id.data

        new_filename_base = secure_filename(form.filename.data)
        full_filename = f"{new_filename_base}.{file_ext}"

        if full_filename != media.filename:
            logger.info(f"User {current_user.id} attempting to rename media ID {media_id}")

            existing = Media.query.filter_by(filename=full_filename).first()
            if existing and existing.id != media.id:
                flash('A file with this name already exists.', 'danger')
                return redirect(url_for('media.update_media', media_id=media.id))

            old_path = os.path.join(current_app.static_folder, 'uploads', media.filename)
            new_path = os.path.join(current_app.static_folder, 'uploads', full_filename)

            try:
                os.rename(old_path, new_path)
                media.filename = full_filename
            except FileNotFoundError:
                flash('Physical file not found for renaming.', 'warning')
            except Exception as e:
                flash(f'Error renaming file: {str(e)}', 'danger')
                return redirect(url_for('media.update_media', media_id=media.id))
        
        db.session.commit()
        flash('Media updated successfully!', 'success')
        return redirect(url_for('media.get_all_media'))

    elif request.method == 'GET':
        form.tag_id.data = media.tag_id
        form.filename.data = filename_no_ext

    return render_template('media/update-media.html', form=form, media=media, 
                           file_ext=file_ext, file_no_ext=filename_no_ext)


@media_bp.route('/delete/<int:media_id>', methods=['POST'])
@login_required
def delete_media(media_id):
    logger.info(f"User {current_user.id} requesting deletion of media ID {media_id}")

    if media_id == 1:
        logger.warning(f"User {current_user.id} attempted to delete DEFAULT media (ID 1) - Action blocked")
        flash('Cannot delete the default image.', 'danger')
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
        flash('File deleted successfully.', 'success')

    except IntegrityError:
        db.session.rollback()
        logger.warning(f"Delete failed: Media {media_id} is in use elsewhere (IntegrityError).")
        flash('Cannot delete this file because it is assigned to an Event. Please remove the association in the event first.', 'danger')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Critical error during media deletion ID {media_id}: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'danger')

    return redirect(url_for('media.get_all_media'))


@media_bp.route('/tags', methods=['GET', 'POST'])
@login_required
def manage_tags():
    form = TagForm()
    if form.validate_on_submit():
        new_tag = Tag(name=form.name.data)
        db.session.add(new_tag)
        db.session.commit()
        flash('Tag added!', 'success')
        return redirect(url_for('media.manage_tags'))
    
    tags = Tag.query.all()
    return render_template('media/tags.html', tags=tags, form=form)


@media_bp.route('/tags/delete/<int:tag_id>', methods=['POST'])
@admin_required
def delete_tag(tag_id):
    tag = Tag.query.get_or_404(tag_id)
    
    # 1. Protection against removal of system tags
    if tag.is_system:
        logger.warning(f"User {current_user.id} tried to delete system tag {tag.name}")
        flash('Cannot delete system tags.', 'danger')
        return redirect(url_for('media.manage_tags'))

    # 2. Download all media related to this tag
    associated_media = Media.query.filter_by(tag_id=tag.id).all()
    media_count = len(associated_media)
    
    try:
        for media in associated_media:
            # A. Reset devices that display removable media (set to default ID=1)
            devices_using_media = Device.query.filter_by(media_id=media.id).all()
            for device in devices_using_media:
                device.media_id = 1
            
            # B. Delete the physical file from the drive
            file_path = os.path.join(current_app.static_folder, 'uploads', media.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            else:
                logger.warning(f"Physical file missing during tag cleanup: {media.filename}")

            # C. Delete media entry from database
            db.session.delete(media)
        
        # 3. Finally, delete the tag itself.
        db.session.delete(tag)
        db.session.commit()
        
        logger.info(f"Tag '{tag.name}' deleted along with {media_count} files by User {current_user.id}")
        flash(f'Tag "{tag.name}" and {media_count} associated file(s) were deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting tag {tag.name}: {str(e)}")
        flash(f'An error occurred while deleting the tag: {str(e)}', 'danger')

    return redirect(url_for('media.manage_tags'))
