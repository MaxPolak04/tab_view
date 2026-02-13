import pytest
from sqlalchemy.exc import IntegrityError

from tab_view.models import Media, Tag


def test_create_tag(init_database):
    """
    Verifies that a new Tag can be successfully created
    and saved to the database.
    Checks if the ID is assigned and the __repr__ method
    works as expected.
    """
    tag = Tag(name="Summer Vacation")
    init_database.session.add(tag)
    init_database.session.commit()

    assert tag.id is not None
    assert tag.name == "Summer Vacation"
    assert repr(tag) == "<Tag Summer Vacation>"


def test_tag_name_must_be_unique(init_database):
    """
    Verifies the unique constraint on the 'name' column.
    Attempting to create two tags with the same name should
    raise an IntegrityError.
    """
    tag1 = Tag(name="Duplicate Name")
    init_database.session.add(tag1)
    init_database.session.commit()

    tag2 = Tag(name="Duplicate Name")
    init_database.session.add(tag2)

    with pytest.raises(IntegrityError):
        init_database.session.commit()

    init_database.session.rollback()


def test_tag_defaults(init_database):
    """
    Verifies that default values are set correctly upon creation.
    Specifically checks that 'is_system' defaults to False.
    """
    tag = Tag(name="Standard Tag")
    init_database.session.add(tag)
    init_database.session.commit()

    assert tag.is_system is False


def test_tag_media_relationship(init_database):
    """
    Verifies the one-to-many relationship between Tag and Media.
    Ensures that media items assigned to a tag are accessible via
    the tag.media relationship.
    """
    tag = Tag(name="Nature")
    init_database.session.add(tag)
    init_database.session.commit()

    media1 = Media(filename="tree.jpg", media_type="image", tag_id=tag.id)
    media2 = Media(filename="river.mp4", media_type="video", tag_id=tag.id)

    init_database.session.add_all([media1, media2])
    init_database.session.commit()

    # Refresh the tag instance to load relationships
    init_database.session.refresh(tag)

    assert len(tag.media) == 2
    assert media1 in tag.media
    assert media2 in tag.media

    # Verify the backref relationship
    assert media1.tag.name == "Nature"
