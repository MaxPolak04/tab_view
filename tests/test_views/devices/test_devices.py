from flask import url_for
from tab_view.models import Device, Media, Tag

# --- PUBLIC ACCESS TESTS ---


def test_show_device_public_access(client, init_database):
    """
    Test that the device display page is accessible without login.
    """
    # 1. Setup: Create Tag first (Required for Media)
    tag = Tag(name="Display Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    # 2. Create Media linked to Tag
    media = Media(filename="bg.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # 3. Create Device linked to Media
    device = Device(name="Reception", device_url="reception-screen", media_id=media.id)
    init_database.session.add(device)
    init_database.session.commit()

    # 4. Act
    response = client.get(url_for("devices.show_device", device_url="reception-screen"))

    # 5. Assert
    assert response.status_code == 200
    assert b"Reception" in response.data


def test_show_device_404(client, init_database):
    """
    Test that accessing a non-existent device URL returns 404.
    """
    response = client.get(url_for("devices.show_device", device_url="ghost-screen"))
    assert response.status_code == 404


# --- PERMISSIONS TESTS (User vs Admin) ---


def test_create_device_forbidden_for_user(auth_client):
    """
    Verify that a regular user cannot access the create device page.
    Expecting 403 Forbidden (from @admin_required).
    """
    response = auth_client.get(url_for("devices.create_device"))
    assert response.status_code == 403


def test_delete_device_forbidden_for_user(auth_client, init_database):
    """
    Verify that a regular user cannot delete a device.
    """
    # Setup: Tag -> Media -> Device
    tag = Tag(name="User Test Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(filename="test.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    device = Device(name="Test", device_url="test", media_id=media.id)
    init_database.session.add(device)
    init_database.session.commit()

    # Attempt delete
    response = auth_client.post(url_for("devices.delete_device", device_id=device.id))

    assert response.status_code == 403
    # Verify it still exists
    assert Device.query.count() == 1


# --- ADMIN CRUD TESTS ---


def test_create_device_success(admin_client, init_database):
    """
    Test that an admin can successfully create a new device.
    """
    # 1. We need at least one media file with a Tag
    tag = Tag(name="Admin Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(filename="default.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Submit form data
    response = admin_client.post(
        url_for("devices.create_device"),
        data={"name": "Lobby TV", "device_url": "lobby-tv", "media_id": media.id},
        follow_redirects=True,
    )

    # 3. Assertions
    assert response.status_code == 200
    assert b"Device added successfully!" in response.data

    # Check DB
    device = Device.query.filter_by(name="Lobby TV").first()
    assert device is not None
    assert device.device_url == "lobby-tv"


def test_update_device_success(admin_client, init_database):
    """
    Test that an admin can update an existing device.
    """
    # 1. Setup
    tag = Tag(name="Update Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(filename="old.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    device = Device(name="Old Name", device_url="old-url", media_id=media.id)
    init_database.session.add(device)
    init_database.session.commit()

    # 2. Act: Change name and URL, keep same media
    response = admin_client.post(
        url_for("devices.update_device", device_id=device.id),
        data={"name": "New Name", "device_url": "new-url", "media_id": media.id},
        follow_redirects=True,
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"Device updated successfully!" in response.data

    # Verify DB update
    init_database.session.refresh(device)
    assert device.name == "New Name"
    assert device.device_url == "new-url"


def test_delete_device_success(admin_client, init_database):
    """
    Test that an admin can delete a device.
    """
    # 1. Setup
    tag = Tag(name="Delete Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(filename="del.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    device = Device(name="To Delete", device_url="del", media_id=media.id)
    init_database.session.add(device)
    init_database.session.commit()

    # 2. Act
    response = admin_client.post(
        url_for("devices.delete_device", device_id=device.id), follow_redirects=True
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"Device deleted successfully!" in response.data
    assert Device.query.count() == 0
