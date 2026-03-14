"""Trips API: list, create, get one."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db.connection import get_connection
from app.db import trips as db_trips
from app.db import price_events as db_events

router = APIRouter(prefix="/trips", tags=["trips"])

class CreateTripBody(BaseModel):
    origin: str
    destination: str
    date: str
    train_identifier: str
    check_interval_minutes: int

@router.get("")
async def list_trips(request: Request):
    conn = await get_connection(request.app.state.db_path)
    items = await db_trips.list_trips(conn)
    return {"trips": items}

@router.post("")
async def create_trip(body: CreateTripBody, request: Request):
    conn = await get_connection(request.app.state.db_path)
    trip_id = await db_trips.create_trip(
        conn,
        origin=body.origin,
        destination=body.destination,
        date=body.date,
        train_identifier=body.train_identifier,
        check_interval_minutes=body.check_interval_minutes,
    )
    trip = await db_trips.get_trip(conn, trip_id)
    return trip

@router.get("/{trip_id:int}")
async def get_trip(trip_id: int, request: Request):
    conn = await get_connection(request.app.state.db_path)
    trip = await db_trips.get_trip(conn, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    events = await db_events.list_by_trip(conn, trip_id)
    return {"trip": trip, "price_events": events}
