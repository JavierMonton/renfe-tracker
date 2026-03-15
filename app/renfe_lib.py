"""
Renfe train search and prices using the vendored renfe_mcp library (GTFS + DWR scraper).

No MCP server process is required: all queries run in-process. Use this module
instead of running the Renfe MCP server when the app is the only consumer.

GTFS data: set RENFE_GTFS_DIR (default: DATA_DIR/renfe_schedule or ./renfe_schedule).
On first use, GTFS can be updated via update_if_needed() from renfe_mcp.update_data.
"""
import os
import logging
from typing import Any, Optional

logger = logging.getLogger("renfe_tracker.renfe_lib")

# Lazy-initialized state
_searcher = None
_gtfs_dir: Optional[str] = None


def _ensure_gtfs_dir() -> str:
    """Resolve GTFS directory from env and set RENFE_GTFS_DIR for update_data."""
    global _gtfs_dir
    if _gtfs_dir is not None:
        return _gtfs_dir
    data_dir = os.environ.get("DATA_DIR", ".")
    default = os.path.join(data_dir, "renfe_schedule") if data_dir != "." else "renfe_schedule"
    _gtfs_dir = os.environ.get("RENFE_GTFS_DIR", default)
    os.environ.setdefault("RENFE_GTFS_DIR", _gtfs_dir)
    return _gtfs_dir


def _init_searcher():
    """Lazy-init ScheduleSearcher and StationService (loads GTFS)."""
    global _searcher
    if _searcher is not None:
        return _searcher
    from renfe_mcp.schedule_searcher import ScheduleSearcher
    from renfe_mcp.station_service import get_station_service

    gtfs_dir = _ensure_gtfs_dir()
    if not os.path.isdir(gtfs_dir) or not os.path.isfile(os.path.join(gtfs_dir, "stops.txt")):
        try:
            from renfe_mcp.update_data import update_if_needed
            update_if_needed()
        except Exception as e:
            logger.warning("GTFS update check failed: %s", e)
    _searcher = ScheduleSearcher(gtfs_dir)
    get_station_service(_searcher.get_stops_dataframe())
    return _searcher


def _get_stops_for_city(city_name: str) -> list[str]:
    """Return list of GTFS stop IDs for a city (for schedule search)."""
    from renfe_mcp.station_service import get_station_service
    _init_searcher()
    svc = get_station_service()
    stations = svc.find_stations(city_name)
    gtfs_ids = [s.gtfs_id for s in stations if s.has_gtfs_data()]
    return gtfs_ids


def search_trains_schedules(
    origin: str,
    destination: str,
    date: str,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]:
    """
    Search train schedules (GTFS only, no prices).
    Returns dict with success, results, total_results, page, total_pages, message.
    """
    from renfe_mcp.schedule_searcher import ScheduleSearcher
    searcher = _init_searcher()
    formatted_date = ScheduleSearcher.format_date(date)
    origin_ids = _get_stops_for_city(origin)
    dest_ids = _get_stops_for_city(destination)
    if not origin_ids:
        return {"success": False, "results": [], "total_results": 0, "page": 1, "total_pages": 0, "message": f"No stations found for '{origin}'."}
    if not dest_ids:
        return {"success": False, "results": [], "total_results": 0, "page": 1, "total_pages": 0, "message": f"No stations found for '{destination}'."}
    return searcher.search_trains(origin_ids, dest_ids, formatted_date, page=page, per_page=per_page)


def get_train_prices(
    origin: str,
    destination: str,
    date: str,
    page: int = 1,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """
    Get real-time train prices (scrapes Renfe website). One call returns many trains.
    Returns list of dicts with train_type, departure_time, arrival_time, duration_minutes, price, available.
    """
    from renfe_mcp.price_checker import check_prices
    _init_searcher()
    return check_prices(origin, destination, date, page=page, per_page=per_page)


def find_stations(city_name: str) -> list[dict[str, Any]]:
    """Return list of stations in a city (name, gtfs_id, etc.)."""
    from renfe_mcp.station_service import get_station_service
    _init_searcher()
    svc = get_station_service()
    stations = svc.find_stations(city_name)
    return [{"name": s.name, "gtfs_id": s.gtfs_id, "has_gtfs": s.has_gtfs_data(), "has_renfe": s.has_renfe_data()} for s in stations]


def ensure_gtfs_updated() -> bool:
    """Run GTFS update check and download if needed. Returns True if updated."""
    _ensure_gtfs_dir()
    from renfe_mcp.update_data import update_if_needed
    return update_if_needed()
