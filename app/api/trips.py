"""Trips API: list, create, get one."""
import logging
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

from app.db.connection import get_connection
from app.db import trips as db_trips
from app.db import price_events as db_events
from app.db import price_samples as db_price_samples
from app.db import price_history as db_price_history

logger = logging.getLogger("renfe_tracker.trips")
router = APIRouter(prefix="/trips", tags=["trips"])


class CreateTripBody(BaseModel):
    origin: str
    destination: str
    date: str
    train_identifier: str
    check_interval_minutes: int
    initial_price: Optional[float] = None
    departure_time: Optional[str] = None
    estimated_prices: Optional[List[float]] = None

    @field_validator("check_interval_minutes")
    @classmethod
    def check_interval_positive(cls, v: int) -> int:
        if v is not None and v <= 0:
            raise ValueError("check_interval_minutes must be greater than 0")
        return v

    @field_validator("origin", "destination", "train_identifier")
    @classmethod
    def required_not_blank(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("required field cannot be blank")
        return v.strip()

    @field_validator("date")
    @classmethod
    def date_not_blank(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("date cannot be blank")
        return v.strip()


@router.get("")
async def list_trips(request: Request):
    conn = await get_connection(request.app.state.db_path)
    items = await db_trips.list_trips(conn)
    for t in items:
        emin, emax = await db_price_samples.get_min_max(conn, t["id"])
        t["estimated_price_min"] = emin
        t["estimated_price_max"] = emax
    return {"trips": items}


@router.post("")
async def create_trip(body: CreateTripBody, request: Request):
    try:
        conn = await get_connection(request.app.state.db_path)
        trip_id = await db_trips.create_trip(
            conn,
            origin=body.origin,
            destination=body.destination,
            date=body.date,
            train_identifier=body.train_identifier,
            check_interval_minutes=body.check_interval_minutes,
            initial_price=body.initial_price,
            departure_time=body.departure_time,
        )
        now = datetime.utcnow()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        # Seed per-trip samples and global history with estimated prices from the initial search.
        try:
            trip_date = date.fromisoformat(body.date)
            weekday = trip_date.weekday()
        except ValueError:
            weekday = None

        for p in body.estimated_prices or []:
            try:
                price_f = float(p)
            except (TypeError, ValueError):
                continue
            await db_price_samples.upsert(conn, trip_id, price_f, now_str)
            if weekday is not None:
                await db_price_history.upsert(
                    conn,
                    body.origin,
                    body.destination,
                    weekday,
                    body.train_identifier,
                    body.departure_time,
                    price_f,
                    now_str,
                )
        trip = await db_trips.get_trip(conn, trip_id)
        emin, emax = await db_price_samples.get_min_max(conn, trip_id)
        trip["estimated_price_min"] = emin
        trip["estimated_price_max"] = emax
        return trip
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("create_trip failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again.",
        )


@router.get("/{trip_id:int}")
async def get_trip(trip_id: int, request: Request):
    conn = await get_connection(request.app.state.db_path)
    trip = await db_trips.get_trip(conn, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    emin, emax = await db_price_samples.get_min_max(conn, trip_id)
    trip["estimated_price_min"] = emin
    trip["estimated_price_max"] = emax
    events = await db_events.list_by_trip(conn, trip_id)
    return {"trip": trip, "price_events": events}


@router.delete("/{trip_id:int}")
async def delete_trip(trip_id: int, request: Request):
    """Remove a tracked trip. Stops scheduler from checking it (it only iterates over existing trips)."""
    conn = await get_connection(request.app.state.db_path)
    deleted = await db_trips.delete_trip(conn, trip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trip not found")
    return Response(status_code=204)
