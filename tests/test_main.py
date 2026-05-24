import json
from unittest.mock import MagicMock

from playlist_update.main import load_local_state, main, save_local_state


def test_load_local_state_missing_file_returns_none(tmp_path):
    state_file = tmp_path / "playlist_data.json"
    assert load_local_state(state_file=state_file) is None


def test_load_local_state_reads_existing_json(tmp_path):
    state_file = tmp_path / "playlist_data.json"
    expected = {"playlist_id": "PLX", "videos": [{"video_id": "abc"}]}
    state_file.write_text(json.dumps(expected), encoding="utf-8")

    assert load_local_state(state_file=state_file) == expected


def test_save_local_state_adds_metadata_and_serializes(tmp_path):
    state_file = tmp_path / "playlist_data.json"
    payload = {
        "playlist_id": "PLX",
        "videos": [
            {
                "video_id": "old",
                "published_at": "2024-01-01T00:00:00Z",
                "title": "Older",
            },
            {
                "video_id": "new",
                "published_at": "2025-01-01T12:00:00Z",
                "title": "Newer",
            },
        ],
    }

    save_local_state(payload, state_file=state_file)

    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["total_count"] == 2
    assert saved["latest_video"] == {
        "video_id": "new",
        "published_at": "2025-01-01T12:00:00Z",
    }
    assert "extraction_timestamp" in saved


def test_save_local_state_handles_empty_videos(tmp_path):
    state_file = tmp_path / "playlist_data.json"
    payload = {"playlist_id": "PLX", "videos": []}

    save_local_state(payload, state_file=state_file)

    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["total_count"] == 0
    assert "latest_video" not in saved
    assert "extraction_timestamp" in saved


def test_save_local_state_creates_missing_parent_directory(tmp_path):
    state_file = tmp_path / "nested" / "missing" / "playlist_data.json"
    payload = {"playlist_id": "PLX", "videos": []}

    save_local_state(payload, state_file=state_file)

    assert state_file.exists()


def test_main_returns_cleanly_when_local_state_has_no_videos(tmp_path, monkeypatch, caplog):
    state_file = tmp_path / "playlist_data.json"
    state_file.write_text(
        json.dumps({"playlist_id": "PLX", "videos": []}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "playlist_update.main.auth_manager.get_authenticated_service",
        lambda: MagicMock(),
    )

    youtube_module = MagicMock()

    with caplog.at_level("WARNING"):
        main(youtube_module=youtube_module, state_file=state_file)

    youtube_module.get_channel_uploads_id.assert_not_called()
    assert any("aucune vidéo connue" in record.message for record in caplog.records)
