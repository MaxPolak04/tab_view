import io
import os
from unittest.mock import patch

from flask import url_for
from sqlalchemy.exc import IntegrityError

from tab_view.models import Device, Event, EventMedia, Media, Tag

# --- GET & ACCESS TESTS ---


def test_media_page_access(auth_client):
    """
    Test that logged-in user can see the media gallery.
    """
    response = auth_client.get(url_for("media.get_all_media"))
    assert response.status_code == 200
    assert b"Media" in response.data


def test_filter_media_by_tag(auth_client, init_database):
    """
    Test the filtering functionality on the main media page.
    """
    # 1. Setup Tags
    tag_holiday = Tag(name="Holiday")
    tag_work = Tag(name="Work")
    init_database.session.add_all([tag_holiday, tag_work])
    init_database.session.commit()

    # 2. Setup Media
    media_h = Media(filename="holiday.jpg", media_type="image", tag_id=tag_holiday.id)
    media_w = Media(filename="work.jpg", media_type="image", tag_id=tag_work.id)
    init_database.session.add_all([media_h, media_w])
    init_database.session.commit()

    # 3. Filter by Holiday
    response = auth_client.get(url_for("media.get_all_media", tag=tag_holiday.id))

    # Check that holiday media is present and work media is NOT
    assert b"holiday.jpg" in response.data
    assert b"work.jpg" not in response.data


# --- UPLOAD TESTS ---


def test_upload_media_with_existing_tag(auth_client, init_database, app):
    """
    Test uploading a file and selecting an existing tag.
    """
    # 1. Setup existing tag
    tag = Tag(name="General")
    init_database.session.add(tag)
    init_database.session.commit()

    # 2. Prepare Data
    data = {
        "file": (io.BytesIO(b"fake image content"), "test_image.jpg"),
        "tag_id": tag.id,  # Select existing tag
        "new_tag_name": "",  # No new tag
    }

    # 3. Upload
    response = auth_client.post(
        url_for("media.new_media"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    # 4. Assertions
    assert response.status_code == 200
    # Route flashes: "Successfully uploaded 1 file(s)!"
    assert b"Successfully uploaded 1 file(s)!" in response.data

    media = Media.query.filter_by(filename="test_image.jpg").first()
    assert media is not None
    assert media.tag_id == tag.id

    # Check physical file
    expected_path = os.path.join(app.static_folder, "uploads", "test_image.jpg")
    assert os.path.exists(expected_path)


def test_upload_media_creates_new_tag(auth_client, init_database, app):
    """
    Test uploading a file while creating a completely new tag.
    """
    # 1. Prepare Data (No existing tags needed)
    data = {
        "file": (io.BytesIO(b"content"), "new_tag_img.jpg"),
        "tag_id": 0,  # "--- Select Existing ---" (value 0)
        "new_tag_name": "Summer 2025",  # Input for new tag
    }

    # 2. Upload
    response = auth_client.post(
        url_for("media.new_media"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    # 3. Assertions
    assert response.status_code == 200
    assert b"Successfully uploaded 1 file(s)!" in response.data

    # Verify Tag was created
    new_tag = Tag.query.filter_by(name="Summer 2025").first()
    assert new_tag is not None

    # Verify Media is linked to new tag
    media = Media.query.filter_by(filename="new_tag_img.jpg").first()
    assert media.tag_id == new_tag.id


def test_upload_duplicate_filename(auth_client, init_database, app):
    """
    Test that uploading a file with an existing name shows an error and skips it.
    """
    # 1. Setup existing Tag and Media
    tag = Tag(name="Setup Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    filename = "duplicate.jpg"

    # Physical file
    file_path = os.path.join(app.static_folder, "uploads", filename)
    with open(file_path, "wb") as f:
        f.write(b"content")

    # DB entry
    media = Media(filename=filename, media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Try to upload same filename
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

    # 3. Assert - Route flashes skipping warning
    assert b"Skipped 1 file(s): duplicate.jpg (already exists)" in response.data
    assert Media.query.filter_by(filename=filename).count() == 1


# --- UPDATE / RENAME TESTS ---


def test_update_media_rename_and_change_tag(auth_client, init_database, app):
    """
    Test updating media: renaming the file AND changing the tag.
    """
    # 1. Setup
    old_tag = Tag(name="Old Tag")
    new_tag = Tag(name="New Tag")
    init_database.session.add_all([old_tag, new_tag])
    init_database.session.commit()

    original_name = "old_name.jpg"
    expected_full_name = "new_name.jpg"

    # Create physical file
    old_path = os.path.join(app.static_folder, "uploads", original_name)
    with open(old_path, "wb") as f:
        f.write(b"data")

    # Create DB entry
    media = Media(filename=original_name, media_type="image", tag_id=old_tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Act: Update via form
    response = auth_client.post(
        url_for("media.update_media", media_id=media.id),
        data={
            "filename": "new_name",  # New base name
            "tag_id": new_tag.id,  # Changing tag
        },
        follow_redirects=True,
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"Media updated successfully!" in response.data

    # Check DB
    init_database.session.refresh(media)
    assert media.filename == expected_full_name
    assert media.tag_id == new_tag.id

    # Check File System
    new_path = os.path.join(app.static_folder, "uploads", expected_full_name)
    assert os.path.exists(new_path)
    assert not os.path.exists(old_path)


# --- DELETE TESTS ---


def test_delete_media_success(auth_client, init_database, app):
    """
    Test deleting a media file.
    """
    # 1. Setup Tags
    tag = Tag(name="Delete Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    # 2. Setup Default Media (ID 1 protection)
    default_media = Media(filename="default.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(default_media)
    init_database.session.commit()

    # 3. Setup Media to delete
    filename = "to_delete.png"
    path = os.path.join(app.static_folder, "uploads", filename)

    with open(path, "wb") as f:
        f.write(b"data")

    media_to_delete = Media(filename=filename, media_type="image", tag_id=tag.id)
    init_database.session.add(media_to_delete)
    init_database.session.commit()

    assert media_to_delete.id != 1

    # 4. Act
    response = auth_client.post(
        url_for("media.delete_media", media_id=media_to_delete.id),
        follow_redirects=True,
    )

    # 5. Assert
    assert b"File deleted successfully" in response.data
    assert Media.query.get(media_to_delete.id) is None
    assert not os.path.exists(path)


def test_delete_default_media_blocked(auth_client, init_database):
    """
    Test that media with ID=1 cannot be deleted.
    """
    # 1. Setup Tag
    tag = Tag(name="System")
    init_database.session.add(tag)
    init_database.session.commit()

    # 2. Force create ID 1
    media = Media(id=1, filename="default.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # 3. Attempt delete
    response = auth_client.post(
        url_for("media.delete_media", media_id=1), follow_redirects=True
    )

    # 4. Assert
    assert b"Cannot delete the default image" in response.data
    assert Media.query.get(1) is not None


def test_delete_media_in_use_by_event(auth_client, init_database, app):
    """
    Test deleting media that is currently
    part of an Event playlist (IntegrityError).
    In SQLite, Foreign Key constraints are
    disabled by default, so we mock the IntegrityError
    to simulate a production database like PostgreSQL/MySQL.
    """
    import datetime

    # 1. Setup Tag, Media, Device, and Event
    tag = Tag(name="Event Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    # ID 1 must exist for the router logic safety fallback
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

    # Create dummy physical file
    path = os.path.join(app.static_folder, "uploads", "in_use.jpg")
    with open(path, "wb") as f:
        f.write(b"data")

    # 2. Act - mock the commit to raise IntegrityError as a real DB would
    with patch("tab_view.db.session.commit") as mock_commit:
        mock_commit.side_effect = IntegrityError(
            "Mocked constraint failure", params={}, orig=Exception("mock")
        )
        response = auth_client.post(
            url_for("media.delete_media", media_id=media.id),
            follow_redirects=True,
        )

    # 3. Assert
    assert (
        b"Cannot delete this file because it is assigned to an Event" in response.data
    )
    assert Media.query.get(media.id) is not None


# --- TAG MANAGEMENT TESTS ---


def test_manage_tags_page_and_create(auth_client, init_database):
    """
    Test accessing tags page and creating a new tag.
    """
    # Test GET
    response_get = auth_client.get(url_for("media.manage_tags"))
    assert response_get.status_code == 200

    # Test POST (Create)
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
    Test deleting a tag successfully using admin client.
    Should also delete associated media and physical files.
    """
    # 1. Setup Tag & Media
    tag = Tag(name="To Delete Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    # Mock default media (ID=1)
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

    # Link to a device to test fallback to ID=1
    device = Device(name="Screen 1", device_url="s1", media_id=media.id)
    init_database.session.add(device)
    init_database.session.commit()

    # Create physical file
    path = os.path.join(app.static_folder, "uploads", filename)
    with open(path, "wb") as f:
        f.write(b"data")

    # 2. Act
    response = admin_client.post(
        url_for("media.delete_tag", tag_id=tag.id),
        follow_redirects=True,
    )

    # 3. Assert
    # Szukamy fragmentów, aby ominąć problem białych znaków ze złamanej linii kodu
    assert b"associated file(s)" in response.data
    assert b"were deleted successfully" in response.data

    assert Tag.query.get(tag.id) is None
    assert Media.query.get(media.id) is None
    assert not os.path.exists(path)

    # Check that device fallback worked
    init_database.session.refresh(device)
    assert device.media_id == 1


def test_delete_system_tag_blocked(admin_client, init_database):
    """
    Test that system tags cannot be deleted.
    """
    tag = Tag(name="System UI", is_system=True)
    init_database.session.add(tag)
    init_database.session.commit()

    response = admin_client.post(
        url_for("media.delete_tag", tag_id=tag.id),
        follow_redirects=True,
    )

    assert b"Cannot delete system tags." in response.data
    assert Tag.query.get(tag.id) is not None
