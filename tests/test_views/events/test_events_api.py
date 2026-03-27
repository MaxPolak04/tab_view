from datetime import datetime, timedelta

from tab_view.models import Device, Event, Media, Tag

# --- ACCESS CONTROL TESTS ---


def test_get_events_unauthorized_returns_401(client):
    """
    Ensure that accessing the API without logging in returns 401.
    """
    response = client.get("/api/v1/events/")
    assert response.status_code == 401


# --- GET REQUESTS TESTS ---


def test_get_events_returns_empty_list(auth_client):
    """
    Verify that an authenticated user gets an empty list if no events exist.
    Using 'auth_client' fixture ensures we are logged in.
    """
    response = auth_client.get("/api/v1/events/")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_events_returns_data(auth_client, init_database):
    """
    Verify that existing events are correctly returned in the response.
    """
    # 1. Setup Data
    device = Device(name="Tablet API", device_url="tablet-api")

    now = datetime.now()
    start_time = now.replace(day=1, hour=10, minute=0)
    end_time = start_time + timedelta(hours=1)

    event = Event(
        title="API Event", start_time=start_time, end_time=end_time, device=device
    )

    init_database.session.add_all([device, event])
    init_database.session.commit()

    # 2. Act
    response = auth_client.get("/api/v1/events/")
    data = response.get_json()

    # 3. Assert
    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["title"] == "API Event"
    assert data[0]["extendedProps"]["device_id"] == device.id
    # Checking ISO format roughly
    assert start_time.isoformat() in data[0]["start"]


# --- POST REQUESTS TESTS ---


def test_create_event_success(auth_client, init_database):
    """
    Test creating a valid event with a media playlist via POST.
    """
    # 1. Setup Dependencies
    tag = Tag(name="API Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    device = Device(name="Screen 1", device_url="url-1")
    media = Media(filename="ad.mp4", media_type="video", tag_id=tag.id)
    init_database.session.add_all([device, media])
    init_database.session.commit()

    # 2. Prepare Payload
    payload = {
        "title": "New Promo",
        "start_time": "2025-05-20T10:00:00",
        "end_time": "2025-05-20T12:00:00",
        "device_id": device.id,  # Testing the legacy fallback
        "media_playlist": [{"media_id": media.id, "order": 1, "duration": 30}],
    }

    # 3. Act
    response = auth_client.post("/api/v1/events/", json=payload)

    # 4. Assert
    assert response.status_code == 201
    data = response.get_json()
    # API now returns 'events' (plural) and message in plural due to device_ids support
    assert data["message"] == "Events created successfully"
    assert data["events"][0]["title"] == "New Promo"

    # Verify DB state
    saved_event = Event.query.filter_by(title="New Promo").first()
    assert saved_event is not None
    assert len(saved_event.event_media) == 1
    assert saved_event.event_media[0].duration == 30


def test_create_event_overlap_error(auth_client, init_database):
    """
    Test that the API rejects an event that overlaps with
    an existing one on the same device.
    """
    # 1. Setup: Create an existing event 10:00 - 11:00
    tag = Tag(name="Overlap Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    device = Device(name="Screen Overlap", device_url="url-ov")
    media = Media(filename="dummy.jpg", media_type="image", tag_id=tag.id)

    existing_event = Event(
        title="Existing",
        start_time=datetime(2025, 5, 20, 10, 0),
        end_time=datetime(2025, 5, 20, 11, 0),
        device=device,
    )
    init_database.session.add_all([device, media, existing_event])
    init_database.session.commit()

    # 2. Act: Try to create a new event 10:30 - 11:30 (Overlap!)
    payload = {
        "title": "Overlapping Event",
        "start_time": "2025-05-20T10:30:00",
        "end_time": "2025-05-20T11:30:00",
        "device_id": device.id,
        "media_playlist": [{"media_id": media.id}],
    }

    response = auth_client.post("/api/v1/events/", json=payload)

    # 3. Assert
    assert response.status_code == 409  # Conflict
    # API returns 'Schedule overlap...' so we check for 'overlap' instead of 'overlaps'
    assert "overlap" in response.get_json()["error"].lower()


def test_create_event_validation_error(auth_client):
    """
    Test missing required fields.
    """
    # Provide device_ids so we get past the first validation layer
    # and trigger the general required fields check.
    payload = {
        "device_ids": [1],
        "title": "Missing Data",
        # Missing start_time, end_time, media_playlist...
    }

    response = auth_client.post("/api/v1/events/", json=payload)

    assert response.status_code == 400
    assert "Missing required fields" in response.get_json()["error"]


# --- PUT REQUESTS TESTS ---


def test_update_event_success(auth_client, init_database):
    """
    Test successful update of an existing event via PUT.
    """
    # 1. Setup Dependencies
    device = Device(name="Screen PUT", device_url="url-put")
    init_database.session.add(device)
    init_database.session.commit()

    event = Event(
        title="Old Title",
        start_time=datetime(2025, 6, 1, 10, 0),
        end_time=datetime(2025, 6, 1, 12, 0),
        device_id=device.id,
    )
    init_database.session.add(event)
    init_database.session.commit()

    # 2. Payload for update
    payload = {
        "title": "Updated Title",
        "device_ids": [device.id],
        # Providing minimal payload to rely on API fallbacks
    }

    # 3. Act
    response = auth_client.put(f"/api/v1/events/{event.id}", json=payload)

    # 4. Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Group events updated successfully"
    assert data["events"][0]["title"] == "Updated Title"

    updated_event = Event.query.filter_by(title="Updated Title").first()
    assert updated_event is not None


# --- DELETE REQUESTS TESTS ---


def test_delete_event_success(auth_client, init_database):
    """
    Test successful deletion of an event (and its group).
    """
    # 1. Setup Dependencies
    device = Device(name="Screen DELETE", device_url="url-del")
    init_database.session.add(device)
    init_database.session.commit()

    event = Event(
        title="To Delete",
        start_time=datetime(2025, 7, 1, 10, 0),
        end_time=datetime(2025, 7, 1, 12, 0),
        device_id=device.id,
        group_id="test-group-id",
    )
    init_database.session.add(event)
    init_database.session.commit()

    # 2. Act
    response = auth_client.delete(f"/api/v1/events/{event.id}")

    # 3. Assert
    assert response.status_code == 200
    assert response.get_json()["message"] == "Event group deleted successfully"

    # Verify DB state
    assert Event.query.get(event.id) is None
