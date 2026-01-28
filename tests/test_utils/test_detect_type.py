import pytest
from tab_view.utils import detect_type


@pytest.mark.parametrize(
    'filename',
    ['photo.jpg', 'photo.jpeg', 'photo.png', 'photo.gif', 'PHOTO.JPG', 'Image.PnG']
)
def test_detect_type_returns_image(filename):
    """
    Checks image extensions, including case variations.
    """
    assert detect_type(filename) == 'image'


@pytest.mark.parametrize(
    'filename',
    ['movie.mp4', 'clip.webm', 'presentation.mov', 'ARCHIVE.MP4']
)
def test_detect_type_returns_video(filename):
    """
    Checks video extensions.
    """
    assert detect_type(filename) == 'video'


@pytest.mark.parametrize(
    'filename',
    ['my.super.photo.jpg', 'data.backup.tar.gz.mp4']
)
def test_detect_type_handles_multiple_dots(filename):
    """
    Ensures that the function only checks the last extension after the last period.
    """
    if filename.endswith('jpg'):
        assert detect_type(filename) == 'image'
    else:
        assert detect_type(filename) == 'video'


def test_detect_type_defaults_to_video_for_unknown():
    """
    Tests the current application logic: anything that is not an image
    is treated as a video (even PDF or TXT).
    """
    assert detect_type('document.pdf') == 'video'
    assert detect_type('readme.txt') == 'video'
    