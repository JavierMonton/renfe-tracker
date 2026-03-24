"""
Helper script to generate a static list of Renfe stations that have
both GTFS data (for schedules) and Renfe codes (for prices).

Run this script manually to regenerate the station list constant used
by the app (see app/constants/stations.py).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import os

from app.renfe_lib import _ensure_gtfs_dir
from renfe_mcp.schedule_searcher import ScheduleSearcher
from renfe_mcp.update_data import update_if_needed
from renfe_mcp.station_service import UnifiedStation, get_station_service


def _collect_unified_stations() -> List[UnifiedStation]:
    """
    Collect unified stations that have both GTFS and Renfe data.

    This scans all GTFS stops and tries to match each one with Renfe
    station metadata, mirroring StationService._find_in_gtfs but
    without filtering by a specific city name.
    """
    gtfs_dir = _ensure_gtfs_dir()
    if not os.path.isdir(gtfs_dir) or not os.path.isfile(os.path.join(gtfs_dir, "stops.txt")):
        update_if_needed()
    searcher = ScheduleSearcher(gtfs_dir)
    svc = get_station_service(searcher.get_stops_dataframe())

    stations: List[UnifiedStation] = []
    seen: set[Tuple[str, str | None]] = set()

    for _, stop in svc.gtfs_stops_df.iterrows():
        gtfs_name = stop["stop_name"]
        gtfs_id = str(stop["stop_id"])

        renfe_match = svc._match_stations(gtfs_name, gtfs_id)
        if not renfe_match:
            continue

        station = UnifiedStation(
            name=gtfs_name,
            gtfs_id=gtfs_id,
            renfe_code=renfe_match.get("cdgoEstacion"),
            renfe_uic=renfe_match.get("cdgoUic"),
            source="both",
        )

        if not (station.has_gtfs_data() and station.has_renfe_data()):
            continue

        key = (station.name, station.renfe_code)
        if key in seen:
            continue
        seen.add(key)
        stations.append(station)

    stations.sort(key=lambda s: s.name)
    return stations


def generate_station_data() -> List[Dict[str, Any]]:
    """
    Generate the list of station dicts for the static module.

    Each entry has:
        - name: display name (string)
        - gtfs_id: GTFS stop_id (string)
        - renfe_code: Renfe cdgoEstacion code (string)
        - renfe_uic: Renfe cdgoUic code (string or None)
    """
    stations = _collect_unified_stations()
    data: List[Dict[str, Any]] = []
    for s in stations:
        data.append(
            {
                "name": s.name,
                "gtfs_id": str(s.gtfs_id) if s.gtfs_id is not None else None,
                "renfe_code": s.renfe_code,
                "renfe_uic": s.renfe_uic,
            }
        )
    return data


def main() -> None:
    """
    Print a Python literal for the RENFE_STATIONS constant to stdout.

    Usage (from project root):
        python -m app.scripts.generate_stations > /tmp/stations.py
    """
    import pprint

    data = generate_station_data()
    print("RENFE_STATIONS = ", end="")
    pprint.pprint(data, sort_dicts=False, width=120)


if __name__ == "__main__":
    main()

