import pytest

from playlist_update.config import parse_bool, parse_int


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1", True),
        ("true", True),
        ("YES", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("No", False),
        ("OFF", False),
    ],
)
def test_parse_bool_valid_values(value, expected):
    assert parse_bool(value, "DRY_RUN") is expected


def test_parse_bool_missing_value_raises_explicit_error():
    with pytest.raises(ValueError, match="DRY_RUN is required"):
        parse_bool(None, "DRY_RUN")


@pytest.mark.parametrize("value", ["", "2", "maybe", "yes please"])
def test_parse_bool_invalid_values_raise(value):
    with pytest.raises(ValueError, match="DRY_RUN must be a boolean"):
        parse_bool(value, "DRY_RUN")


@pytest.mark.parametrize(
    ("value", "minimum", "expected"),
    [
        ("1", 1, 1),
        ("10", 1, 10),
        (" 42 ", 0, 42),
        ("0", 0, 0),
    ],
)
def test_parse_int_valid_values(value, minimum, expected):
    assert parse_int(value, "SHORTS_MIN_SECONDS", minimum=minimum) == expected


def test_parse_int_missing_value_raises_explicit_error():
    with pytest.raises(ValueError, match="SHORTS_MIN_SECONDS is required"):
        parse_int(None, "SHORTS_MIN_SECONDS", minimum=1)


@pytest.mark.parametrize("value", ["abc", "1.5", "NaN"])
def test_parse_int_invalid_format_raises(value):
    with pytest.raises(ValueError, match="SHORTS_MIN_SECONDS must be an integer"):
        parse_int(value, "SHORTS_MIN_SECONDS", minimum=1)


def test_parse_int_below_minimum_raises_explicit_error():
    with pytest.raises(ValueError, match="SHORTS_MIN_SECONDS must be >= 1"):
        parse_int("0", "SHORTS_MIN_SECONDS", minimum=1)
