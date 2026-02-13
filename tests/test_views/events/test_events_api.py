from datetime import datetime, timedelta

from tab_view.models import Device, Event, Media, Tag  # Added Tag import

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
    # Create Tag first (Required for Media)
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
        "device_id": device.id,
        "media_playlist": [{"media_id": media.id, "order": 1, "duration": 30}],
    }

    # 3. Act
    response = auth_client.post("/api/v1/events/", json=payload)

    # 4. Assert
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Event created successfully"
    assert data["event"]["title"] == "New Promo"

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
    # Create Tag first
    tag = Tag(name="Overlap Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    device = Device(name="Screen Overlap", device_url="url-ov")
    # Use Media for playlist requirement
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
    assert "overlaps" in response.get_json()["error"]


def test_create_event_validation_error(auth_client):
    """
    Test missing required fields.
    """
    payload = {
        "title": "Missing Data"
        # Missing start_time, end_time, device_id...
    }

    response = auth_client.post("/api/v1/events/", json=payload)

    assert response.status_code == 400
    assert "Missing required fields" in response.get_json()["error"]
