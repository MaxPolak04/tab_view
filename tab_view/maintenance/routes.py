import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import flash, render_template
from flask_login import current_user

from tab_view.models import Event, db
from tab_view.utils import admin_required

from . import maintenance_bp
from .forms import CleanupEventsForm

logger = logging.getLogger(__name__)


@maintenance_bp.route("/cleanup-events", methods=["GET", "POST"])
@admin_required
def cleanup_events_view():
    form = CleanupEventsForm()

    cutoff_date = None
    affected_count = None
    dry_run_result = False
    events_to_delete = []

    if form.validate_on_submit():
        now = datetime.now()

        # Get the first day of the current month at 00:00:00
        current_month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )

        # If user enters 1 (March), we want events before March 1st (all Feb and older).
        # We subtract (months - 1). For input=1,
        # we subtract 0 months -> cutoff is March 1.
        # For input=2, we subtract 1 month -> cutoff is Feb 1 (all Jan and older).
        cutoff_date = current_month_start - relativedelta(months=form.months.data - 1)

        query = Event.query.filter(Event.end_time < cutoff_date)
        affected_count = query.count()

        if form.dry_run.data:
            dry_run_result = True
            events_to_delete = query.order_by(Event.end_time.asc()).all()

            logger.info(
                f"Maintenance Dry Run by Admin {current_user.id}: "
                f"Found {affected_count} events older than {cutoff_date}."
            )

            flash(
                f"Preview: {affected_count} events would be deleted "
                f"(end_time < {cutoff_date.strftime('%Y-%m-%d %H:%M')}).",
                "info",
            )
        else:
            logger.info(
                f"Maintenance Cleanup STARTED by Admin {current_user.id}. "
                f"Target: events older than {cutoff_date}. Count: {affected_count}"
            )

            try:
                deleted_events = query.all()
                for event in deleted_events:
                    db.session.delete(event)

                db.session.commit()

                logger.info(
                    f"Maintenance Cleanup COMPLETED successfully by \
                        Admin {current_user.id}. "
                    f"Deleted {len(deleted_events)} events."
                )

                flash(
                    f"{len(deleted_events)} events deleted successfully "
                    f"(end_time < {cutoff_date.strftime('%Y-%m-%d %H:%M')}).",
                    "success",
                )
            except Exception as e:
                db.session.rollback()
                logger.error(
                    f"Error during maintenance cleanup: {str(e)} \
                        (Admin: {current_user.id})"
                )
                flash(f"An error occurred during cleanup: {str(e)}", "danger")

    return render_template(
        "admin/maintenance.html",
        form=form,
        cutoff_date=cutoff_date,
        affected_count=affected_count,
        dry_run_result=dry_run_result,
        events_to_delete=events_to_delete,
    )
