---
id: installation
sidebar_position: 2
title: Installation
---

# Installation

Renfe Tracker is distributed as a Docker image. The **recommended** way to run it is with Docker Compose, but plain `docker run` and local development without Docker are also supported.

---

## Option 1 — Docker Compose (recommended) {#docker-compose}

Docker Compose is the simplest option for a permanent, always-on deployment. The compose file handles volume mounts, automatic restarts, and environment variable configuration in one place.

### 1. Get the files

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/renfe-tracker.git
cd renfe-tracker
cp docker-compose.example.yml docker-compose.yml
```

### 2. (Optional) Configure environment variables

Open `docker-compose.yml` and uncomment / fill in any options you need:

```yaml
services:
  app:
    build: .
    ports:
      - "${PORT:-8000}:8000"
    environment:
      DATA_DIR: /data

      # ── Email alerts ─────────────────────────────────────────
      # SMTP_HOST: smtp.example.com
      # SMTP_PORT: 587
      # SMTP_USERNAME: alerts@example.com
      # SMTP_PASSWORD: your-smtp-password

      # ── Home Assistant alerts ────────────────────────────────
      # HA_URL: http://homeassistant.local:8123
      # HA_TOKEN: your-long-lived-access-token

    volumes:
      - ./data:/data
    restart: unless-stopped
```

### 3. Build and start

```bash
docker compose up --build -d
```

Open **http://localhost:8000**. To use a different port, set `PORT` in a `.env` file or inline:

```bash
PORT=9000 docker compose up -d
```

### 4. Stopping / updating

```bash
# Stop
docker compose down

# Pull latest code and rebuild
git pull
docker compose up --build -d
```

Data in `./data` is never touched by these commands.

---

## Option 2 — `docker run` {#docker-run}

Use this if you prefer managing the container manually or want to integrate it into an existing setup.

### Build the image

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/renfe-tracker.git
cd renfe-tracker
docker build -t renfe-tracker .
```

### Run the container

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  renfe-tracker
```

With email and Home Assistant environment variables:

```bash
docker run -d \
  --name renfe-tracker \
  --restart unless-stopped \
  -p 8000:8000 \
  -v "$(pwd)/data:/data" \
  -e SMTP_HOST=smtp.example.com \
  -e SMTP_PORT=587 \
  -e SMTP_USERNAME=alerts@example.com \
  -e SMTP_PASSWORD=your-password \
  -e HA_URL=http://homeassistant.local:8123 \
  -e HA_TOKEN=your-ha-token \
  renfe-tracker
```

Open **http://localhost:8000**.

---

## Option 3 — Local development (no Docker) {#local-dev}

This is useful if you want to hack on the code. It requires [uv](https://github.com/astral-sh/uv) (Python package manager) and Node.js 18+.

### Backend

```bash
# Install dependencies
uv sync

# Start the API server (auto-reload on code changes)
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev      # Vite dev server on http://localhost:5173
                 # All /api requests are proxied to :8000
```

The Vite dev server proxies `/api` calls to the FastAPI backend, so you get hot-reload on the frontend while the backend handles data.

### Running tests

```bash
uv run pytest          # all tests (Renfe is mocked, no real network calls)
uv run pytest -v       # verbose output
```

---

## Data persistence

All application data lives in the `./data` directory (or wherever you point the volume):

| Path | Contents |
|------|----------|
| `./data/renfe_tracker.db` | SQLite database (trips, prices, notifications) |
| `./data/renfe_schedule/` | Renfe GTFS data (downloaded automatically on first search) |

The database and GTFS files survive container restarts, rebuilds, and updates. Back up the `./data` directory to keep your tracked trips and price history.

### File ownership

The container runs as root by default so it can always create and write the database on first start. If you want the host files owned by your user, set `PUID` and `PGID`:

```yaml
environment:
  PUID: 1000
  PGID: 1000
```

Or after first start:

```bash
chown -R $(id -u):$(id -g) ./data
```
