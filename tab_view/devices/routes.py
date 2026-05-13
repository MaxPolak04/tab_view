import logging
import os
from datetime import datetime

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from tab_view import db
from tab_view.models import Device, Event, Media, Tag
from tab_view.utils import admin_required, log_audit_action
from tab_view.weather import WeatherService

from . import devices_bp
from .forms import DeleteDevice, NewDevice, UpdateDevice

logger = logging.getLogger(__name__)


@devices_bp.route("/", methods=["GET"])
@login_required
def get_all_devices():
    form = DeleteDevice()

    page = request.args.get("page", 1, type=int)
    sort_order = request.args.get("sort", "asc")
    per_page = 12

    if sort_order == "desc":
        order_clause = Device.name.desc()
    else:
        order_clause = Device.name.asc()

    pagination = Device.query.order_by(order_clause).paginate(
        page=page, per_page=per_page
    )

    devices = pagination.items
    return render_template(
        "devices/devices.html",
        devices=devices,
        pagination=pagination,
        form=form,
        current_sort=sort_order,
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
        "devices/display.html",
        device=device,
        media=media,
        schedule=schedule,
        show_clock=device.show_clock,
    )


@devices_bp.route("/api/<device_url>/current_state")
def api_device_state(device_url):
    device = Device.query.filter_by(device_url=device_url).first_or_404()
    now = datetime.now()

    weather_data = WeatherService.get_weather()

    def get_cache_buster(filename):
        try:
            filepath = os.path.join(
                current_app.root_path, "static", "uploads", filename
            )
            return int(os.path.getmtime(filepath))
        except Exception:
            return int(now.timestamp())

    active_event = Event.query.filter(
        Event.device_id == device.id, Event.start_time <= now, Event.end_time > now
    ).first()

    show_weather = active_event.show_weather if active_event else device.show_weather

    if active_event:
        playlist = [
            {
                "media_id": em.media_id,
                "filename": em.media.filename,
                "media_type": em.media.media_type,
                "order": em.order,
                "duration": em.duration,
                "cache_buster": get_cache_buster(em.media.filename),
            }
            for em in sorted(active_event.event_media, key=lambda x: x.order)
        ]
        return jsonify(
            {
                "status": "event",
                "event_id": active_event.id,
                "event_title": active_event.title,
                "playlist": playlist,
                "show_clock": active_event.show_clock,
                "show_weather": show_weather,
                "weather": weather_data,
            }
        )

    default_media_data = None
    if device.media:
        default_media_data = {
            "filename": device.media.filename,
            "media_type": device.media.media_type,
            "cache_buster": get_cache_buster(device.media.filename),
        }

    return jsonify(
        {
            "status": "default",
            "event_id": None,
            "default_media": default_media_data,
            "show_clock": device.show_clock,
            "show_weather": show_weather,
            "weather": weather_data,
        }
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
        show_clock = form.show_clock.data
        show_weather = form.show_weather.data

        try:
            new_device = Device(
                name=name,
                device_url=device_url,
                media_id=media_id,
                show_clock=show_clock,
                show_weather=show_weather,
            )
            db.session.add(new_device)
            db.session.commit()

            logger.info(
                f"Device created: {new_device.name} (ID: {new_device.id}) "
                f"URL: {new_device.device_url} by User {current_user.id}"
            )

            log_audit_action(
                "CREATE",
                "Device",
                f"Created new device '{new_device.name}' "
                f"(URL: {new_device.device_url}).",
            )

            flash("Device added successfully!", "success")
            return redirect(url_for("devices.get_all_devices"))
        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error creating device '{name}': {str(e)} (User: {current_user.id})"
            )
            flash(f"Error creating device: {str(e)}", "danger")

    return render_template("devices/new-device.html", form=form)


@devices_bp.route("/update/<int:device_id>", methods=["GET", "POST"])
@admin_required
def update_device(device_id):
    if not current_user.is_admin:
        flash("Device settings can only be modified by administrators.", "warning")
        return redirect(url_for("devices.get_all_devices"))

    device = Device.query.get_or_404(device_id)
    tags = Tag.query.all()
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
        form.show_clock.data = device.show_clock
        form.show_weather.data = device.show_weather

    if form.validate_on_submit():
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
            changes = []

            # Check exact changes before applying them
            if device.name != form.name.data:
                changes.append(f"Name changed to '{form.name.data}'")
            if device.device_url != form.device_url.data:
                changes.append(f"URL changed to '{form.device_url.data}'")
            if device.media_id != form.media_id.data:
                new_media = Media.query.get(form.media_id.data)
                new_media_name = (
                    new_media.filename if new_media else str(form.media_id.data)
                )
                changes.append(f"Default Media changed to '{new_media_name}'")
            if device.show_clock != form.show_clock.data:
                changes.append(f"Show Clock changed to {form.show_clock.data}")
            if device.show_weather != form.show_weather.data:
                changes.append(f"Show Weather changed to {form.show_weather.data}")

            # Apply changes
            device.name = form.name.data
            device.device_url = form.device_url.data
            device.media_id = form.media_id.data
            device.show_clock = form.show_clock.data
            device.show_weather = form.show_weather.data

            db.session.commit()

            # Only log if something was actually modified
            if changes:
                changes_str = ", ".join(changes)
                logger.info(
                    f"Device updated: {old_name} (ID: {device.id}) "
                    f"Changes: {changes_str} by User {current_user.id}"
                )
                log_audit_action(
                    "UPDATE",
                    "Device",
                    f"Updated device '{old_name}'. Changes: {changes_str}.",
                )
            else:
                logger.info(
                    f"Device update submitted for '{old_name}' (ID: {device.id}), "
                    f"but no values were changed by User {current_user.id}."
                )

            flash("Device updated successfully!", "success")
            return redirect(url_for("devices.get_all_devices"))

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Error updating device ID {device.id}: {str(e)} "
                f"(User: {current_user.id})"
            )
            flash(f"Error updating device: {str(e)}", "danger")

    return render_template(
        "devices/update-device.html",
        form=form,
        device=device,
        tags=tags,
        media_list=[
            {
                "id": m.id,
                "filename": m.filename,
                "media_type": m.media_type,
                "tag_id": m.tag_id,
            }
            for m in media_list
        ],
    )


@devices_bp.route("/schedule/<int:device_id>", methods=["GET"])
@login_required
def device_schedule(device_id):
    device = Device.query.get_or_404(device_id)

    # Filter out System tags and media for the event schedule picker
    tags = Tag.query.filter_by(is_system=False).all()
    media_list = Media.query.join(Tag).filter(~Tag.is_system).all()

    return render_template(
        "devices/device-schedule.html",
        device=device,
        tags=tags,
        media_list=[
            {
                "id": m.id,
                "filename": m.filename,
                "media_type": m.media_type,
                "tag_id": m.tag_id,
            }
            for m in media_list
        ],
    )


@devices_bp.route("/delete/<int:device_id>", methods=["POST"])
@admin_required
def delete_device(device_id):
    logger.info(f"User {current_user.id} requesting deletion of device ID {device_id}")

    device = Device.query.get_or_404(device_id)
    device_name = device.name

    try:
        db.session.delete(device)
        db.session.commit()

        logger.info(
            f"Device deleted from DB: {device_name} (ID: {device_id}) "
            f"by User {current_user.id}"
        )

        log_audit_action(
            "DELETE", "Device", f"Permanently deleted device '{device_name}'."
        )

        flash("Device deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Critical error deleting device ID {device_id}: "
            f"{str(e)} (User: {current_user.id})"
        )
        flash(f"Error deleting device: {str(e)}", "danger")

    return redirect(url_for("devices.get_all_devices"))
