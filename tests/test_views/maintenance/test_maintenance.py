from datetime import datetime

from dateutil.relativedelta import relativedelta
from flask import url_for

from tab_view.models import Device, Event

# --- ACCESS TEST ---


def test_cleanup_page_forbidden_for_non_admin(auth_client):
    """
    Verify that regular users cannot access maintenance tools.
    """
    response = auth_client.get(url_for("maintenance.cleanup_events_view"))
    assert response.status_code == 403


# --- LOGIC TESTS ---


def test_cleanup_dry_run_does_not_delete(admin_client, init_database):
    """
    Test 'Dry Run' mode. It should find old events but NOT delete them.
    """
    # 1. Setup Data
    device = Device(name="Maintenance Screen", device_url="maint-url")

    # Create an 'OLD' event (2 years ago)
    old_date = datetime.now() - relativedelta(years=2)
    old_event = Event(
        title="Old Event",
        start_time=old_date,
        end_time=old_date + relativedelta(hours=1),
        device=device,
    )

    init_database.session.add_all([device, old_event])
    init_database.session.commit()

    # 2. Act: Submit form with dry_run=True (simulate checkbox checked)
    # Route calculates cutoff as:
    # current_month_start - relativedelta(months=form.months.data - 1)
    # To simulate 1 year (12 months) cutoff, we must pass 13 (13 - 1 = 12 months ago).
    response = admin_client.post(
        url_for("maintenance.cleanup_events_view"),
        data={"months": 13, "dry_run": "y"},
        follow_redirects=True,
    )

    # 3. Assert
    assert response.status_code == 200
    # Check flash message for "Preview"
    assert b"Preview:" in response.data

    # CRITICAL: Verify the event still exists!
    assert Event.query.count() == 1


def test_cleanup_execute_deletes_old_events(admin_client, init_database):
    """
    Test actual execution. Should delete old events and keep new ones.
    """
    # 1. Setup Data
    device = Device(name="Cleanup Screen", device_url="clean-url")

    # Event A: 2 years old (Should be deleted)
    date_old = datetime.now() - relativedelta(years=2)
    event_old = Event(
        title="To Delete", start_time=date_old, end_time=date_old, device=device
    )

    # Event B: 1 month old (Should stay)
    date_new = datetime.now() - relativedelta(months=1)
    event_new = Event(
        title="To Keep", start_time=date_new, end_time=date_new, device=device
    )

    init_database.session.add_all([device, event_old, event_new])
    init_database.session.commit()

    # 2. Act: Submit form WITHOUT dry_run (simulate checkbox unchecked)
    # To set cutoff at 1 year ago, we pass months=13
    response = admin_client.post(
        url_for("maintenance.cleanup_events_view"),
        data={
            "months": 13,
        },
        follow_redirects=True,
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"events deleted successfully" in response.data

    # CRITICAL: Check DB state
    # Old event should be gone
    assert Event.query.filter_by(title="To Delete").first() is None
    # New event should remain
    assert Event.query.filter_by(title="To Keep").first() is not None
