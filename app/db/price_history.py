"""Global price history for reusable estimated ranges.

One row per (origin, destination, weekday, train_identifier, departure_time, price),
with last_seen_at updated on repeat observations.
"""
from typing import Optional, Tuple

import aiosqlite


async def upsert(
    conn: aiosqlite.Connection,
    origin: str,
    destination: str,
    weekday: int,
    train_identifier: str,
    departure_time: Optional[str],
    price: float,
    last_seen_at: str,
) -> None:
    """Insert or update last_seen_at for a global price sample."""
    await conn.execute(
        """
        INSERT INTO price_history (
            origin, destination, weekday, train_identifier, departure_time, price, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(origin, destination, weekday, train_identifier, departure_time, price)
        DO UPDATE SET last_seen_at = excluded.last_seen_at
        """,
        (origin, destination, weekday, train_identifier, departure_time, price, last_seen_at),
    )
    await conn.commit()


async def get_min_max(
    conn: aiosqlite.Connection,
    origin: str,
    destination: str,
    weekday: int,
    train_identifier: str,
    departure_time: Optional[str],
) -> Tuple[Optional[float], Optional[float]]:
    """Return (min(price), max(price)) for the given key; (None, None) if no samples."""
    cursor = await conn.execute(
        """
        SELECT MIN(price) AS mn, MAX(price) AS mx
        FROM price_history
        WHERE origin = ?
          AND destination = ?
          AND weekday = ?
          AND train_identifier = ?
          AND departure_time IS ?
        """,
        (origin, destination, weekday, train_identifier, departure_time),
    )
    row = await cursor.fetchone()
    if row is None or (row[0] is None and row[1] is None):
        return (None, None)
    return (row[0], row[1])


async def delete_older_than(conn: aiosqlite.Connection, cutoff_iso: str) -> int:
    """Delete global price history rows with last_seen_at < cutoff_iso. Returns number of rows deleted."""
    cursor = await conn.execute(
        "DELETE FROM price_history WHERE last_seen_at < ?", (cutoff_iso,)
    )
    await conn.commit()
    return cursor.rowcount or 0

