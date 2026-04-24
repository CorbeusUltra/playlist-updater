import os
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    root_dir = Path(__file__).resolve().parents[1]
    src_dir = root_dir / "src"
    sys.path.insert(0, str(src_dir))


def pytest_configure() -> None:
    _ensure_src_on_path()

    # Default env values so imports stay deterministic in tests.
    os.environ.setdefault("CHANNEL_ID", "UC12345678901234567890")
    os.environ.setdefault("PLAYLIST_ID", "PL12345678901234567890123456789012")
    os.environ.setdefault("SHORTS_MIN_SECONDS", "60")
    os.environ.setdefault("DRY_RUN", "true")
