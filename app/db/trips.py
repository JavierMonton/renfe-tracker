"""Trip persistence."""
from typing import Any, List, Optional
import aiosqlite

async def list_trips(conn: aiosqlite.Connection) -> List[dict]:
    cursor = await conn.execute(
        "SELECT id, origin, destination, date, train_identifier, check_interval_minutes, created_at FROM trips ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    return [_row_to_trip(r) for r in rows]

async def get_trip(conn: aiosqlite.Connection, trip_id: int) -> Optional[dict]:
    cursor = await conn.execute(
        "SELECT id, origin, destination, date, train_identifier, check_interval_minutes, created_at FROM trips WHERE id = ?",
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
) -> int:
    cursor = await conn.execute(
        """INSERT INTO trips (origin, destination, date, train_identifier, check_interval_minutes)
           VALUES (?, ?, ?, ?, ?)""",
        (origin, destination, date, train_identifier, check_interval_minutes),
    )
    await conn.commit()
    return cursor.lastrowid

def _row_to_trip(row: Any) -> dict:
    return {
        "id": row["id"],
        "origin": row["origin"],
        "destination": row["destination"],
        "date": row["date"],
        "train_identifier": row["train_identifier"],
        "check_interval_minutes": row["check_interval_minutes"],
        "created_at": row["created_at"],
    }
