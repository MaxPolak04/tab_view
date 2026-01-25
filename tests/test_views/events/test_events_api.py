from datetime import datetime, timedelta, timezone
from tab_view.models import Device, Event


def test_get_events_returns_200(client):
    response = client.get('/api/v1/events/')

    assert response.status_code == 200


def test_get_events_returns_empty_list_when_no_events(client):
    response = client.get('/api/v1/events/')

    data = response.get_json()

    assert isinstance(data, list)
    assert data == []


def test_get_events_returns_event_data(client, database):
    device = Device(
        name='Tablet API',
        device_url='tablet-api'
    )

    now = datetime.now(timezone.utc)

    event = Event(
        start_time=now,
        end_time=now + timedelta(hours=1),
        device=device
    )

    database.session.add_all([device, event])
    database.session.commit()

    response = client.get('/api/v1/events/')
    data = response.get_json()

    assert len(data) == 1

    event_data = data[0]

    assert event_data['title'] == 'API Event'
    assert event_data['start'] == '2025-01-01T09:00:00'
    assert event_data['end'] == '2025-01-01T10:00:00'
    assert event_data['extendedProps']['device_id'] == device.id
