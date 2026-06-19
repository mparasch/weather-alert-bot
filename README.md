# weather-alert-bot

A small Discord bot that monitors local weather forecasts (via OpenWeather) and posts alerts to a channel when rain is expected. Alerts include interactive buttons to mark an item as covered or to snooze alerts.

## Features

- Periodic weather checks (every 30 minutes)
- Posts alerts to a configured Discord channel when rain is forecast
- Interactive buttons to `Mark Covered` or `Snooze` alerts
- Persistent state (covered / snoozed) stored on disk

## Requirements

- Python 3.8+
- See `requirements.txt` for Python package dependencies

## Configuration

Set the following environment variables before running the bot:

- `DISCORD_TOKEN` — your bot token from the Discord Developer Portal
- `OPENWEATHER_API_KEY` — API key for OpenWeather (https://openweathermap.org/)
- `CHANNEL_ID` — numeric ID of the Discord channel where alerts should be posted
- `LAT` — latitude (decimal) for the location to monitor
- `LON` — longitude (decimal) for the location to monitor

The bot stores runtime state in `/app/state.json` by default; ensure the process can write to that path or update the code if you want a different location.

## Install

1. Create a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate    # bash / macOS
.\.venv\Scripts\Activate   # PowerShell on Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

Set environment variables and run the bot. Example (PowerShell):

```powershell
$env:DISCORD_TOKEN = "your_token_here"
$env:OPENWEATHER_API_KEY = "your_openweather_key"
$env:CHANNEL_ID = "123456789012345678"
$env:LAT = "37.7749"
$env:LON = "-122.4194"
python bot.py
```

Or (bash):

```bash
export DISCORD_TOKEN="your_token_here"
export OPENWEATHER_API_KEY="your_openweather_key"
export CHANNEL_ID="123456789012345678"
export LAT="37.7749"
export LON="-122.4194"
python bot.py
```

## Usage

- The bot runs a background task that checks the forecast and posts an alert message in the configured channel when rain is expected.
- Alert messages include two buttons:
	- `Mark Covered` — marks the item as covered and pauses alerts for 24 hours
	- `Snooze` — snoozes alerts for a short period (default 3 hours)
- Button responses are visible to everyone in the channel (public messages).

## Notes & Troubleshooting

- The code expects numeric `CHANNEL_ID`, `LAT`, and `LON` values; ensure those environment variables are set correctly.
- If you encounter a Python syntax error referencing `LAT`/`LON` at startup, let me know and I can patch `bot.py` to fix the parsing lines.
- On Windows, ensure the process has permission to create the `/app` folder or change `STATE_FILE` in [bot.py](bot.py) to a writable path.

## Files of interest

- [bot.py](bot.py) — main bot implementation
- [requirements.txt](requirements.txt) — Python dependencies

## Contributing

Feel free to open issues or PRs. If you want, I can help: fix config parsing, add Docker support, or add unit tests.

## License

MIT — see LICENSE (not included)

