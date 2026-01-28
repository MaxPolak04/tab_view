import pytest
import os
import io
from flask import url_for
from tab_view.models import Media

# --- GET & ACCESS TESTS ---

def test_media_page_access(auth_client):
    """
    Test that logged-in user can see the media gallery.
    """
    response = auth_client.get(url_for('media.get_all_media'))
    assert response.status_code == 200
    assert b"Media" in response.data

# --- UPLOAD TESTS ---

def test_upload_media_success(auth_client, init_database, app):
    """
    Test uploading a valid image file.
    Checks DB record and physical file existence.
    """
    # 1. Simulate a file
    data = {
        'file': (io.BytesIO(b"fake image content"), 'test_image.jpg')
    }

    # 2. Upload
    response = auth_client.post(
        url_for('media.new_media'), 
        data=data, 
        content_type='multipart/form-data', # Crucial for file uploads!
        follow_redirects=True
    )

    # 3. Assert Response
    assert response.status_code == 200
    assert b"Media added successfully!" in response.data

    # 4. Assert Database
    media = Media.query.filter_by(filename='test_image.jpg').first()
    assert media is not None
    assert media.media_type == 'image'

    # 5. Assert Physical File
    # We check if the file actually landed in our temporary uploads folder
    expected_path = os.path.join(app.static_folder, 'uploads', 'test_image.jpg')
    assert os.path.exists(expected_path)


def test_upload_duplicate_filename(auth_client, init_database, app):
    """
    Test that uploading a file with an existing name shows an error.
    """
    # 1. Create existing file manually
    filename = 'duplicate.jpg'
    # Create physical file
    file_path = os.path.join(app.static_folder, 'uploads', filename)
    with open(file_path, 'wb') as f:
        f.write(b'content')
    
    # Create DB entry
    media = Media(filename=filename, media_type='image')
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Try to upload the same filename again
    data = {
        'file': (io.BytesIO(b"new content"), filename)
    }
    
    response = auth_client.post(
        url_for('media.new_media'), 
        data=data, 
        content_type='multipart/form-data',
        follow_redirects=True
    )

    # 3. Assert
    assert b"A file with this name already exists" in response.data
    # Ensure DB count is still 1, not 2
    assert Media.query.filter_by(filename=filename).count() == 1


# --- UPDATE / RENAME TESTS ---

def test_rename_media_success(auth_client, init_database, app):
    """
    Test renaming a media file.
    Should update DB and rename the physical file.
    """
    # 1. Setup
    original_name = 'old_name.jpg'
    new_name_base = 'new_name'
    expected_full_name = 'new_name.jpg'

    # Create physical file
    old_path = os.path.join(app.static_folder, 'uploads', original_name)
    with open(old_path, 'wb') as f:
        f.write(b'data')

    # Create DB entry
    media = Media(filename=original_name, media_type='image')
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Act: Rename via form
    response = auth_client.post(
        url_for('media.update_media', media_id=media.id),
        data={'filename': new_name_base}, # Form sends only the base name (no extension)
        follow_redirects=True
    )

    # 3. Assert
    assert response.status_code == 200
    assert b"Media updated successfully!" in response.data

    # Check DB
    init_database.session.refresh(media)
    assert media.filename == expected_full_name

    # Check File System
    new_path = os.path.join(app.static_folder, 'uploads', expected_full_name)
    assert os.path.exists(new_path)
    assert not os.path.exists(old_path) # Old file should be gone


# --- DELETE TESTS ---

def test_delete_media_success(auth_client, init_database, app):
    """
    Test deleting a media file.
    We must ensure the media to delete is NOT ID 1 (default media protected from deletion).
    """
    # 1. Setup: Create a dummy "Default" media to occupy ID 1
    default_media = Media(filename='default.jpg', media_type='image')
    init_database.session.add(default_media)
    init_database.session.commit()

    # 2. Setup: Create the ACTUAL file to delete (this will get ID 2)
    filename = 'to_delete.png'
    path = os.path.join(app.static_folder, 'uploads', filename)
    
    # Create the physical file
    with open(path, 'wb') as f:
        f.write(b'data')
    
    # Create the DB record
    media_to_delete = Media(filename=filename, media_type='image')
    init_database.session.add(media_to_delete)
    init_database.session.commit()

    # Verify that we are not testing on ID 1
    assert media_to_delete.id != 1

    # 3. Act
    response = auth_client.post(
        url_for('media.delete_media', media_id=media_to_delete.id),
        follow_redirects=True
    )

    # 4. Assert
    assert b"File deleted successfully" in response.data
    
    # Check that ID 2 is gone, but ID 1 remains
    assert Media.query.get(media_to_delete.id) is None
    assert Media.query.get(1) is not None
    
    # Check physical file is gone
    assert not os.path.exists(path)


def test_delete_default_media_blocked(auth_client, init_database):
    """
    Test that media with ID=1 cannot be deleted.
    """
    # 1. Force create ID 1 (Standard SQL allows forcing ID)
    media = Media(id=1, filename='default.jpg', media_type='image')
    init_database.session.add(media)
    init_database.session.commit()

    # 2. Attempt delete
    response = auth_client.post(
        url_for('media.delete_media', media_id=1),
        follow_redirects=True
    )

    # 3. Assert
    assert b"Cannot delete the default image" in response.data
    assert Media.query.get(1) is not None
