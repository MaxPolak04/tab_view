from . import devices_bp
from tab_view import db
from tab_view.models import Device, Media
from .forms import NewDevice, UpdateDevice
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_required


@devices_bp.route('/', methods=['GET'])
@login_required
def get_all_devices():

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = Device.query \
        .order_by(Device.id) \
        .paginate(page=page, per_page=per_page)
    
    devices = pagination.items
    return render_template('devices.html',
                           devices=devices,
                           pagination=pagination)


@devices_bp.route('/<device_url>')
def show_device(device_url):
    device = Device.query.filter_by(device_url=device_url).first_or_404()
    media = device.media
    return render_template('devices/display.html', media=media)


@devices_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_device():
    media_list = Media.query.all()
    if not media_list:
        flash("No media available. Add a file before creating the device.", "warning")
        return redirect(url_for('media.new_media'))

    form = NewDevice()
    form.media_id.choices = [(media.id, media.filename) for media in media_list]

    if form.validate_on_submit():
        name = form.name.data
        device_url = form.device_url.data
        media_id = form.media_id.data

        new_device = Device(name=name, device_url=device_url, media_id=media_id)
        db.session.add(new_device)
        db.session.commit()
        flash('Device added successfully!', 'success')
        return redirect(url_for('devices.get_all_devices'))
    return render_template('new-device.html', form=form)


@devices_bp.route('/update/<device_id>', methods=['GET', 'POST'])
@login_required
def update_device(device_id):
    device = Device.query.get_or_404(device_id)

    media_list = Media.query.all()
    if not media_list:
        flash("No media available. Add a file before creating the device.", "warning")
        return redirect(url_for('media.new_media'))
    
    form = UpdateDevice()
    form.media_id.choices = [(media.id, media.filename) for media in media_list]

    if form.validate_on_submit():

        existing_name = Device.query.filter_by(name=form.name.data).first()
        if existing_name and existing_name.id != device.id:
            flash('This device name is already in use.', 'danger')
            return redirect(url_for('devices.update_device', device_id=device.id))

        existing_url = Device.query.filter_by(device_url=form.device_url.data).first()
        if existing_url and existing_url.id != device.id:
            flash('This URL is already assigned to another device.', 'danger')
            return redirect(url_for('devices.update_device', device_id=device.id))

        device.name = form.name.data
        device.device_url = form.device_url.data
        device.media_id = form.media_id.data

        db.session.commit()
        flash('Device updated successfully!', 'success')
        return redirect(url_for('devices.get_all_devices'))
    return render_template('update-device.html', form=form, device=device)


@devices_bp.route('/delete/<device_url>', methods=['POST'])
@login_required
def delete_device(device_url):
    device = Device.query.get_or_404(device_url)
    db.session.delete(device)
    db.session.commit()
    flash('Device deleted successfully!', 'success')
    return redirect(url_for('device.get_all_devices'))
