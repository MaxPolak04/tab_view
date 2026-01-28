from tab_view.models import Device, Media, Event, EventMedia
from datetime import datetime


def test_event_to_dict_returns_expected_keys(init_database):
    """
    Verifies that the to_dict method returns a dictionary with the correct structure and keys.
    Checks specifically for the presence of 'extendedProps' and the correct mapping of the device ID.
    """
    device = Device(
        name='N.100',
        device_url='n100'    
    )

    event = Event(
        title='Test Event',
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 11, 0),
        device=device
    )

    init_database.session.add_all([device, event])
    init_database.session.commit()

    data = event.to_dict()

    assert isinstance(data, dict)
    assert data['title'] == 'Test Event'
    assert data['extendedProps']['device_id'] == device.id


def test_event_dates_are_returned_as_iso_strings(init_database):
    """
    Tests that start_time and end_time datetime objects are correctly converted into ISO 8601 strings.
    This format is required for proper parsing by frontend calendar libraries (e.g., FullCalendar).
    """
    device = Device(
        name='N.100',
        device_url='n100'            
    )

    event = Event(
        title='ISO test',
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 11, 0),
        device=device
    )

    init_database.session.add_all([device, event])
    init_database.session.commit()

    data = event.to_dict()

    assert data['start'] == '2025-01-01T10:00:00'
    assert data['end'] == '2025-01-01T11:00:00'


def test_event_to_dict_returns_media_playlist(init_database):
    """
    Verifies that the to_dict method correctly serializes related Media objects.
    Ensures that the 'media_playlist' list contains nested dictionaries with Media details 
    and EventMedia specific fields (order, duration).
    """
    device = Device(
        name="N.100",
        device_url="n100"
    )

    media = Media(
        filename="image.jpg",
        media_type="image"
    )

    event = Event(
        title="Test event",
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 11, 0),
        device=device
    )

    event_media = EventMedia(
        event=event,
        media=media,
        order=1,
        duration=15
    )

    init_database.session.add_all([device, media, event, event_media])
    init_database.session.commit()

    data = event.to_dict()

    assert data["title"] == "Test event"
    assert data["extendedProps"]["device_id"] == device.id
    assert len(data["extendedProps"]["media_playlist"]) == 1

    playlist_item = data["extendedProps"]["media_playlist"][0]

    assert playlist_item["media_id"] == media.id
    assert playlist_item["filename"] == "image.jpg"
    assert playlist_item["media_type"] == "image"
    assert playlist_item["order"] == 1
    assert playlist_item["duration"] == 15
