"""Search API: options (origins/destinations) and search (real Renfe trains)."""
import os
import logging
from datetime import date as _date

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db.connection import get_connection
from app.db import price_history as db_price_history

logger = logging.getLogger("renfe_tracker.search")

router = APIRouter(prefix="/search", tags=["search"])

# Static options for frontend dropdowns. Must include at least Zaragoza, Calatayud, Tafalla (Phase 1.1).
# Same list for origins and destinations; backend maps to Renfe codes in renfe_lib when needed.
SEARCH_CITIES = [
    # Original cities
    "Madrid",
    "Barcelona",
    "Valencia",
    "Sevilla",
    "Bilbao",
    "Málaga",
    "Zaragoza",
    "Calatayud",
    "Tafalla",
    # Additional cities from Renfe UI
    "A CORUÑA",
    "ALICANTE/ALACANT-TERMINAL",
    "CÓRDOBA-JULIO ANGUITA",
    "LLEIDA-PIRINEUS",
    "MÁLAGA MARÍA ZAMBRANO",
    "OURENSE",
    "SANTIAGO DE COMPOSTELA-DANIEL CASTELAO",
    "SEVILLA-SANTA JUSTA",
]

ORIGINS = SEARCH_CITIES
DESTINATIONS = SEARCH_CITIES

class SearchBody(BaseModel):
    date: str
    origin: str
    destination: str

@router.get("/options")
async def get_search_options():
    return {"origins": ORIGINS, "destinations": DESTINATIONS}

def _is_mock_enabled() -> bool:
    return os.environ.get("RENFE_MOCK") == "1" or os.environ.get("RENFE_USE_MOCK", "").lower() == "true"


def _is_possible_trains_enabled() -> bool:
    val = os.environ.get("RENFE_POSSIBLE_TRAINS", "1").strip().lower()
    return val not in ("0", "false")


def _mock_trains() -> list:
    """Fixed example trains when RENFE_MOCK=1 or RENFE_USE_MOCK=true (no real backend)."""
    return [
        {"name": "AVE", "price": 45.50, "duration_minutes": 90, "estimated_price_min": None, "estimated_price_max": None, "estimated_prices": [], "is_possible": False, "departure_time": "09:30"},
        {"name": "Avlo", "price": 25.00, "duration_minutes": 95, "estimated_price_min": None, "estimated_price_max": None, "estimated_prices": [], "is_possible": False, "departure_time": "11:15"},
        {"name": "Alvia", "price": 38.20, "duration_minutes": 120, "estimated_price_min": None, "estimated_price_max": None, "estimated_prices": [], "is_possible": False, "departure_time": "14:00"},
    ]


def _trains_from_gtfs_backend(date: str, origin: str, destination: str) -> list:
    """Use vendored renfe_mcp (GTFS + DWR) to get trains with prices. Returns same shape with is_possible=False."""
    from app.renfe_lib import get_train_prices
    results = get_train_prices(origin, destination, date, page=1, per_page=50)
    return [
        {
            "name": t["train_type"],
            "price": t["price"] if t.get("available") else None,
            "duration_minutes": t["duration_minutes"],
            "estimated_price_min": None,
            "estimated_price_max": None,
            "estimated_prices": [],
            "is_possible": False,
            "departure_time": t["departure_time"],
        }
        for t in results
    ]


@router.post("")
async def search(body: SearchBody, request: Request):
    if _is_mock_enabled():
        return {"trains": _mock_trains()}
    try:
        if _is_possible_trains_enabled():
            from app.services.possible_trains import get_trains_with_possible
            trains = get_trains_with_possible(body.origin, body.destination, body.date)
        else:
            trains = _trains_from_gtfs_backend(body.date, body.origin, body.destination)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Renfe no disponible: {e}")

    # Enrich estimated ranges with global price history (if any).
    try:
        trip_date = _date.fromisoformat(body.date)
        weekday = trip_date.weekday()
        conn = await get_connection(request.app.state.db_path)
        for t in trains:
            name = (t.get("name") or "").strip()
            dep_time = t.get("departure_time")
            if not name:
                continue
            gmin, gmax = await db_price_history.get_min_max(
                conn,
                body.origin,
                body.destination,
                weekday,
                name,
                dep_time,
            )
            if gmin is None and gmax is None:
                continue
            emin = t.get("estimated_price_min")
            emax = t.get("estimated_price_max")
            if gmin is not None:
                emin = gmin if emin is None else min(emin, gmin)
            if gmax is not None:
                emax = gmax if emax is None else max(emax, gmax)
            t["estimated_price_min"] = emin
            t["estimated_price_max"] = emax
    except Exception as e:
        logger.warning("search: failed to apply global price history: %s", e)

    return {"trains": trains}
