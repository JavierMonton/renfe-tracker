"""SQLite schema: trips and price_events."""
import logging
import aiosqlite

logger = logging.getLogger(__name__)

TRIPS_TABLE = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    date TEXT NOT NULL,
    train_identifier TEXT NOT NULL,
    check_interval_minutes INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    initial_price REAL,
    last_checked_at TEXT,
    departure_time TEXT
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

# New columns added after initial schema (for existing DBs without them)
TRIPS_ALTER_COLUMNS = [
    ("initial_price", "REAL"),
    ("last_checked_at", "TEXT"),
    ("departure_time", "TEXT"),
]


async def _add_column_if_missing(conn: aiosqlite.Connection, table: str, column: str, col_type: str) -> None:
    cursor = await conn.execute("PRAGMA table_info(trips)" if table == "trips" else "PRAGMA table_info(price_events)")
    rows = await cursor.fetchall()
    names = [r[1] for r in rows]
    if column in names:
        return
    await conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    logger.info("Added column %s.%s", table, column)


async def init_db(db_path: str) -> None:
    async with aiosqlite.connect(db_path) as conn:
        await conn.execute(TRIPS_TABLE)
        await conn.execute(PRICE_EVENTS_TABLE)
        await conn.commit()
        for col, typ in TRIPS_ALTER_COLUMNS:
            await _add_column_if_missing(conn, "trips", col, typ)
        await conn.commit()
