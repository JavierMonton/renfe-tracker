"""Search API: options (origins/destinations) and search (real Renfe trains)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.renfe_client import search_trains, RenfeClientError

router = APIRouter(prefix="/search", tags=["search"])

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

@router.post("")
async def search(body: SearchBody):
    try:
        trains = search_trains(body.date, body.origin, body.destination)
    except RenfeClientError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"trains": trains}
