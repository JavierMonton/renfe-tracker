"""Database connection helper. Call get_connection() with path from config."""
import aiosqlite
from typing import Optional

_connection: Optional[aiosqlite.Connection] = None

async def get_connection(db_path: str) -> aiosqlite.Connection:
    global _connection
    if _connection is None:
        _connection = await aiosqlite.connect(db_path)
        _connection.row_factory = aiosqlite.Row
    return _connection

async def close_connection() -> None:
    global _connection
    if _connection is not None:
        await _connection.close()
        _connection = None
