from tab_view.utils import detect_type


def test_detect_type_returns_image_for_image_extensions():
    assert detect_type('photo.jpg') == 'image'
    assert detect_type('photo.jpeg') == 'image'
    assert detect_type('photo.png') == 'image'
    assert detect_type('photo.gif') == 'image'


def test_detect_type_returns_video_for_non_image_extensions():
    assert detect_type("movie.mp4") == "video"
    assert detect_type("clip.webm") == "video"
    assert detect_type("presentation.mov") == "video"
