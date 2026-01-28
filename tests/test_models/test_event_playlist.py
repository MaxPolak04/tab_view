from datetime import datetime
from tab_view.models import Device, Media, Event, EventMedia


def test_event_to_dict_returns_sorted_media_playlist(init_database):
    """
    Verifies that the media playlist returned by to_dict is sorted by the 'order' field ascending.
    
    This ensures that even if media items are added to the database out of sequence,
    the API returns them in the correct playback order defined by the 'order' column.
    """
    device = Device(
        name='N.200',
        device_url='n200'
    )

    media1 = Media(filename='video.mp4', media_type='video')
    media2 = Media(filename='image.jpg', media_type='image')

    event = Event(
        title='Playlist Test',
        start_time=datetime(2025, 1, 1, 8, 0),
        end_time=datetime(2025, 1, 1, 9, 0),
        device=device
    )

    em2 = EventMedia(
        event=event,
        media=media2,
        order=2,
        duration=5
    )

    em1 = EventMedia(
        event=event,
        media=media1,
        order=1,
        duration=10
    )

    init_database.session.add_all([device, media1, media2, event, em1, em2])
    init_database.session.commit()

    data = event.to_dict()
    playlist = data['extendedProps']['media_playlist']

    assert len(playlist) == 2

    assert playlist[0]['filename'] == 'video.mp4'
    assert playlist[0]['order'] == 1
    assert playlist[0]['duration'] == 10

    assert playlist[1]['filename'] == 'image.jpg'
    assert playlist[1]['order'] == 2
    assert playlist[1]['duration'] == 5
