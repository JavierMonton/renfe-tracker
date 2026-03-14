"""Search API: options (origins/destinations) and search (mock trains)."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.renfe_client import search_trains

router = APIRouter(prefix="/search", tags=["search"])

# Static options for frontend dropdowns (mock/sample).
ORIGINS = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Málaga"]
DESTINATIONS = ["Madrid", "Barcelona", "Valencia", "Sevilla", "Bilbao", "Málaga"]

class SearchBody(BaseModel):
    date: str
    origin: str
    destination: str

@router.get("/options")
async def get_search_options():
    return {"origins": ORIGINS, "destinations": DESTINATIONS}

@router.post("")
async def search(body: SearchBody):
    trains = search_trains(body.date, body.origin, body.destination)
    return {"trains": trains}
