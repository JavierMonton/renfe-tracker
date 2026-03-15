"""Price event persistence."""
from typing import Any, List
import aiosqlite

async def insert_price_event(
    conn: aiosqlite.Connection, trip_id: int, price_detected: float
) -> int:
    cursor = await conn.execute(
        "INSERT INTO price_events (trip_id, price_detected, detected_at) VALUES (?, ?, datetime('now'))",
        (trip_id, price_detected),
    )
    await conn.commit()
    return cursor.lastrowid


async def list_by_trip(conn: aiosqlite.Connection, trip_id: int) -> List[dict]:
    cursor = await conn.execute(
        "SELECT id, trip_id, price_detected, detected_at FROM price_events WHERE trip_id = ? ORDER BY detected_at DESC",
        (trip_id,),
    )
    rows = await cursor.fetchall()
    return [_row_to_event(r) for r in rows]

def _row_to_event(row: Any) -> dict:
    return {
        "id": row["id"],
        "trip_id": row["trip_id"],
        "price_detected": row["price_detected"],
        "detected_at": row["detected_at"],
    }
