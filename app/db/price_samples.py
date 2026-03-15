"""Price samples for estimated range: one row per (trip_id, price), last_seen_at updated on repeat."""
from typing import Optional, Tuple

import aiosqlite


async def upsert(conn: aiosqlite.Connection, trip_id: int, price: float, last_seen_at: str) -> None:
    """Insert (trip_id, price, last_seen_at) or update last_seen_at if (trip_id, price) already exists."""
    await conn.execute(
        """INSERT INTO price_samples (trip_id, price, last_seen_at) VALUES (?, ?, ?)
           ON CONFLICT(trip_id, price) DO UPDATE SET last_seen_at = excluded.last_seen_at""",
        (trip_id, price, last_seen_at),
    )
    await conn.commit()


async def get_min_max(conn: aiosqlite.Connection, trip_id: int) -> Tuple[Optional[float], Optional[float]]:
    """Return (min(price), max(price)) for the trip; (None, None) if no samples."""
    cursor = await conn.execute(
        "SELECT MIN(price) AS mn, MAX(price) AS mx FROM price_samples WHERE trip_id = ?",
        (trip_id,),
    )
    row = await cursor.fetchone()
    if row is None or (row[0] is None and row[1] is None):
        return (None, None)
    return (row[0], row[1])
