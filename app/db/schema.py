"""SQLite schema: trips, price_events, price samples, and notifications."""
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
    departure_time TEXT,
    last_price_changed_at TEXT,
    last_price_change_direction TEXT
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

PRICE_SAMPLES_TABLE = """
CREATE TABLE IF NOT EXISTS price_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL REFERENCES trips(id) ON DELETE CASCADE,
    price REAL NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE(trip_id, price)
)
"""

PRICE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    weekday INTEGER NOT NULL,
    train_identifier TEXT NOT NULL,
    departure_time TEXT,
    price REAL NOT NULL,
    last_seen_at TEXT NOT NULL,
    UNIQUE(origin, destination, weekday, train_identifier, departure_time, price)
)
"""

NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    label TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),

    -- Email
    smtp_host TEXT,
    smtp_port INTEGER,
    smtp_username TEXT,
    smtp_password TEXT,
    smtp_use_starttls INTEGER,
    email_to TEXT,
    email_from TEXT,
    email_subject TEXT,

    -- Home Assistant
    ha_url TEXT,
    ha_token TEXT,
    ha_notify_service TEXT,

    -- Web Push
    webpush_vapid_subject TEXT,
    webpush_vapid_public_key TEXT,
    webpush_vapid_private_key TEXT
)
"""

PUSH_SUBSCRIPTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id INTEGER NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    keys_auth TEXT NOT NULL,
    keys_p256dh TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at TEXT NOT NULL,
    UNIQUE(notification_id, endpoint)
)
"""

# New columns added after initial schema (for existing DBs without them)
TRIPS_ALTER_COLUMNS = [
    ("initial_price", "REAL"),
    ("last_checked_at", "TEXT"),
    ("departure_time", "TEXT"),
    ("last_price_changed_at", "TEXT"),
    ("last_price_change_direction", "TEXT"),
]

NOTIFICATIONS_ALTER_COLUMNS = [
    ("smtp_use_starttls", "INTEGER"),
    ("ha_notify_service", "TEXT"),
    ("webpush_vapid_subject", "TEXT"),
    ("webpush_vapid_public_key", "TEXT"),
    ("webpush_vapid_private_key", "TEXT"),
    ("language", "TEXT"),
]


async def _add_column_if_missing(conn: aiosqlite.Connection, table: str, column: str, col_type: str) -> None:
    cursor = await conn.execute(f"PRAGMA table_info({table})")
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
        await conn.execute(PRICE_SAMPLES_TABLE)
        await conn.execute(PRICE_HISTORY_TABLE)
        await conn.execute(NOTIFICATIONS_TABLE)
        await conn.execute(PUSH_SUBSCRIPTIONS_TABLE)
        await conn.commit()
        for col, typ in TRIPS_ALTER_COLUMNS:
            await _add_column_if_missing(conn, "trips", col, typ)
        for col, typ in NOTIFICATIONS_ALTER_COLUMNS:
            await _add_column_if_missing(conn, "notifications", col, typ)
        await conn.commit()
