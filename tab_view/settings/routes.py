import logging
import os
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import current_app, flash, redirect, render_template, url_for
from flask_login import current_user

from tab_view.models import Event, Media, db
from tab_view.utils import admin_required

from . import settings_bp
from .forms import CleanupEventsForm, DefaultImageForm

logger = logging.getLogger(__name__)


def _render_settings_view(
    cleanup_form=None,
    default_image_form=None,
    cutoff_date=None,
    affected_count=None,
    dry_run_result=False,
    events_to_delete=None,
):
    """Helper function to load data and render the settings view cleanly."""
    cleanup_form = cleanup_form or CleanupEventsForm()
    default_image_form = default_image_form or DefaultImageForm()

    # Cache buster to force browser to load new default.png
    default_media = Media.query.get(1)
    timestamp = (
        default_media.uploaded_at.timestamp()
        if default_media and default_media.uploaded_at
        else 0
    )

    return render_template(
        "admin/settings.html",
        cleanup_form=cleanup_form,
        default_image_form=default_image_form,
        default_timestamp=timestamp,
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

            # Update timestamp in DB so cache buster works on frontend
            default_media = Media.query.get(1)
            if default_media:
                default_media.uploaded_at = db.func.now()
                db.session.commit()

            logger.info(f"Default image replaced by Admin {current_user.id}")
            flash("Default image has been successfully replaced.", "success")
        except Exception as e:
            logger.error(f"Error updating default image: {str(e)}")
            flash(f"Failed to update default image: {str(e)}", "danger")

    return redirect(url_for("settings.settings_view"))


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
