# Playlist Update

A Python script to automatically update YouTube playlists using the Google API.

## Requirements

- Python 3.10+
- Google API credentials (see setup below)

## Installation

```bash
pip install -r requirements.txt
```

## Setup

1. Retrieve your `credentials.json` from google API and place it in the `credentials` folder.
2. Create a `.env` file with your the aimed playlist and channel identifiers. Also add  the minimum video duration time (O by default if you want all the videos, it was useful for me because I wanted to avoid shorts) and dry run mode state (to be sure everything runs correctly before really running it). It should look like this :

```.env
CHANNEL_ID=...
PLAYLIST_ID=...
SHORTS_MIN_SECONDS=0
DRY_RUN=true
```

## Usage

Run the `script/run.py` file.

## License

See LICENSE file for details.
