"""Search API: options (origins/destinations) and search (real Renfe trains)."""
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/search", tags=["search"])

# Static options for frontend dropdowns. Must include at least Zaragoza, Calatayud, Tafalla (Phase 1.1).
# Same list for origins and destinations; backend maps to Renfe codes in renfe_lib when needed.
ORIGINS = [
    "Madrid",
    "Barcelona",
    "Valencia",
    "Sevilla",
    "Bilbao",
    "Málaga",
    "Zaragoza",
    "Calatayud",
    "Tafalla",
]
DESTINATIONS = ORIGINS

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
        {"name": "AVE", "price": 45.50, "duration_minutes": 90, "estimated_price_min": None, "estimated_price_max": None, "is_possible": False},
        {"name": "Avlo", "price": 25.00, "duration_minutes": 95, "estimated_price_min": None, "estimated_price_max": None, "is_possible": False},
        {"name": "Alvia", "price": 38.20, "duration_minutes": 120, "estimated_price_min": None, "estimated_price_max": None, "is_possible": False},
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
            "is_possible": False,
            "departure_time": t["departure_time"],
        }
        for t in results
    ]


@router.post("")
async def search(body: SearchBody):
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
    return {"trains": trains}
