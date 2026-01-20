import pytest
from tab_view.utils import str_to_bool


@pytest.mark.parametrize(
    "value",
    ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]
)
def test_str_to_bool_returns_true_for_truthy_values(value):
    assert str_to_bool(value) is True


@pytest.mark.parametrize(
    "value",
    ["false", "False", "0", "no", "None", "", None]
)
def test_str_to_bool_returns_false_for_falsy_values(value):
    assert str_to_bool(value) is False
