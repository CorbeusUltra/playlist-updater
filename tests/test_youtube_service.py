from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest

from playlist_updater.youtube_service import (
    LAST_UPDATED_PREFIX,
    format_last_updated_line,
    parse_duration,
    strip_last_updated_line,
    update_playlist_last_updated,
)


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


def test_format_last_updated_line_english_with_time_and_tz():
    when = datetime(2026, 6, 5, 14, 30, tzinfo=ZoneInfo("Europe/Paris"))
    assert format_last_updated_line(when) == "🔄 Last updated: 5 June 2026 at 14:30 CEST"


def test_strip_last_updated_line_removes_existing_marker():
    description = "Cool beats playlist.\n\n🔄 Last updated: 1 January 2026 at 09:00 CET"
    assert strip_last_updated_line(description) == "Cool beats playlist."


def test_strip_last_updated_line_leaves_description_without_marker():
    description = "Cool beats playlist.\nNo marker here."
    assert strip_last_updated_line(description) == "Cool beats playlist.\nNo marker here."


def test_update_playlist_last_updated_preserves_title_and_single_marker():
    youtube = MagicMock()
    youtube.playlists().list().execute.return_value = {
        "items": [
            {
                "snippet": {
                    "title": "My Beats",
                    "description": "Cool beats.\n\n🔄 Last updated: 1 January 2026 at 09:00 CET",
                }
            }
        ]
    }

    when = datetime(2026, 6, 5, 14, 30, tzinfo=ZoneInfo("Europe/Paris"))
    assert update_playlist_last_updated(youtube, "PLX", when) is True

    update_kwargs = youtube.playlists().update.call_args.kwargs
    sent_snippet = update_kwargs["body"]["snippet"]
    assert update_kwargs["body"]["id"] == "PLX"
    assert sent_snippet["title"] == "My Beats"
    assert sent_snippet["description"].count(LAST_UPDATED_PREFIX) == 1
    assert sent_snippet["description"].endswith("🔄 Last updated: 5 June 2026 at 14:30 CEST")
    assert sent_snippet["description"].startswith("Cool beats.")


def test_update_playlist_last_updated_returns_false_when_playlist_missing():
    youtube = MagicMock()
    youtube.playlists().list().execute.return_value = {"items": []}

    when = datetime(2026, 6, 5, 14, 30, tzinfo=ZoneInfo("Europe/Paris"))
    assert update_playlist_last_updated(youtube, "PLX", when) is False
    youtube.playlists().update.assert_not_called()
