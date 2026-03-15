# Renfe library (vendored)

This folder contains the **library part** of the [Renfe MCP server](https://github.com/belgrano9/renfe_mcp_server): GTFS schedule search and DWR-based price scraping. There is **no MCP server** here; the app calls this code directly from Python.

## What’s included

- **schedule_searcher** – Train schedules from Renfe GTFS open data.
- **station_service** – Station lookups (city → stations, GTFS + Renfe codes).
- **price_checker** – Real-time prices via Renfe website (DWR scraper).
- **scraper/** – DWR protocol and station codes.
- **update_data** – Download/update GTFS data from Renfe.

## Usage from the app

Use `app.renfe_lib`:

- `search_trains_schedules(origin, destination, date, page, per_page)` – schedules only.
- `get_train_prices(origin, destination, date, page, per_page)` – prices (one batch call).
- `find_stations(city_name)` – stations in a city.
- `ensure_gtfs_updated()` – run GTFS update check.

The search API uses this (only backend). No separate server process is required.

## GTFS data path

- **Env:** `RENFE_GTFS_DIR` (optional). Default: `{DATA_DIR}/renfe_schedule` if `DATA_DIR` is set, else `renfe_schedule` in the current directory.
- On first use, if GTFS is missing, the app runs an update and downloads data from Renfe.
- In Docker, set `DATA_DIR=/data`; GTFS is then stored in `/data/renfe_schedule` and persists with the volume.

## Updating this vendored code

To refresh from the upstream MCP server repo, copy the relevant modules from `src/renfe_mcp` (excluding `server.py` and `security.py`) and re-apply any project-specific changes (e.g. `update_data` using `RENFE_GTFS_DIR`).
