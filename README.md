# Telegram Repost Bot

Reposts messages from a source Telegram channel to a destination channel, replacing links with a promotional URL.

## Setup

1. Set environment variables: `API_ID`, `API_HASH`, `SOURCE_CHANNEL`, `DEST_CHANNEL`
2. Run locally first to generate the session file (required for Railway)
3. Deploy to Railway with the session file included

## Files

- `repost.py` — Main bot logic
- `requirements.txt` — Python dependencies
- `Procfile` — Railway worker command
- `session_name.session` — Auth session (generate locally before deploy)
