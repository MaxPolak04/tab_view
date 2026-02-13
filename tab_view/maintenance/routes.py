import logging
from flask import render_template, flash
from flask_login import current_user
from . import maintenance_bp
from tab_view.models import Event, db
from tab_view.utils import admin_required
from .forms import CleanupEventsForm
from dateutil.relativedelta import relativedelta
from datetime import datetime


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
        cutoff_date = now - relativedelta(
            years=form.years.data, months=form.months.data
        )

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
                f"Preview: {affected_count} events would be deleted (end_time < {cutoff_date}).",
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
                    f"Maintenance Cleanup COMPLETED successfully by Admin {current_user.id}. "
                    f"Deleted {len(deleted_events)} events."
                )

                flash(
                    f"{len(deleted_events)} events deleted successfully (end_time < {cutoff_date}).",
                    "success",
                )
            except Exception as e:
                db.session.rollback()
                logger.error(
                    f"Error during maintenance cleanup: {str(e)} (Admin: {current_user.id})"
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
