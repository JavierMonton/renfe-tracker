"""Background maintenance tasks (cleanup, compaction, etc.)."""
import logging
import os
from datetime import datetime, timedelta

from app.db.connection import get_connection
from app.db import price_history as db_price_history

logger = logging.getLogger(__name__)

_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def _get_history_retention_days() -> int:
    """
    Number of days to keep global price history.

    Controlled by RENFE_PRICE_HISTORY_DAYS env var (default: 365).
    Must be >= 0. If 0, cleanup removes all history older than "now".
    """
    raw = os.environ.get("RENFE_PRICE_HISTORY_DAYS", "").strip()
    if not raw:
        return 365
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid RENFE_PRICE_HISTORY_DAYS=%r; falling back to 365", raw)
        return 365
    if value < 0:
        logger.warning("RENFE_PRICE_HISTORY_DAYS=%r is negative; using 0", raw)
        return 0
    return value


async def run_maintenance(db_path: str) -> None:
    """Run periodic maintenance tasks (called by scheduler)."""
    retention_days = _get_history_retention_days()
    if retention_days == 0:
        cutoff = datetime.utcnow()
    else:
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
    cutoff_str = cutoff.strftime(_DATETIME_FMT)

    conn = await get_connection(db_path)

    deleted = await db_price_history.delete_older_than(conn, cutoff_str)
    if deleted:
        logger.info(
            "Maintenance: deleted %s old price_history rows (retention=%s days, cutoff=%s)",
            deleted,
            retention_days,
            cutoff_str,
        )
    else:
        logger.info(
            "Maintenance: no price_history rows to delete (retention=%s days, cutoff=%s)",
            retention_days,
            cutoff_str,
        )

