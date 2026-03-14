# Renfe Tracker

Track Renfe trains and prices (media/larga distancia). Self-hosted, runs in Docker.

## Run with Docker

From the repo root:

```bash
docker compose up --build
```

Then open **http://localhost:8000**. To change the host port, set `PORT` in a `.env` file (e.g. `PORT=8080`) or when running.

## Data persistence

The SQLite database and any app data are stored on the host in **`./data`**, which is mounted into the container at `/data`. The DB file is `./data/renfe_tracker.db`. Data survives container restarts and rebuilds.

If you see permission errors when the app writes to `./data`, run: `chown -R 1000:1000 ./data`.
