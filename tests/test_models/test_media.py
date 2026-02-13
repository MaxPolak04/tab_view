import pytest
from sqlalchemy.exc import IntegrityError
from tab_view.models import Media, Tag


def test_create_media(init_database):
    """
    Verifies that a Media object can be successfully created and saved.
    Checks if the ID and uploaded_at timestamp are generated automatically.
    """
    # Media requires a Tag due to the foreign key constraint
    tag = Tag(name="Test Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    media = Media(filename="test_image.jpg", media_type="image", tag_id=tag.id)
    init_database.session.add(media)
    init_database.session.commit()

    assert media.id is not None
    assert media.filename == "test_image.jpg"
    assert media.media_type == "image"
    assert media.uploaded_at is not None
    assert repr(media) == "<Media test_image.jpg>"


def test_media_requires_tag(init_database):
    """
    Verifies that creating a Media object without a tag_id raises an IntegrityError.
    The database schema defines tag_id as nullable=False.
    """
    media = Media(filename="orphan_file.jpg", media_type="image")
    init_database.session.add(media)

    with pytest.raises(IntegrityError):
        init_database.session.commit()

    init_database.session.rollback()


def test_media_requires_filename(init_database):
    """
    Verifies that the filename field is mandatory.
    Attempting to save Media without a filename should raise an IntegrityError.
    """
    tag = Tag(name="Another Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    # Create media without filename
    media = Media(media_type="image", tag_id=tag.id)
    init_database.session.add(media)

    with pytest.raises(IntegrityError):
        init_database.session.commit()

    init_database.session.rollback()


def test_media_tag_relationship_access(init_database):
    """
    Verifies that the relationship between Media and Tag works correctly.
    Ensures that we can access the Tag object directly from the Media instance.
    """
    tag = Tag(name="Relationship Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    # Assigning the tag object directly instead of tag_id
    media = Media(filename="linked_file.mp4", media_type="video", tag=tag)
    init_database.session.add(media)
    init_database.session.commit()

    # Refresh to ensure data is loaded from DB
    init_database.session.refresh(media)

    assert media.tag is not None
    assert media.tag.name == "Relationship Tag"
    assert media.tag.id == tag.id
