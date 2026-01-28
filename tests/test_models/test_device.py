import pytest
from sqlalchemy.exc import IntegrityError
from tab_view.models import Device, Media


def test_create_device(init_database):
    """
    Test successful creation of a Device.
    Verifies that ID is assigned and defaults are set.
    """
    device = Device(
        name="N.100",
        device_url="n100"
    )

    init_database.session.add(device)
    init_database.session.commit()

    assert device.id is not None
    assert device.name == "N.100"
    
    init_database.session.refresh(device)
    assert device.uploaded_at is not None


def test_device_unique_name(init_database):
    """
    Test that the 'name' column enforces unique constraint.
    """
    device1 = Device(name="N.100", device_url="n100")
    init_database.session.add(device1)
    init_database.session.commit()

    device2 = Device(name="N.100", device_url="n200")
    init_database.session.add(device2)

    with pytest.raises(IntegrityError):
        init_database.session.commit()
    
    init_database.session.rollback()


def test_device_unique_url(init_database):
    """
    Test that the 'device_url' column enforces unique constraint.
    """
    device1 = Device(name="N.100", device_url="n100")
    init_database.session.add(device1)
    init_database.session.commit()

    device2 = Device(name="N.200", device_url="n100")
    init_database.session.add(device2)

    with pytest.raises(IntegrityError):
        init_database.session.commit()
    
    init_database.session.rollback()


def test_device_media_relationship(init_database):
    """
    Test the relationship between Device and Media.
    """
    media = Media(filename="promo.mp4", media_type="video")
    init_database.session.add(media)
    init_database.session.flush() 

    device = Device(
        name="N.100",
        device_url="n100",
        media=media
    )
    init_database.session.add(device)
    init_database.session.commit()

    saved_device = Device.query.filter_by(name="N.100").first()
    
    assert saved_device.media_id == media.id
    assert saved_device.media.filename == "promo.mp4"
    