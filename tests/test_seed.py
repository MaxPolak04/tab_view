from unittest.mock import patch

from werkzeug.security import check_password_hash

from tab_view import db
from tab_view.models import Media, Tag, User
from tab_view.seed import seed_data


def test_seed_data_full_execution(init_database):
    """
    Test verifies that seed_data creates the required Admin user,
    the 'System' tag, and the default Media record.
    """
    with (
        patch("os.path.exists") as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("shutil.copy") as mock_copy,
    ):
        # Simulating that the source file (assets) exists,
        # but the destination file does not
        mock_exists.side_effect = lambda path: "assets" in path

        # We're launching the seeding phase
        seed_data()

        # 1. Admin Account Verification
        admin = User.query.filter_by(username="admin").first()
        assert admin is not None
        assert admin.is_admin is True
        assert check_password_hash(admin.password, "admin") is True

        # 2. Tag Verification
        tags = Tag.query.all()
        assert len(tags) == 1
        system_tag = tags[0]
        assert system_tag.name == "System"
        assert system_tag.is_system is True

        # 3. Verifying the default media file
        media = Media.query.get(1)
        assert media is not None
        assert media.filename == "default.png"
        assert media.media_type == "image"
        assert media.tag_id == system_tag.id

        # 4. Verifying file operations
        assert mock_makedirs.called
        assert mock_copy.called


def test_seed_data_is_idempotent(init_database):
    """
    Test verifies that running seed_data multiple times
    does not create duplicate records or raise IntegrityErrors.
    """
    with (
        patch("os.path.exists", return_value=True),
        patch("os.makedirs"),
        patch("shutil.copy"),
    ):
        seed_data()

        seed_data()

        assert User.query.count() == 1
        assert Tag.query.count() == 1
        assert Media.query.count() == 1


def test_seed_data_updates_existing_system_tag(init_database):
    """
    Test verifies that if a tag named 'System' already exists but
    is not marked as system (is_system=False), the seed function
    will update it to is_system=True.
    """
    existing_tag = Tag(name="System", is_system=False)
    db.session.add(existing_tag)
    db.session.commit()

    with patch("os.path.exists", return_value=True):
        seed_data()

    updated_tag = Tag.query.filter_by(name="System").first()
    assert updated_tag is not None
    assert updated_tag.is_system is True


def test_seed_data_missing_source_image(init_database):
    """
    Test verifies that if the source image is missing from assets,
    the application handles it gracefully without copying.
    """
    with (
        patch("os.path.exists", return_value=False),
        patch("os.makedirs") as mock_makedirs,
        patch("shutil.copy") as mock_copy,
    ):
        seed_data()

        assert not mock_copy.called
        assert mock_makedirs.called
        assert Media.query.get(1) is not None
