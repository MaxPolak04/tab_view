import logging

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from tab_view import db
from tab_view.models import Device, Event, Media
from tab_view.utils import admin_required

from . import devices_bp
from .forms import DeleteDevice, NewDevice, UpdateDevice

logger = logging.getLogger(__name__)


@devices_bp.route("/", methods=["GET"])
@login_required
def get_all_devices():
    form = DeleteDevice()

    page = request.args.get("page", 1, type=int)
    # Get sort order from URL query parameters, default to ascending ('asc')
    sort_order = request.args.get("sort", "asc")
    per_page = 9

    # Determine the sorting column and direction
    if sort_order == "desc":
        order_clause = Device.name.desc()
    else:
        order_clause = Device.name.asc()

    # Apply the sorting clause to the query
    pagination = Device.query.order_by(order_clause).paginate(
        page=page, per_page=per_page
    )

    devices = pagination.items
    return render_template(
        "devices/devices.html",
        devices=devices,
        pagination=pagination,
        form=form,
        current_sort=sort_order,  # Pass current sort state to the template
    )


@devices_bp.route("/<device_url>")
def show_device(device_url):
    device = Device.query.filter_by(device_url=device_url).first_or_404()
    media = device.media

    events = Event.query.filter_by(device_id=device.id).all()

    schedule = []
    for event in events:
        playlist = [
            {
                "media_id": em.media_id,
                "filename": em.media.filename,
                "media_type": em.media.media_type,
                "order": em.order,
                "duration": em.duration,
            }
            for em in sorted(event.event_media, key=lambda x: x.order)
        ]

        schedule.append(
            {
                "id": event.id,
                "title": event.title,
                "start": event.start_time.isoformat(),
                "end": event.end_time.isoformat(),
                "media_playlist": playlist,
            }
        )

    return render_template(
        "devices/display.html", device=device, media=media, schedule=schedule
    )


@devices_bp.route("/new", methods=["GET", "POST"])
@admin_required
def create_device():
    media_list = Media.query.all()
    if not media_list:
        flash("No media available. Add a file before creating the device.", "warning")
        return redirect(url_for("media.new_media"))

    form = NewDevice()
    form.media_id.choices = [(media.id, media.filename) for media in media_list]

    if form.validate_on_submit():
        name = form.name.data
        device_url = form.device_url.data
        media_id = form.media_id.data

        try:
            new_device = Device(name=name, device_url=device_url, media_id=media_id)
            db.session.add(new_device)
            db.session.commit()

            logger.info(
                f"Device created: {new_device.name} (ID: {new_device.id}) "
                f"URL: {new_device.device_url} by User {current_user.id}"
            )

            flash("Device added successfully!", "success")
            return redirect(url_for("devices.get_all_devices"))
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error creating device '{name}': {str(e)} \
                    (User: {current_user.id})"
            )
            flash(f"Error creating device: {str(e)}", "danger")

    return render_template("devices/new-device.html", form=form)


@devices_bp.route("/update/<int:device_id>", methods=["GET", "POST"])
@login_required
def update_device(device_id):
    device = Device.query.get_or_404(device_id)
    media_list = Media.query.all()

    if not media_list:
        flash("No media available. Add a file before updating the device.", "warning")
        return redirect(url_for("media.new_media"))

    form = UpdateDevice(obj=device)
    form.device_id = device.id
    form.media_id.choices = [(media.id, media.filename) for media in media_list]

    if request.method == "GET":
        form.name.data = device.name
        form.device_url.data = device.device_url
        form.media_id.data = device.media_id

    if form.validate_on_submit():
        if not current_user.is_admin:
            logger.warning(
                f"Unauthorized device update attempt: Device ID {device.id} "
                f"by non-admin User {current_user.id}"
            )
            flash("Device settings can only be modified by administrators.", "warning")
            return render_template(
                "devices/update-device.html",
                form=form,
                device=device,
                media_list=media_list,
            )

        existing_name = Device.query.filter_by(name=form.name.data).first()
        if existing_name and existing_name.id != device.id:
            logger.warning(
                f"Update failed - duplicate name '{form.name.data}' "
                f"for Device ID {device.id} (User: {current_user.id})"
            )
            flash("This device name is already in use.", "danger")
            return redirect(url_for("devices.update_device", device_id=device.id))

        existing_url = Device.query.filter_by(device_url=form.device_url.data).first()
        if existing_url and existing_url.id != device.id:
            logger.warning(
                f"Update failed - duplicate URL '{form.device_url.data}' "
                f"for Device ID {device.id} (User: {current_user.id})"
            )
            flash("This URL is already assigned to another device.", "danger")
            return redirect(url_for("devices.update_device", device_id=device.id))

        try:
            old_name = device.name
            device.name = form.name.data
            device.device_url = form.device_url.data
            device.media_id = form.media_id.data

            db.session.commit()

            logger.info(
                f"Device updated: {old_name} -> {device.name} (ID: {device.id}) "
                f"by User {current_user.id}"
            )

            flash("Device updated successfully!", "success")
            return redirect(url_for("devices.get_all_devices"))

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error updating device ID {device.id}: {str(e)} \
                    (User: {current_user.id})"
            )
            flash(f"Error updating device: {str(e)}", "danger")

    return render_template(
        "devices/update-device.html",
        form=form,
        device=device,
        media_list=[
            {"id": m.id, "filename": m.filename, "media_type": m.media_type}
            for m in media_list
        ],
    )


@devices_bp.route("/delete/<int:device_id>", methods=["POST"])
@admin_required
def delete_device(device_id):
    logger.info(
        f"User {current_user.id} requesting \
                deletion of device ID {device_id}"
    )

    device = Device.query.get_or_404(device_id)
    device_name = device.name

    try:
        db.session.delete(device)
        db.session.commit()

        logger.info(
            f"Device deleted from DB: {device_name} (ID: {device_id}) "
            f"by User {current_user.id}"
        )

        flash("Device deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Critical error deleting device ID {device_id}: \
                {str(e)} (User: {current_user.id})"
        )
        flash(f"Error deleting device: {str(e)}", "danger")

    return redirect(url_for("devices.get_all_devices"))
