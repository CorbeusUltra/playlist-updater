# playlist_update

[![Tests](https://github.com/CorbeusUltra/playlist_update/actions/workflows/tests.yml/badge.svg)](https://github.com/CorbeusUltra/playlist_update/actions/workflows/tests.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/github/license/CorbeusUltra/playlist_update)

A Python tool that automatically keeps a YouTube playlist in sync with new uploads from a given channel, with an optional duration filter to skip YouTube Shorts.

## How it works

The script authenticates with Google using OAuth 2.0 the first time it runs, then persists the token locally so that all subsequent runs are non-interactive — the browser window only opens once. On the very first execution (bootstrap), the current contents of the target playlist are downloaded and saved into a local JSON file (`data/playlist_data.json`), which becomes the reference point used to detect new uploads on every later run.

From that point on, each run fetches the channel's recent uploads and keeps only the videos published strictly after the most recent video already known locally. Videos shorter than the `SHORTS_MIN_SECONDS` threshold are filtered out — this is the mechanism used to exclude YouTube Shorts — and the remaining new videos are appended to the target playlist in chronological order (oldest first). A `DRY_RUN` mode runs the entire pipeline without actually modifying the playlist, which is the recommended way to verify your configuration before the first real run.

The script is deliberately quota-friendly: it reads the channel's system `uploads` playlist (1 API unit per page) instead of calling `search()` (which costs 100 units per query), and it stops paginating as soon as it encounters a video older than the local reference date.

## Requirements

- Python 3.10+
- A Google Cloud project with the **YouTube Data API v3** enabled
- OAuth 2.0 credentials (type: *Desktop app*) downloaded as `credentials.json`

## Installation

```bash
git clone https://github.com/CorbeusUltra/playlist_update.git
cd playlist_update
pip install -r requirements.txt
```

## Google API credentials setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a new project (or select an existing one).
2. In the left menu, go to **APIs & Services > Library**. Search for **YouTube Data API v3** and click **Enable**.
3. Go to **APIs & Services > OAuth consent screen**. Choose **External**, fill in the required fields (app name, support email), and save.
4. Go to **APIs & Services > Credentials**. Click **Create credentials > OAuth client ID**. Select **Desktop app** as the application type.
5. Download the generated JSON file and rename it `credentials.json`. Place it in the `credentials/` folder at the root of the project.

> The first time you run the script, a browser window will open asking you to authorize the application. After authorization, a `token.json` file is saved in `credentials/` and reused for all subsequent runs.
>
> **About the redirect URI:** if you created your OAuth client as a **Desktop app**, Google accepts any `http://localhost:<port>` redirect automatically and you can leave `OAUTH_PORT` unset (the script will pick a free port). If your OAuth client is a **Web application**, you must either (a) recreate it as a Desktop app, or (b) declare an explicit authorized redirect URI like `http://localhost:8080` in the Cloud Console and set `OAUTH_PORT=8080` in your `.env` so the script binds to the matching port.

## Configuration

Create a `.env` file at the root of the project with the following variables:

```env
CHANNEL_ID=UCxxxxxxxxxxxxxxxxxxxxxxxx   # YouTube channel ID (starts with UC)
PLAYLIST_ID=PLxxxxxxxxxxxxxxxxxxxxxxxx  # Target playlist ID (starts with PL)
SHORTS_MIN_SECONDS=60                   # Minimum video duration in seconds (0 = keep all videos)
DRY_RUN=true                            # Set to false to actually modify the playlist
# Optional — port used by the local OAuth server during the one-time browser flow.
# Leave unset (default 0) to pick a free port automatically. Set to a fixed port
# (e.g. 8080) if your OAuth client in Google Cloud Console requires a specific
# redirect URI like http://localhost:8080.
# OAUTH_PORT=8080
```

**How to find the channel and playlist IDs:**
- **Channel ID:** Go to the channel page on YouTube. The URL contains `/channel/UCxxxxxxx` — copy the `UC...` part. If the channel uses a custom URL, open the page source and search for `"channelId"`.
- **Playlist ID:** Open the playlist on YouTube. The URL contains `list=PLxxxxxxx` — copy the `PL...` part.

## Usage

```bash
python script/run.py
```

On the first run, a browser window will open for OAuth authorization. Subsequent runs are fully non-interactive.

To verify your setup without modifying the playlist, keep `DRY_RUN=true`.

## Project structure

```
playlist_update/
├── script/run.py               # Entry point
├── src/playlist_update/
│   ├── auth_manager.py         # OAuth 2.0 lifecycle (token generation, refresh)
│   ├── config.py               # Environment variable parsing and validation
│   ├── main.py                 # Orchestration logic and local state management
│   └── youtube_service.py      # YouTube Data API v3 wrapper
├── tests/                      # pytest test suite
├── data/playlist_data.json     # Local state cache (auto-created on first run)
└── credentials/                # credentials.json and token.json (not versioned)
```

## License

MIT — see [LICENSE](LICENSE) for details.
