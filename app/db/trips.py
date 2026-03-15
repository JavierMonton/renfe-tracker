"""Trip persistence."""
from typing import Any, List, Optional
import aiosqlite

_TRIP_COLUMNS = (
    "id, origin, destination, date, train_identifier, check_interval_minutes, created_at, "
    "initial_price, last_checked_at, departure_time"
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


async def update_last_checked_at(conn: aiosqlite.Connection, trip_id: int, datetime_str: str) -> None:
    await conn.execute(
        "UPDATE trips SET last_checked_at = ? WHERE id = ?",
        (datetime_str, trip_id),
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
    }
