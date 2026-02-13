from unittest.mock import patch
from tab_view.seed import seed_data
from tab_view.models import Media, Tag


def test_seed_data_full_execution(init_database):
    """
    Test verifies that seed_data creates required system tags ('Other', 'eNStudios', 'System')
    and creates the default Media record assigned to the 'System' tag.

    It uses mocking to avoid actual file system operations during tests.
    """
    with (
        patch("os.path.exists") as mock_exists,
        patch("os.makedirs") as mock_makedirs,
        patch("shutil.copy") as mock_copy,
    ):
        # Simulate that the source asset file exists so copying can proceed
        # The lambda function returns True if checking for 'assets', otherwise False (initially)
        mock_exists.side_effect = lambda path: "assets" in path

        # Execute the seed function
        seed_data()

        # 1. Verify Tags creation
        tags = Tag.query.all()
        tag_names = [t.name for t in tags]

        assert "Other" in tag_names
        assert "eNStudios" in tag_names
        assert "System" in tag_names
        assert len(tags) == 3

        # 2. Verify Default Media creation
        media = Media.query.get(1)
        system_tag = Tag.query.filter_by(name="System").first()

        assert media is not None
        assert media.filename == "default.png"
        assert media.media_type == "image"
        # Ensure the media is correctly linked to the System tag
        assert media.tag_id == system_tag.id

        # 3. Verify File Operations were attempted
        assert mock_makedirs.called
        assert mock_copy.called


def test_seed_data_is_idempotent(init_database):
    """
    Test verifies that running seed_data multiple times does not create duplicate records
    or raise IntegrityErrors.
    """
    with (
        patch("os.path.exists", return_value=True),
        patch("os.makedirs"),
        patch("shutil.copy"),
    ):
        # First run
        seed_data()

        # Second run
        seed_data()

        # Assert counts remain the same
        assert Tag.query.count() == 3
        assert Media.query.count() == 1
