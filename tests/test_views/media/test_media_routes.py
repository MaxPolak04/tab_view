import io
import os

from flask import url_for

from tab_view.models import Media, Tag

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
    assert b"Media added successfully!" in response.data

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
    assert b"Media added successfully!" in response.data

    # Verify Tag was created
    new_tag = Tag.query.filter_by(name="Summer 2025").first()
    assert new_tag is not None

    # Verify Media is linked to new tag
    media = Media.query.filter_by(filename="new_tag_img.jpg").first()
    assert media.tag_id == new_tag.id


def test_upload_duplicate_filename(auth_client, init_database, app):
    """
    Test that uploading a file with an existing name shows an error.
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

    # 3. Assert
    assert b"A file with this name already exists" in response.data
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
    # Note: We must ensure ID 1 exists to test logic correctly,
    # though here we strictly delete ID != 1
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
