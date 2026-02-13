import pytest

from tab_view.utils import str_to_bool


@pytest.mark.parametrize(
    "value", ["true", "True", "TRUE", "1", "yes", "Yes", "YES", 1, True]
)
def test_str_to_bool_returns_true(value):
    """
    Test inputs that should evaluate to True.
    Includes mixed types (int, bool) to verify type casting.
    """
    assert str_to_bool(value) is True


@pytest.mark.parametrize(
    "value", ["false", "False", "0", "no", "random_text", "", None, 0, False]
)
def test_str_to_bool_returns_false(value):
    """
    Test inputs that should evaluate to False.
    Anything not explicitly in the 'true' list should return False.
    """
    assert str_to_bool(value) is False
