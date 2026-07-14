import logging
from datetime import datetime, timedelta

from tab_view import db, scheduler
from tab_view.models import AuditLog

logger = logging.getLogger(__name__)


def cleanup_old_audit_logs():
    """
    Deletes audit logs older than 90 days.
    Intended to be run as a scheduled background job.
    Uses application context to interact with the database.
    """
    with scheduler.app.app_context():
        try:
            # cutoff_date = datetime.now() - timedelta(days=90)
            cutoff_date = datetime.now() - timedelta(days=1)

            old_logs_query = AuditLog.query.filter(AuditLog.timestamp < cutoff_date)
            logs_count = old_logs_query.count()

            if logs_count > 0:
                old_logs_query.delete(synchronize_session=False)
                db.session.commit()
                logger.info(
                    f"Automated maintenance: Deleted {logs_count} audit "
                    f"logs older than 90 days."
                )
            else:
                logger.info(
                    "Automated maintenance: No audit logs older than 90 days found."
                )

        except Exception as e:
            db.session.rollback()
            logger.error(
                f"Automated maintenance failed while cleaning up audit logs: {str(e)}"
            )


def setup_scheduled_tasks(scheduler_instance):
    """
    Registers all background jobs and starts the scheduler.
    """
    # Run the cleanup job every day at 03:00 AM
    scheduler_instance.add_job(
        id="cleanup_audit_logs",
        func=cleanup_old_audit_logs,
        trigger="cron",
        hour=3,
        minute=0,
    )

    if not scheduler_instance.running:
        scheduler_instance.start()
