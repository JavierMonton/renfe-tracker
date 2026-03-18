"""
Periodic job: for each tracked trip that is due, call Renfe for prices,
update last_checked_at, and insert a price_event only when the price changed.
"""
import logging
from datetime import datetime

from app.db.connection import get_connection
from app.db import trips as db_trips
from app.db import price_events as db_events
from app.db import price_samples as db_price_samples
from app.db import price_history as db_price_history
from app.renfe_lib import get_train_prices
from app.services.possible_trains import _reference_dates

logger = logging.getLogger(__name__)

# SQLite stores datetimes as "YYYY-MM-DD HH:MM:SS" (UTC when using datetime('now'))
_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    s = s.strip()
    if "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    try:
        return datetime.strptime(s, _DATETIME_FMT)
    except ValueError:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d")
        except ValueError:
            return None


def _is_due(trip: dict, now: datetime) -> bool:
    ref_str = trip.get("last_checked_at") or trip.get("created_at")
    ref_dt = _parse_dt(ref_str)
    if not ref_dt:
        return True
    delta_minutes = (now - ref_dt).total_seconds() / 60
    return delta_minutes >= trip["check_interval_minutes"]


def _find_matching_train(trains: list, train_identifier: str, departure_time: str | None) -> dict | None:
    """Find a train in get_train_prices results that matches trip's train_identifier and optional departure_time."""
    train_id_lower = (train_identifier or "").strip().lower()
    for t in trains:
        name = (t.get("train_type") or "").strip().lower()
        if name != train_id_lower:
            continue
        if departure_time:
            dep = (t.get("departure_time") or "").strip()
            if dep != departure_time.strip():
                continue
        return t
    return None


def _get_current_price(trip: dict, events: list) -> float | None:
    """Current price = latest price_event, or initial_price if no events."""
    if events:
        return float(events[0]["price_detected"])
    return trip.get("initial_price") if trip.get("initial_price") is not None else None


async def run_price_check(db_path: str) -> None:
    """
    Load all trips; for each due trip, call Renfe, match train, update last_checked_at
    and optionally insert a price_event when price changed.
    Errors for one trip are logged and do not block others.
    """
    conn = await get_connection(db_path)
    all_trips = await db_trips.list_trips(conn)
    now = datetime.utcnow()
    now_str = now.strftime(_DATETIME_FMT)

    due_trips = [t for t in all_trips if _is_due(t, now)]
    logger.info(
        "Running price check for tracked trips (total=%s, due=%s)",
        len(all_trips),
        len(due_trips),
    )

    for trip in all_trips:
        if not _is_due(trip, now):
            continue
        trip_id = trip["id"]
        logger.info(
            "Scheduler checking trip %s (%s -> %s, %s)",
            trip_id,
            trip["origin"],
            trip["destination"],
            trip["date"],
        )
        try:
            results = get_train_prices(
                trip["origin"],
                trip["destination"],
                trip["date"],
                page=1,
                per_page=50,
            )
        except Exception as e:
            logger.warning("get_train_prices failed for trip %s: %s", trip_id, e, exc_info=True)
            try:
                await db_trips.update_last_checked_at(conn, trip_id, now_str)
            except Exception as db_e:
                logger.warning("update_last_checked_at failed for trip %s: %s", trip_id, db_e)
            continue

        match = _find_matching_train(
            results,
            trip["train_identifier"],
            trip.get("departure_time"),
        )
        if not match:
            await db_trips.update_last_checked_at(conn, trip_id, now_str)
            continue

        price_raw = match.get("price") if match.get("available") else None
        if price_raw is None:
            await db_trips.update_last_checked_at(conn, trip_id, now_str)
            continue
        try:
            new_price = float(price_raw)
        except (TypeError, ValueError):
            await db_trips.update_last_checked_at(conn, trip_id, now_str)
            continue

        events = await db_events.list_by_trip(conn, trip_id)
        current = _get_current_price(trip, events)
        if current is not None and abs(new_price - current) < 1e-6:
            await db_trips.update_last_checked_at(conn, trip_id, now_str)
        else:
            await db_events.insert_price_event(conn, trip_id, new_price)
            direction = None
            if current is not None:
                # We only reach this branch when the price differs from the previous current price.
                if new_price < current:
                    direction = "down"
                elif new_price > current:
                    direction = "up"
            await db_trips.update_last_price_change(
                conn,
                trip_id,
                direction=direction,
                datetime_str=now_str,
            )
        await db_trips.update_last_checked_at(conn, trip_id, now_str)

        # Also record in global price history for future searches (exact trip date).
        trip_weekday = date.fromisoformat(trip["date"]).weekday()
        await db_price_history.upsert(
            conn,
            trip["origin"],
            trip["destination"],
            trip_weekday,
            trip["train_identifier"],
            trip.get("departure_time"),
            new_price,
            now_str,
        )

        # Reference dates: same weekday, other weeks – upsert prices into price_samples for estimated range
        for ref_date in _reference_dates(trip["date"]):
            try:
                ref_results = get_train_prices(
                    trip["origin"],
                    trip["destination"],
                    ref_date,
                    page=1,
                    per_page=50,
                )
            except Exception as e:
                logger.warning(
                    "get_train_prices (ref date %s) failed for trip %s: %s",
                    ref_date,
                    trip_id,
                    e,
                )
                continue
            ref_match = _find_matching_train(
                ref_results,
                trip["train_identifier"],
                trip.get("departure_time"),
            )
            if not ref_match:
                continue
            ref_price_raw = ref_match.get("price") if ref_match.get("available") else None
            if ref_price_raw is None:
                continue
            try:
                ref_price = float(ref_price_raw)
            except (TypeError, ValueError):
                continue
            await db_price_samples.upsert(conn, trip_id, ref_price, now_str)

            # And record reference-date price in global price history.
            ref_weekday = date.fromisoformat(ref_date).weekday()
            await db_price_history.upsert(
                conn,
                trip["origin"],
                trip["destination"],
                ref_weekday,
                trip["train_identifier"],
                trip.get("departure_time"),
                ref_price,
                now_str,
            )

    if due_trips:
        logger.info("Price check run finished (%s trip(s) processed)", len(due_trips))
