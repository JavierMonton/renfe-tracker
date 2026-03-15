---
name: renfe-queries
description: How to query Renfe train schedules and prices using this project's integrated library (app.renfe_lib). Use when searching trains, checking prices, or listing stations (Barcelona–Zaragoza, Madrid–Valencia, etc.).
---

# Renfe train queries (this project)

Renfe search and prices run **in-process** in this repo. There is **no external MCP server**. Use the code in this project.

## Entry point: `app.renfe_lib`

All Renfe queries go through **`app.renfe_lib`**:

- **`search_trains_schedules(origin, destination, date, page=1, per_page=50)`**  
  Schedules only (GTFS). Returns a dict with `success`, `results`, `total_results`, `page`, `total_pages`, `message`. Each result has `train_type`, `origin_station`, `destination_station`, `departure_time`, `arrival_time`, `duration_hours`, `duration_mins`. **No prices.**

- **`get_train_prices(origin, destination, date, page=1, per_page=20)`**  
  Real-time prices (scrapes Renfe). Returns a list of dicts: `train_type`, `departure_time`, `arrival_time`, `duration_minutes`, `price`, `available`. **One call returns many trains**; no need to query train by train.

- **`find_stations(city_name)`**  
  List stations in a city. Returns list of dicts with `name`, `gtfs_id`, `has_gtfs`, `has_renfe`.

- **`ensure_gtfs_updated()`**  
  Run GTFS update check and download if needed. Returns `True` if data was updated.

## How to run a search

1. From the project root, ensure the app or a Python process can import `app.renfe_lib` (e.g. run with `sys.path` including the repo root).
2. Call **`get_train_prices(origin, destination, date)`** to get trains with prices in one go. Use **`search_trains_schedules(...)`** if you only need schedules (no prices).
3. Date format: **ISO** `YYYY-MM-DD` (e.g. `2026-04-07`). The library also accepts European and written formats internally.
4. City names (e.g. `"Barcelona"`, `"Calatayud"`, `"Zaragoza"`) are enough; the library resolves them to stations.

## Configuration

- **GTFS path:** `RENFE_GTFS_DIR` (optional). Default: `{DATA_DIR}/renfe_schedule` if `DATA_DIR` is set, else `renfe_schedule` in the current directory. GTFS is downloaded on first use if missing.
- **Backend:** The HTTP search API uses this library by default (`RENFE_BACKEND=gtfs`). Set `RENFE_BACKEND=playwright` to use the old Playwright/Chromium backend instead.

## Summary

| Need               | Function / source              | Data source        |
|--------------------|--------------------------------|--------------------|
| Schedules          | `search_trains_schedules()`    | GTFS (renfe_mcp)   |
| Prices (with times)| `get_train_prices()`           | Renfe website (DWR scrape) |
| Stations in a city | `find_stations()`              | renfe_mcp station service |

Implementation lives under **`renfe_mcp/`** (vendored GTFS + scraper). See **`renfe_mcp/README.md`** for details.

For low-level Renfe website details (DWR, session, station codes), see **`.cursor/renfe-calls.md`**.
