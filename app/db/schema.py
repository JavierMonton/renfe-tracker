"""SQLite schema: trips and price_events."""
import aiosqlite

TRIPS_TABLE = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    date TEXT NOT NULL,
    train_identifier TEXT NOT NULL,
    check_interval_minutes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

PRICE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS price_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    price_detected REAL NOT NULL,
    detected_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(TRIPS_TABLE)
        await conn.execute(PRICE_EVENTS_TABLE)
        await conn.commit()
