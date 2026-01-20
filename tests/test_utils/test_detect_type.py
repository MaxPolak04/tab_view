import pytest
from tab_view.utils import detect_type


@pytest.mark.parametrize(
    'filename',
    ['photo.jpg', 'photo.jpeg', 'photo.png', 'photo.gif']
)
def test_detect_type_returns_image_for_image_extensions(filename):
    assert detect_type(filename) == 'image'


@pytest.mark.parametrize(
        'filename',
        ['movie.mp4', 'clip.webm', 'presentation.mov']
)
def test_detect_type_returns_video_for_non_image_extensions(filename):
    assert detect_type(filename) == 'video'
