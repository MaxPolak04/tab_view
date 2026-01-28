import pytest
from flask import url_for
from tab_view.models import Device, Media

# --- PUBLIC ACCESS TESTS ---

def test_show_device_public_access(client, init_database):
    """
    Test that the device display page is accessible without login.
    """
    # 1. Setup: Device needs Media
    media = Media(filename="bg.jpg", media_type="image")
    device = Device(name="Reception", device_url="reception-screen", media=media)
    
    init_database.session.add_all([media, device])
    init_database.session.commit()

    # 2. Act
    response = client.get(url_for('devices.show_device', device_url='reception-screen'))

    # 3. Assert
    assert response.status_code == 200
    assert b"Reception" in response.data

def test_show_device_404(client, init_database):
    """
    Test that accessing a non-existent device URL returns 404.
    """
    response = client.get(url_for('devices.show_device', device_url='ghost-screen'))
    assert response.status_code == 404


# --- PERMISSIONS TESTS (User vs Admin) ---

def test_create_device_forbidden_for_user(auth_client):
    """
    Verify that a regular user cannot access the create device page.
    Expecting 403 Forbidden (from @admin_required).
    """
    response = auth_client.get(url_for('devices.create_device'))
    assert response.status_code == 403

def test_delete_device_forbidden_for_user(auth_client, init_database):
    """
    Verify that a regular user cannot delete a device.
    """
    # Setup device
    media = Media(filename="test.jpg")
    device = Device(name="Test", device_url="test", media=media)
    init_database.session.add_all([media, device])
    init_database.session.commit()

    # Attempt delete
    response = auth_client.post(url_for('devices.delete_device', device_id=device.id))
    
    assert response.status_code == 403
    # Verify it still exists
    assert Device.query.count() == 1


# --- ADMIN CRUD TESTS ---

def test_create_device_success(admin_client, init_database):
    """
    Test that an admin can successfully create a new device.
    """
    # 1. We need at least one media file, otherwise controller redirects to new_media
    media = Media(filename="default.jpg", media_type="image")
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Submit form data
    response = admin_client.post(url_for('devices.create_device'), data={
        'name': 'Lobby TV',
        'device_url': 'lobby-tv',
        'media_id': media.id
    }, follow_redirects=True)

    # 3. Assertions
    assert response.status_code == 200
    assert b"Device added successfully!" in response.data
    
    # Check DB
    device = Device.query.filter_by(name='Lobby TV').first()
    assert device is not None
    assert device.device_url == 'lobby-tv'

def test_update_device_success(admin_client, init_database):
    """
    Test that an admin can update an existing device.
    """
    # 1. Setup
    media = Media(filename="old.jpg")
    device = Device(name="Old Name", device_url="old-url", media=media)
    init_database.session.add_all([media, device])
    init_database.session.commit()

    # 2. Act: Change name and URL
    response = admin_client.post(url_for('devices.update_device', device_id=device.id), data={
        'name': 'New Name',
        'device_url': 'new-url',
        'media_id': media.id
    }, follow_redirects=True)

    # 3. Assert
    assert response.status_code == 200
    assert b"Device updated successfully!" in response.data
    
    # Verify DB update
    init_database.session.refresh(device)
    assert device.name == 'New Name'
    assert device.device_url == 'new-url'

def test_delete_device_success(admin_client, init_database):
    """
    Test that an admin can delete a device.
    """
    # 1. Setup
    media = Media(filename="del.jpg")
    device = Device(name="To Delete", device_url="del", media=media)
    init_database.session.add_all([media, device])
    init_database.session.commit()

    # 2. Act
    response = admin_client.post(
        url_for('devices.delete_device', device_id=device.id), 
        follow_redirects=True
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"Device deleted successfully!" in response.data
    assert Device.query.count() == 0
