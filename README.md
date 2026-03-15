# Renfe Tracker

Track Renfe trains and prices (media/larga distancia). Self-hosted, runs in Docker.

## Run with Docker

From the repo root:

```bash
docker compose up --build
```

Then open **http://localhost:8000**. To change the host port, set `PORT` in a `.env` file (e.g. `PORT=8080`) or when running.

**Search (Renfe):** By default the app uses the **integrated Renfe library** (GTFS schedules + live price scraping). No separate MCP server or browser is required; everything runs inside this project. GTFS data is downloaded automatically on first use into `DATA_DIR/renfe_schedule` (in Docker, `/data/renfe_schedule`).  
To use the old **Playwright/Chromium** backend instead, set `RENFE_BACKEND=playwright` (and use Docker or run `playwright install chromium` locally).  
To test search **without** any real Renfe calls, set `RENFE_MOCK=1` (or `RENFE_USE_MOCK=true`): the API returns a fixed list of example trains.

## Data persistence

The SQLite database and any app data are stored on the host in **`./data`**, which is mounted into the container at `/data`. The DB file is `./data/renfe_tracker.db`. Renfe GTFS schedule data (used by the integrated backend) is stored in `./data/renfe_schedule` and is also persisted. Data survives container restarts and rebuilds.

If you see permission errors when the app writes to `./data`, run: `chown -R 1000:1000 ./data`.

## Tests

Run tests locally (no Docker, no real Renfe calls; Renfe is mocked):

```bash
pip install -r requirements.txt
pytest
```

Tests use a temporary database and mock the Renfe website so they are fast and reliable. To run with verbose output: `pytest -v`.
