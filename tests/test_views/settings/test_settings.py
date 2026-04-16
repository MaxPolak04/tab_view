import io
from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from flask import url_for

from tab_view.models import Device, Event


def test_settings_endpoints_forbidden_for_non_admin(auth_client):
    """
    Verifies that a standard user cannot access or trigger any settings endpoints.
    Ensures administrative routes are protected against unauthorized access.
    """
    endpoints = [
        ("GET", url_for("settings.settings_view")),
        ("POST", url_for("settings.cleanup_events_view")),
        ("POST", url_for("settings.update_default_image")),
    ]

    for method, url in endpoints:
        if method == "GET":
            response = auth_client.get(url)
        else:
            response = auth_client.post(url, data={})

        assert response.status_code == 403


def test_settings_view_loads_for_admin(admin_client):
    """
    Verifies that the settings dashboard renders correctly for an administrator.
    Checks for the exact HTML strings used in the updated UI.
    """
    response = admin_client.get(url_for("settings.settings_view"))

    assert response.status_code == 200
    assert b"Upload replacement image" in response.data
    assert b"Cleanup Old Events" in response.data


def test_cleanup_dry_run_does_not_delete(admin_client, init_database):
    """
    Verifies the dry-run execution of the event cleanup tool.
    It ensures that old events are identified but retained in the database.
    """
    device = Device(name="Maintenance Screen", device_url="maint-url")

    old_date = datetime.now() - relativedelta(years=2)
    old_event = Event(
        title="Old Event",
        start_time=old_date,
        end_time=old_date + relativedelta(hours=1),
        device=device,
    )

    init_database.session.add_all([device, old_event])
    init_database.session.commit()

    # Pass 13 months to simulate a 1-year cutoff (13 - 1 = 12 months ago)
    response = admin_client.post(
        url_for("settings.cleanup_events_view"),
        data={"months": 13, "dry_run": "y"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Preview:" in response.data
    assert Event.query.count() == 1


def test_cleanup_execute_deletes_old_events(admin_client, init_database):
    """
    Verifies the actual execution of the event cleanup tool.
    Ensures that events older than the threshold are permanently deleted,
    while newer events are preserved.
    """
    device = Device(name="Cleanup Screen", device_url="clean-url")

    date_old = datetime.now() - relativedelta(years=2)
    event_old = Event(
        title="To Delete", start_time=date_old, end_time=date_old, device=device
    )

    date_new = datetime.now() - relativedelta(months=1)
    event_new = Event(
        title="To Keep", start_time=date_new, end_time=date_new, device=device
    )

    init_database.session.add_all([device, event_old, event_new])
    init_database.session.commit()

    # Omit the 'dry_run' field to execute the deletion
    response = admin_client.post(
        url_for("settings.cleanup_events_view"),
        data={"months": 13},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"events deleted successfully" in response.data
    assert Event.query.filter_by(title="To Delete").first() is None
    assert Event.query.filter_by(title="To Keep").first() is not None


@patch("werkzeug.datastructures.FileStorage.save")
def test_update_default_image_success(mock_save, admin_client, init_database):
    """
    Verifies that an admin can upload a valid image to replace the default system media.
    Uses patching to prevent actual file system writes during the test.
    """
    data = {"file": (io.BytesIO(b"dummy image data"), "new_default.png")}

    response = admin_client.post(
        url_for("settings.update_default_image"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Default image has been successfully replaced." in response.data
    assert mock_save.called


def test_update_default_image_rejects_invalid_file_type(admin_client):
    """
    Verifies that the form validation properly rejects non-image files
    based on the allowed extensions (jpg, png, gif) and displays the WTForms error.
    """
    data = {"file": (io.BytesIO(b"dummy text data"), "malicious_script.txt")}

    response = admin_client.post(
        url_for("settings.update_default_image"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Images only" in response.data
