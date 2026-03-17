# Renfe Tracker

Track Renfe trains and prices (media/larga distancia). Self-hosted, runs in Docker.

**Setup:** Dependencies are managed with [uv](https://github.com/astral-sh/uv). Run `uv sync` to create the environment and install from `pyproject.toml` / `uv.lock`.

## Run with Docker

### Building the image

From the repo root:

```bash
docker build -t renfe-tracker .
```

The image exposes port **8000** and expects a **data volume** at `/data` (SQLite DB, GTFS data in `/data/renfe_schedule`). Mount it to persist data across restarts.

### Running with compose (recommended for 24/7)

Using the provided `compose.yaml`:

```bash
docker compose up --build -d
```

Then open **http://localhost:8000**. To change the host port, set `PORT` in a `.env` file (e.g. `PORT=8080`) or when running (for example, `PORT=8080 docker compose up -d`).

The compose file mounts `./data` to `/data` and uses `restart: unless-stopped` so the app restarts automatically after failures or reboots. You can replace `./data` with your own path (e.g. `/srv/renfe-tracker/data`) so the database and config stay on your host.

**Search (Renfe):** The app uses the **integrated Renfe library** (GTFS schedules + live price scraping via DWR). No separate MCP server or browser is required; everything runs inside this project. GTFS data is downloaded automatically on first use into `DATA_DIR/renfe_schedule` (in Docker, `/data/renfe_schedule`).  
To test search **without** any real Renfe calls, set `RENFE_MOCK=1` (or `RENFE_USE_MOCK=true`): the API returns a fixed list of example trains.

## Data persistence

The SQLite database and any app data are stored on the host in **`./data`**, which is mounted into the container at `/data` by `compose.yaml`. The DB file is `./data/renfe_tracker.db`. Renfe GTFS schedule data (used by the integrated backend) is stored in `./data/renfe_schedule` and is also persisted. Data survives container restarts and rebuilds; the service is configured with `restart: unless-stopped` so it will come back up automatically after failures or host reboots.

If you see permission errors when the app writes to `./data`, run: `chown -R 1000:1000 ./data`.

## Local development and tests

This project uses **[uv](https://github.com/astral-sh/uv)** for dependencies and runs.

From the repo root:

```bash
uv sync
uv run pytest
```

- **`uv sync`** – creates `.venv` (if needed), installs the project and dependencies from `pyproject.toml` / `uv.lock`.
- **`uv run pytest`** – runs tests in the project env (no Docker, no real Renfe calls; Renfe is mocked).

Verbose tests: `uv run pytest -v`. Run the app locally: `uv run uvicorn app.main:app --reload`.
