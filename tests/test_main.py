import json

from playlist_update.main import load_local_state, save_local_state


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
