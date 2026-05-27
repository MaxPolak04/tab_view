import io
import os
from unittest.mock import patch

from flask import url_for
from sqlalchemy.exc import IntegrityError

from tab_view.models import Device, Event, EventMedia, Media, Tag

# --- GET & ACCESS TESTS ---


def test_media_page_access(auth_client):
    """
    Verifies that a logged-in user can access the main media gallery.
    """
    response = auth_client.get(url_for("media.get_all_media"))
    assert response.status_code == 200
    assert b"Media" in response.data


def test_filter_media_by_tag(auth_client, init_database):
    """
    Verifies the filtering functionality on the main media page using tag IDs.
    """
    tag_holiday = Tag(name="Holiday")
    tag_work = Tag(name="Work")
    init_database.session.add_all([tag_holiday, tag_work])
    init_database.session.commit()

    media_h = Media(filename="holiday.jpg", media_type="image", tag_id=tag_holiday.id)
    media_w = Media(filename="work.jpg", media_type="image", tag_id=tag_work.id)
    init_database.session.add_all([media_h, media_w])
    init_database.session.commit()

    response = auth_client.get(url_for("media.get_all_media", tag=tag_holiday.id))

    # Ensure only the selected tag's media is displayed
    assert b"holiday.jpg" in response.data
    assert b"work.jpg" not in response.data


# --- UPLOAD TESTS ---


def test_upload_media_with_existing_tag(auth_client, init_database, app):
    """
    Verifies uploading a file while assigning it to a pre-existing tag.
    """
    tag = Tag(name="General")
    init_database.session.add(tag)
    init_database.session.commit()

    data = {
        "file": (io.BytesIO(b"fake image content"), "test_image.jpg"),
        "tag_id": tag.id,
        "new_tag_name": "",
    }

    response = auth_client.post(
        url_for("media.new_media"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Successfully uploaded 1 file(s)!" in response.data

    media = Media.query.filter_by(filename="test_image.jpg").first()
    assert media is not None
    assert media.tag_id == tag.id

    expected_path = os.path.join(app.static_folder, "uploads", "test_image.jpg")
    assert os.path.exists(expected_path)


def test_upload_media_creates_new_tag(auth_client, init_database, app):
    """
    Verifies uploading a file while dynamically creating a new tag.
    """
    data = {
        "file": (io.BytesIO(b"content"), "new_tag_img.jpg"),
        "tag_id": 0,
        "new_tag_name": "Summer 2025",
    }

    response = auth_client.post(
        url_for("media.new_media"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Successfully uploaded 1 file(s)!" in response.data

    new_tag = Tag.query.filter_by(name="Summer 2025").first()
    assert new_tag is not None

    media = Media.query.filter_by(filename="new_tag_img.jpg").first()
    assert media.tag_id == new_tag.id


def test_upload_duplicate_filename(auth_client, init_database, app):
    """
    Verifies that attempting to upload a file with an already existing filename
    skips the file and warns the user without raising server errors.
    """
    tag = Tag(name="Setup Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    filename = "duplicate.jpg"
    file_path = os.path.join(app.static_folder, "uploads", filename)
    with open(file_path, "wb") as f:
        f.write(b"content")

    media = Media(filename=filename, media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    data = {
        "file": (io.BytesIO(b"new content"), filename),
        "tag_id": tag.id,
        "new_tag_name": "",
    }

    response = auth_client.post(
        url_for("media.new_media"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert b"Skipped 1 file(s): duplicate.jpg (already exists)" in response.data
    assert Media.query.filter_by(filename=filename).count() == 1


# --- UPDATE / RENAME TESTS ---


def test_update_media_rename_and_change_tag(auth_client, init_database, app):
    """
    Verifies updating standard media properties: renaming the physical file
    and changing the associated tag.
    Includes the creation of a mock default media (ID=1) to prevent
    the system security block from rejecting the test update.
    """
    # 1. Setup default media to occupy ID 1 (System Protection)
    system_tag = Tag(name="System", is_system=True)
    init_database.session.add(system_tag)
    init_database.session.commit()

    default_media = Media(
        id=1, filename="default.png", media_type="image", tag_id=system_tag.id
    )
    init_database.session.add(default_media)
    init_database.session.commit()

    # 2. Setup standard test tags
    old_tag = Tag(name="Old Tag")
    new_tag = Tag(name="New Tag")
    init_database.session.add_all([old_tag, new_tag])
    init_database.session.commit()

    original_name = "old_name.jpg"
    expected_full_name = "new_name.jpg"

    # Create physical file for testing
    old_path = os.path.join(app.static_folder, "uploads", original_name)
    with open(old_path, "wb") as f:
        f.write(b"data")

    # This media will safely receive an ID > 1
    media = Media(filename=original_name, media_type="image", tag_id=old_tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # Double check to ensure we are not testing against the protected ID
    assert media.id != 1

    # 3. Act: Submit the update form
    response = auth_client.post(
        url_for("media.update_media", media_id=media.id),
        data={
            "filename": "new_name",
            "tag_id": new_tag.id,
        },
        follow_redirects=True,
    )

    # 4. Assertions
    assert response.status_code == 200
    assert b"Media updated successfully!" in response.data

    init_database.session.refresh(media)
    assert media.filename == expected_full_name
    assert media.tag_id == new_tag.id

    new_path = os.path.join(app.static_folder, "uploads", expected_full_name)
    assert os.path.exists(new_path)
    assert not os.path.exists(old_path)


def test_update_system_media_blocked(auth_client, init_database):
    """
    Verifies that the update view completely blocks access if the requested
    media ID is 1 (the protected default system image).
    """
    tag = Tag(name="System", is_system=True)
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(id=1, filename="default.png", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # Attempt to access the GET route for updating ID 1
    response = auth_client.get(
        url_for("media.update_media", media_id=1), follow_redirects=True
    )

    assert b"System security: You cannot edit the default system file." in response.data


# --- DELETE TESTS ---


def test_delete_media_success(auth_client, init_database, app):
    """
    Verifies that standard media can be successfully deleted, including
    its physical file representation.
    """
    tag = Tag(name="Delete Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    default_media = Media(filename="default.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(default_media)
    init_database.session.commit()

    filename = "to_delete.png"
    path = os.path.join(app.static_folder, "uploads", filename)
    with open(path, "wb") as f:
        f.write(b"data")

    media_to_delete = Media(filename=filename, media_type="image", tag_id=tag.id)
    init_database.session.add(media_to_delete)
    init_database.session.commit()

    response = auth_client.post(
        url_for("media.delete_media", media_id=media_to_delete.id),
        follow_redirects=True,
    )

    assert b"File deleted successfully" in response.data
    assert Media.query.get(media_to_delete.id) is None
    assert not os.path.exists(path)


def test_delete_default_media_blocked(auth_client, init_database):
    """
    Verifies that the system explicitly prevents deletion of media ID 1.
    """
    tag = Tag(name="System")
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(id=1, filename="default.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    response = auth_client.post(
        url_for("media.delete_media", media_id=1), follow_redirects=True
    )

    assert b"Cannot delete the default image" in response.data
    assert Media.query.get(1) is not None


def test_delete_media_in_use_by_event(auth_client, init_database, app):
    """
    Verifies the IntegrityError catch block when attempting to delete media
    that is actively referenced by an event playlist.
    """
    import datetime

    tag = Tag(name="Event Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    default_m = Media(filename="default.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(default_m)
    init_database.session.commit()

    media = Media(filename="in_use.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    device = Device(name="Test Screen", device_url="test-screen")
    init_database.session.add(device)
    init_database.session.commit()

    event = Event(
        title="Test Event",
        start_time=datetime.datetime.now(),
        end_time=datetime.datetime.now(),
        device_id=device.id,
    )
    init_database.session.add(event)
    init_database.session.commit()

    event_media = EventMedia(event_id=event.id, media_id=media.id, order=1)
    init_database.session.add(event_media)
    init_database.session.commit()

    path = os.path.join(app.static_folder, "uploads", "in_use.jpg")
    with open(path, "wb") as f:
        f.write(b"data")

    with patch("tab_view.db.session.commit") as mock_commit:
        mock_commit.side_effect = IntegrityError(
            "Mocked constraint failure", params={}, orig=Exception("mock")
        )
        response = auth_client.post(
            url_for("media.delete_media", media_id=media.id),
            follow_redirects=True,
        )

    assert (
        b"Cannot delete this file because it is assigned to the following Event(s):"
        in response.data
    )
    assert Media.query.get(media.id) is not None


# --- TAG MANAGEMENT TESTS ---


def test_manage_tags_page_and_create(auth_client, init_database):
    """
    Verifies the functionality of creating a new tag from the tag management view.
    """
    response_get = auth_client.get(url_for("media.manage_tags"))
    assert response_get.status_code == 200

    response_post = auth_client.post(
        url_for("media.manage_tags"),
        data={"name": "Winter Campaign"},
        follow_redirects=True,
    )

    assert response_post.status_code == 200
    assert b"Tag added!" in response_post.data
    assert Tag.query.filter_by(name="Winter Campaign").first() is not None


def test_delete_tag_success(admin_client, init_database, app):
    """
    Verifies the cascading deletion of a standard tag, ensuring associated
    media files are removed and devices fall back to the default media.
    """
    tag = Tag(name="To Delete Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    default_tag = Tag(name="System", is_system=True)
    init_database.session.add(default_tag)
    init_database.session.commit()

    default_media = Media(
        id=1, filename="def.jpg", media_type="image", tag_id=default_tag.id
    )
    init_database.session.add(default_media)
    init_database.session.commit()

    filename = "tag_del.jpg"
    media = Media(filename=filename, media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    device = Device(name="Screen 1", device_url="s1", media_id=media.id)
    init_database.session.add(device)
    init_database.session.commit()

    path = os.path.join(app.static_folder, "uploads", filename)
    with open(path, "wb") as f:
        f.write(b"data")

    response = admin_client.post(
        url_for("media.delete_tag", tag_id=tag.id),
        follow_redirects=True,
    )

    assert b"associated file(s)" in response.data
    assert b"were deleted successfully" in response.data

    assert Tag.query.get(tag.id) is None
    assert Media.query.get(media.id) is None
    assert not os.path.exists(path)

    init_database.session.refresh(device)
    assert device.media_id == 1


def test_delete_system_tag_blocked(admin_client, init_database):
    """
    Verifies that system-level tags are protected from deletion.
    """

    tag = Tag(name="System UI", is_system=True)
    init_database.session.add(tag)
    init_database.session.commit()

    response = admin_client.post(
        url_for("media.delete_tag", tag_id=tag.id),
        follow_redirects=True,
    )

    assert b"You cannot delete a system tag." in response.data
    assert Tag.query.get(tag.id) is not None
