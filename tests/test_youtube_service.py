import pytest

from playlist_update.youtube_service import parse_duration


@pytest.mark.parametrize(
    ("duration_iso", "formatted", "seconds"),
    [
        ("PT4M13S", "4:13", 253),
        ("PT59S", "0:59", 59),
        ("PT2H3M4S", "2:03:04", 7384),
        ("PT1H", "1:00:00", 3600),
        ("PT15M", "15:00", 900),
        ("PT0S", "0:00", 0),
    ],
)
def test_parse_duration_valid_formats(duration_iso, formatted, seconds):
    assert parse_duration(duration_iso) == (formatted, seconds)


@pytest.mark.parametrize("duration_iso", [None, "", "P1DT2H", "invalid"])
def test_parse_duration_invalid_or_empty_fallback(duration_iso):
    assert parse_duration(duration_iso) == ("0:00", 0)
