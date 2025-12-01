from flask import render_template, flash
from . import maintenance_bp
from tab_view.models import Event, db
from tab_view.utils import admin_required
from .forms import CleanupEventsForm
from dateutil.relativedelta import relativedelta
from datetime import datetime


@maintenance_bp.route('/cleanup-events', methods=['GET', 'POST'])
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
            years=form.years.data, 
            months=form.months.data
        )
        
        query = Event.query.filter(Event.end_time < cutoff_date)
        affected_count = query.count()

        if form.dry_run.data:
            dry_run_result = True
            events_to_delete = query.order_by(Event.end_time.asc()).all()

            flash(
                f'Preview: {affected_count} events would be deleted (end_time < {cutoff_date}).',
                'info'
            )
        else:
            deleted_events = query.all()
            for event in deleted_events:
                db.session.delete(event)
            db.session.commit()
            flash(
                f'{len(deleted_events)} events deleted successfully (end_time < {cutoff_date}).',
                'success'
            )

    return render_template(
        'admin/maintenance.html',
        form=form,
        cutoff_date=cutoff_date,
        affected_count=affected_count,
        dry_run_result=dry_run_result,
        events_to_delete=events_to_delete
    )
