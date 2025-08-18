from . import devices_bp
from tab_view import db
from tab_view.models import Device, Media
from .forms import NewDevice
from flask import request, render_template, flash, redirect, url_for
from flask_login import login_required


@devices_bp.route('/', methods=['GET'])
@login_required
def get_all_devices():
    # pagination
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
    device = Media.query.filter_by(device_url=f'devices/{device_url}').first_or_404()
    media = device.media
    return render_template('devices/display.html', media=media)


@devices_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_device():
    form = NewDevice()
    form.media_id.choices = [(media.id, media.filename) for media in Media.query.all()]

    if form.validate_on_submit():
        name = form.name.data
        device_url = form.device_url.data
        media_id = form.media.data

        new_device = Device(name=name, device_url=device_url, media_id=media_id)
        db.session.add(new_device)
        db.session.commit()
        flash('Device added successfully!', 'success')
        return redirect(url_for('devices.get_all_devices'))
    return render_template('new-device.html', form=form)


@devices_bp.route('/update/<device_url>', methods=['GET', 'POST'])
def update_device(device_url):
    pass


@devices_bp.route('/delete/<device_url>')
def delete_device(device_url):
    pass
