# Renfe Tracker

[![Docker Hub](https://img.shields.io/docker/v/jmonton/renfe-tracker/latest?label=Docker%20Hub&logo=docker)](https://hub.docker.com/repository/docker/jmonton/renfe-tracker/tags)

Track Renfe trains and prices (media/larga distancia). Self-hosted, runs in Docker.

Features, installation, and configuration, 
explained in the [**Documentation website**](https://JavierMonton.github.io/renfe-tracker/).


Using this application, a user can search for Renfe trains, see possible trains not published, see estimated price ranges, 
and track trips to get notified of price changes.


---

## Table of Contents

- [Features](#features)
- [Run with Docker](#run-with-docker)
  - [Running with compose (recommended for 24/7)](#running-with-compose-recommended-for-247)
- [Configuration](#configuration)

---

## Features

- See Price Ranges and Possible Trains: 
When searching for trains, the app shows estimated price ranges based on historical data and highlights possible trains that may not be published yet.

![img.png](./website/static/img/search-screenshot.png)
- Track multiple trips:

![img_1.png](./website/static/img/trips-screenshot.png)
- See historical price changes:

![img_2.png](./website/static/img/prices-screenshot.png)



## Run with Docker

The image is published on Docker Hub as [`jmonton/renfe-tracker:latest`](https://hub.docker.com/r/jmonton/renfe-tracker) — no build step required.

It exposes port **8000** and expects a **data volume** at `/data` (SQLite DB, GTFS data in `/data/renfe_schedule`). Mount it to persist data across restarts.

### Running with compose (recommended for 24/7)

Copy the [example compose file](docker-compose.example.yml) and start:

```bash
cp docker-compose.example.yml docker-compose.yml
docker compose up -d
```

Open **http://localhost:8000**. To change the host port, set `PORT` in a `.env` file (e.g. `PORT=8080`) or inline (e.g. `PORT=8080 docker compose up -d`).

The compose file mounts `./data` to `/data` and uses `restart: unless-stopped` so the app restarts automatically after failures or reboots. You can replace `./data` with your own path (e.g. `/srv/renfe-tracker/data`) so the database and config stay on your host.

**PUID / PGID (optional):** The app process runs as root inside the container so it can always create and write the database on first run (avoids permission issues with bind-mounted volumes). If you set `PUID` and `PGID`, the entrypoint will chown `/data` and `/app` to that user when possible, so files on the host (e.g. `./data`) end up owned by your user. You can then run with your preferred ownership; the app will still run as root and write to `/data`.

**Search (Renfe):** The app uses the **integrated Renfe library** (GTFS schedules + live price scraping via DWR). No separate MCP server or browser is required; everything runs inside this project. GTFS data is downloaded automatically on first use into `DATA_DIR/renfe_schedule` (in Docker, `/data/renfe_schedule`).  
To test search **without** any real Renfe calls, set `RENFE_MOCK=1` (or `RENFE_USE_MOCK=true`): the API returns a fixed list of example trains.

## Configuration

For configuration options, refer to the [documentation website](https://javiermonton.github.io/renfe-tracker/configuration).
