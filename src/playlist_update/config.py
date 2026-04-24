import os
from pathlib import Path
from dotenv import load_dotenv


def find_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("Project root not found")


# Files path
ROOT_DIR = find_root(Path(__file__).resolve())
ENV_FILE = ROOT_DIR / ".env"
PLAYLIST_DATA_FILE = ROOT_DIR / "data" / "playlist_data.json"
TOKEN_FILE = ROOT_DIR / "credentials" / "token.json"
CREDENTIALS_FILE =  ROOT_DIR / "credentials" / "credentials.json"


load_dotenv(dotenv_path=ENV_FILE, override=False)


# Variables
def parse_bool(value: str | None, var_name: str) -> bool:
    if value is None:
        raise ValueError(f"{var_name} is required")
    v = value.strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    raise ValueError(f"{var_name} must be a boolean (true/false)")

def parse_int(value: str | None, var_name: str, minimum: int = 0) -> int:
    if value is None:
        raise ValueError(f"{var_name} is required")
    try:
        n = int(value)
    except ValueError:
        raise ValueError(f"{var_name} must be an integer")
    if n < minimum:
        raise ValueError(f"{var_name} must be >= {minimum}")
    return n

CHANNEL_ID = os.getenv("CHANNEL_ID")
PLAYLIST_ID = os.getenv("PLAYLIST_ID")
SHORTS_MIN_SECONDS = parse_int(os.getenv("SHORTS_MIN_SECONDS"), "SHORTS_MIN_SECONDS", minimum=1)
DRY_RUN = parse_bool(os.getenv("DRY_RUN"), "DRY_RUN")

if not CHANNEL_ID or not CHANNEL_ID.startswith("UC"):
    raise ValueError("CHANNEL_ID must start with 'UC'")

if not PLAYLIST_ID or not PLAYLIST_ID.startswith("PL"):
    raise ValueError("PLAYLIST_ID must start with 'PL'")
