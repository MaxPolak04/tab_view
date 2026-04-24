import io
import json
import logging
import os
import shutil
import zipfile
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import current_app, flash, redirect, render_template, send_file, url_for
from flask_login import current_user

from tab_view.models import (
    AuditLog,
    Device,
    Event,
    EventMedia,
    Media,
    Tag,
    User,
    db,
)
from tab_view.utils import admin_required, log_audit_action

from . import settings_bp
from .forms import CleanupEventsForm, DefaultImageForm, ExportDataForm, ImportDataForm

logger = logging.getLogger(__name__)


def _render_settings_view(
    cleanup_form=None,
    default_image_form=None,
    export_form=None,
    import_form=None,
    cutoff_date=None,
    affected_count=None,
    dry_run_result=False,
    events_to_delete=None,
):
    """Helper function to load data and render the settings view cleanly."""
    cleanup_form = cleanup_form or CleanupEventsForm()
    default_image_form = default_image_form or DefaultImageForm()
    export_form = export_form or ExportDataForm()
    import_form = import_form or ImportDataForm()

    # Cache buster to force browser to load new default.png
    default_media = Media.query.get(1)
    timestamp = (
        default_media.uploaded_at.timestamp()
        if default_media and default_media.uploaded_at
        else 0
    )

    # Grab the current server time for the NTP clock display
    server_time = datetime.now()

    return render_template(
        "admin/settings.html",
        cleanup_form=cleanup_form,
        default_image_form=default_image_form,
        export_form=export_form,
        import_form=import_form,
        default_timestamp=timestamp,
        server_time=server_time,
        cutoff_date=cutoff_date,
        affected_count=affected_count,
        dry_run_result=dry_run_result,
        events_to_delete=events_to_delete or [],
    )


@settings_bp.route("/", methods=["GET"])
@admin_required
def settings_view():
    return _render_settings_view()


@settings_bp.route("/update-default-image", methods=["POST"])
@admin_required
def update_default_image():
    form = DefaultImageForm()
    if form.validate_on_submit():
        file = form.file.data

        # Always overwrite exactly as 'default.png'
        file_path = os.path.join(current_app.static_folder, "uploads", "default.png")

        try:
            file.save(file_path)
            default_media = Media.query.get(1)
            if default_media:
                default_media.uploaded_at = db.func.now()
                db.session.commit()

            logger.info(f"Default image replaced by Admin {current_user.id}")

            # --- AUDIT LOG ---
            log_audit_action("UPDATE", "Settings", "Replaced the default system image.")

            flash("Default image has been successfully replaced.", "success")
            return redirect(url_for("settings.settings_view"))
        except Exception as e:
            logger.error(f"Error updating default image: {str(e)}")
            flash(f"Failed to update default image: {str(e)}", "danger")
            return redirect(url_for("settings.settings_view"))
    return _render_settings_view(default_image_form=form)


@settings_bp.route("/cleanup-events", methods=["POST"])
@admin_required
def cleanup_events_view():
    form = CleanupEventsForm()

    cutoff_date = None
    affected_count = None
    dry_run_result = False
    events_to_delete = []

    if form.validate_on_submit():
        now = datetime.now()
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        cutoff_date = current_month_start - relativedelta(months=form.months.data - 1)

        query = Event.query.filter(Event.end_time < cutoff_date)
        affected_count = query.count()

        if form.dry_run.data:
            dry_run_result = True
            events_to_delete = query.order_by(Event.end_time.asc()).all()
            logger.info(
                f"Maintenance Dry Run by Admin {current_user.id}: "
                f"Found {affected_count} events."
            )
            flash(f"Preview: {affected_count} events would be deleted.", "info")
        else:
            try:
                deleted_events = query.all()
                for event in deleted_events:
                    db.session.delete(event)
                db.session.commit()

                logger.info(
                    f"Maintenance Cleanup COMPLETED by Admin {current_user.id}. "
                    f"Deleted {len(deleted_events)}."
                )

                # --- AUDIT LOG ---
                log_audit_action(
                    "DELETE",
                    "System",
                    f"Performed automated maintenance cleanup. \
                        Permanently deleted {len(deleted_events)} old events.",
                )

                flash(f"{len(deleted_events)} events deleted successfully.", "success")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error during maintenance cleanup: {str(e)}")
                flash(f"An error occurred during cleanup: {str(e)}", "danger")

    return _render_settings_view(
        cleanup_form=form,
        cutoff_date=cutoff_date,
        affected_count=affected_count,
        dry_run_result=dry_run_result,
        events_to_delete=events_to_delete,
    )


@settings_bp.route("/export-data", methods=["POST"])
@admin_required
def export_data():
    form = ExportDataForm()
    if form.validate_on_submit():
        memory_file = io.BytesIO()

        # Create ZIP archive in memory
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            # Export Database to JSON
            if form.export_db.data:
                db_data = {
                    "tags": [
                        {"id": t.id, "name": t.name, "is_system": t.is_system}
                        for t in Tag.query.all()
                    ],
                    "users": [
                        {
                            "id": u.id,
                            "username": u.username,
                            "password": u.password,
                            "created_at": u.created_at.isoformat()
                            if u.created_at
                            else None,
                            "last_login_at": u.last_login_at.isoformat()
                            if u.last_login_at
                            else None,
                            "is_admin": u.is_admin,
                        }
                        for u in User.query.all()
                    ],
                    "media": [
                        {
                            "id": m.id,
                            "filename": m.filename,
                            "media_type": m.media_type,
                            "uploaded_at": m.uploaded_at.isoformat()
                            if m.uploaded_at
                            else None,
                            "tag_id": m.tag_id,
                        }
                        for m in Media.query.all()
                    ],
                    "devices": [
                        {
                            "id": d.id,
                            "name": d.name,
                            "device_url": d.device_url,
                            "uploaded_at": d.uploaded_at.isoformat()
                            if d.uploaded_at
                            else None,
                            "media_id": d.media_id,
                            "show_clock": d.show_clock,
                        }
                        for d in Device.query.all()
                    ],
                    "events": [
                        {
                            "id": e.id,
                            "group_id": e.group_id,
                            "title": e.title,
                            "start_time": e.start_time.isoformat()
                            if e.start_time
                            else None,
                            "end_time": e.end_time.isoformat() if e.end_time else None,
                            "color": e.color,
                            "created_at": e.created_at.isoformat()
                            if e.created_at
                            else None,
                            "updated_at": e.updated_at.isoformat()
                            if e.updated_at
                            else None,
                            "device_id": e.device_id,
                            "show_clock": e.show_clock,
                        }
                        for e in Event.query.all()
                    ],
                    "event_media": [
                        {
                            "id": em.id,
                            "event_id": em.event_id,
                            "media_id": em.media_id,
                            "order": em.order,
                            "duration": em.duration,
                        }
                        for em in EventMedia.query.all()
                    ],
                    "audit_logs": [
                        {
                            "id": a.id,
                            "timestamp": a.timestamp.isoformat()
                            if a.timestamp
                            else None,
                            "user_id": a.user_id,
                            "action": a.action,
                            "entity_type": a.entity_type,
                            "details": a.details,
                            "ip_address": a.ip_address,
                        }
                        for a in AuditLog.query.all()
                    ],
                }
                zf.writestr("db_dump.json", json.dumps(db_data))

            # Export Media Files
            if form.export_media.data:
                uploads_dir = os.path.join(current_app.static_folder, "uploads")
                for root, _, files in os.walk(uploads_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # We store them in the zip under "uploads/" directory
                        zf.write(file_path, arcname=os.path.join("uploads", file))

        memory_file.seek(0)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        log_audit_action("EXPORT", "System", "Performed system data export.")
        return send_file(
            memory_file,
            download_name=f"tabview_export_{timestamp_str}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    flash("Export failed due to form errors.", "danger")
    return redirect(url_for("settings.settings_view"))


@settings_bp.route("/import-data", methods=["POST"])
@admin_required
def import_data():
    form = ImportDataForm()
    if form.validate_on_submit():
        file = form.file.data

        try:
            with zipfile.ZipFile(file, "r") as zf:
                # 1. Restore DB if json exists in the archive
                if "db_dump.json" in zf.namelist():
                    with zf.open("db_dump.json") as f:
                        data = json.load(f)

                    # To prevent FK violations, we must
                    # delete in exact reverse dependency order
                    db.session.query(AuditLog).delete()
                    db.session.query(EventMedia).delete()
                    db.session.query(Event).delete()
                    db.session.query(Device).delete()
                    db.session.query(Media).delete()
                    db.session.query(User).delete()
                    db.session.query(Tag).delete()
                    db.session.commit()

                    def parse_dt(dt_str):
                        return datetime.fromisoformat(dt_str) if dt_str else None

                    # Insert in dependency order
                    for item in data.get("tags", []):
                        db.session.add(Tag(**item))
                    db.session.commit()

                    for item in data.get("users", []):
                        item["created_at"] = parse_dt(item.get("created_at"))
                        item["last_login_at"] = parse_dt(item.get("last_login_at"))
                        db.session.add(User(**item))
                    db.session.commit()

                    for item in data.get("media", []):
                        item["uploaded_at"] = parse_dt(item.get("uploaded_at"))
                        db.session.add(Media(**item))
                    db.session.commit()

                    for item in data.get("devices", []):
                        item["uploaded_at"] = parse_dt(item.get("uploaded_at"))
                        db.session.add(Device(**item))
                    db.session.commit()

                    for item in data.get("events", []):
                        item["start_time"] = parse_dt(item.get("start_time"))
                        item["end_time"] = parse_dt(item.get("end_time"))
                        item["created_at"] = parse_dt(item.get("created_at"))
                        item["updated_at"] = parse_dt(item.get("updated_at"))
                        db.session.add(Event(**item))
                    db.session.commit()

                    for item in data.get("event_media", []):
                        db.session.add(EventMedia(**item))
                    db.session.commit()

                    for item in data.get("audit_logs", []):
                        item["timestamp"] = parse_dt(item.get("timestamp"))
                        db.session.add(AuditLog(**item))
                    db.session.commit()

                # 2. Extract media files if they exist
                uploads_dir = os.path.join(current_app.static_folder, "uploads")
                for member in zf.namelist():
                    if member.startswith("uploads/") and member != "uploads/":
                        filename = os.path.basename(member)
                        target_path = os.path.join(uploads_dir, filename)
                        with (
                            zf.open(member) as source,
                            open(target_path, "wb") as target,
                        ):
                            shutil.copyfileobj(source, target)

            log_audit_action("IMPORT", "System", "Restored system data from archive.")
            flash("System data has been successfully imported and restored.", "success")

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during data import: {str(e)}")
            flash(f"An error occurred during import: {str(e)}", "danger")

    return redirect(url_for("settings.settings_view"))
