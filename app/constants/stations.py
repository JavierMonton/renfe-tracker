"""
Static-like list of Renfe stations for origin/destination selection.

The data is derived from the vendored renfe_mcp station service and
includes only stations that have both:
- GTFS coverage (for schedules)
- Renfe codes (for price checking)

The list is generated at import time via the same logic used by the
helper script in app/scripts/generate_stations.py. In practice this is
effectively static for the lifetime of the process, and can be
regenerated when GTFS / Renfe metadata changes.
"""

from __future__ import annotations

from typing import Any, List, Dict

from app.scripts.generate_stations import generate_station_data

RENFE_STATIONS: List[Dict[str, Any]] = generate_station_data()

