"""Trip persistence."""
from typing import Any, List, Optional
import aiosqlite

_TRIP_COLUMNS = (
    "id, origin, destination, date, train_identifier, check_interval_minutes, created_at, "
    "initial_price, last_checked_at, departure_time, "
    "last_price_changed_at, last_price_change_direction, "
    "COALESCE(("
    "SELECT pe.price_detected FROM price_events pe "
    "WHERE pe.trip_id = trips.id "
    "ORDER BY pe.detected_at DESC "
    "LIMIT 1"
    "), initial_price) AS current_price"
)


async def list_trips(conn: aiosqlite.Connection) -> List[dict]:
    cursor = await conn.execute(
        f"SELECT {_TRIP_COLUMNS} FROM trips ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    return [_row_to_trip(r) for r in rows]


async def get_trip(conn: aiosqlite.Connection, trip_id: int) -> Optional[dict]:
    cursor = await conn.execute(
        f"SELECT {_TRIP_COLUMNS} FROM trips WHERE id = ?",
        (trip_id,),
    )
    row = await cursor.fetchone()
    return _row_to_trip(row) if row else None


async def create_trip(
    conn: aiosqlite.Connection,
    origin: str,
    destination: str,
    date: str,
    train_identifier: str,
    check_interval_minutes: int,
    *,
    initial_price: Optional[float] = None,
    departure_time: Optional[str] = None,
) -> int:
    cursor = await conn.execute(
        """INSERT INTO trips (origin, destination, date, train_identifier, check_interval_minutes, initial_price, last_checked_at, departure_time)
           VALUES (?, ?, ?, ?, ?, ?, NULL, ?)""",
        (origin, destination, date, train_identifier, check_interval_minutes, initial_price, departure_time),
    )
    await conn.commit()
    return cursor.lastrowid


async def delete_trip(conn: aiosqlite.Connection, trip_id: int) -> bool:
    """Delete a trip by id. price_events are removed by CASCADE. Returns True if a row was deleted."""
    cursor = await conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    await conn.commit()
    return cursor.rowcount > 0


async def update_last_checked_at(conn: aiosqlite.Connection, trip_id: int, datetime_str: str) -> None:
    await conn.execute(
        "UPDATE trips SET last_checked_at = ? WHERE id = ?",
        (datetime_str, trip_id),
    )
    await conn.commit()


async def update_last_price_change(
    conn: aiosqlite.Connection,
    trip_id: int,
    *,
    direction: Optional[str],
    datetime_str: str,
) -> None:
    await conn.execute(
        """
        UPDATE trips
        SET last_price_change_direction = ?,
            last_price_changed_at = ?
        WHERE id = ?
        """,
        (direction, datetime_str, trip_id),
    )
    await conn.commit()


def _row_to_trip(row: Any) -> dict:
    return {
        "id": row["id"],
        "origin": row["origin"],
        "destination": row["destination"],
        "date": row["date"],
        "train_identifier": row["train_identifier"],
        "check_interval_minutes": row["check_interval_minutes"],
        "created_at": row["created_at"],
        "initial_price": row["initial_price"] if row["initial_price"] is not None else None,
        "last_checked_at": row["last_checked_at"],
        "departure_time": row["departure_time"],
        "current_price": row["current_price"] if row["current_price"] is not None else None,
        "last_price_changed_at": row["last_price_changed_at"],
        "last_price_change_direction": row["last_price_change_direction"],
    }
