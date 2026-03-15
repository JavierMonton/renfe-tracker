"""Search API: options (origins/destinations) and search (real Renfe trains)."""
import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.renfe_client import (
    RenfeBrowserNotFoundError,
    RenfeClientError,
    RenfeTimeoutError,
    search_trains,
)

router = APIRouter(prefix="/search", tags=["search"])


def _use_gtfs_backend() -> bool:
    """Use in-process Renfe library (GTFS + DWR) instead of Playwright. Default: True."""
    return os.environ.get("RENFE_BACKEND", "gtfs").lower() in ("gtfs", "1", "true")

# Static options for frontend dropdowns. Must include at least Zaragoza, Calatayud, Tafalla (Phase 1.1).
# Same list for origins and destinations; backend maps to Renfe codes in renfe_client when needed.
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


def _mock_trains() -> list:
    """Fixed example trains when RENFE_MOCK=1 or RENFE_USE_MOCK=true (no Playwright)."""
    return [
        {"name": "AVE", "price": 45.50, "duration_minutes": 90, "estimated_price_min": None, "estimated_price_max": None},
        {"name": "Avlo", "price": 25.00, "duration_minutes": 95, "estimated_price_min": None, "estimated_price_max": None},
        {"name": "Alvia", "price": 38.20, "duration_minutes": 120, "estimated_price_min": None, "estimated_price_max": None},
    ]


def _trains_from_gtfs_backend(date: str, origin: str, destination: str) -> list:
    """Use vendored renfe_mcp (GTFS + DWR) to get trains with prices. Returns same shape as Playwright."""
    from app.renfe_lib import get_train_prices
    results = get_train_prices(origin, destination, date, page=1, per_page=50)
    return [
        {
            "name": t["train_type"],
            "price": t["price"] if t.get("available") else None,
            "duration_minutes": t["duration_minutes"],
            "estimated_price_min": None,
            "estimated_price_max": None,
        }
        for t in results
    ]


@router.post("")
async def search(body: SearchBody):
    if _is_mock_enabled():
        return {"trains": _mock_trains()}
    if _use_gtfs_backend():
        try:
            trains = _trains_from_gtfs_backend(body.date, body.origin, body.destination)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Renfe no disponible: {e}")
        return {"trains": trains}
    try:
        trains = await search_trains(body.date, body.origin, body.destination)
    except RenfeBrowserNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Renfe no disponible: navegador no instalado. Ejecuta 'playwright install chromium' o usa Docker.",
        )
    except RenfeTimeoutError:
        raise HTTPException(status_code=503, detail="Renfe tardó demasiado en responder.")
    except RenfeClientError as e:
        msg = str(e).lower()
        if "executable doesn't exist" in msg or "playwright" in msg:
            detail = "Renfe no disponible: navegador no instalado. Ejecuta 'playwright install chromium' o usa Docker."
        elif "tardó demasiado" in msg:
            detail = "Renfe tardó demasiado en responder."
        else:
            detail = str(e)
        raise HTTPException(status_code=503, detail=detail)
    return {"trains": trains}
