"""Notification configuration persistence (email + Home Assistant + browser notifications).

Only user-facing fields are stored in the database.
SMTP credentials and Home Assistant URL/token are read from environment variables (app.config).
"""

from __future__ import annotations

import logging
from typing import Optional

import aiosqlite

logger = logging.getLogger("renfe_tracker.notifications.db")

NOTIFICATION_TYPES = ("email", "home_assistant", "browser")


async def create_notification(
    conn: aiosqlite.Connection,
    *,
    type: str,
    label: Optional[str] = None,
    language: Optional[str] = None,
    # Email (user-facing only – no SMTP credentials)
    email_to: Optional[str] = None,
    email_subject: Optional[str] = None,
    # Home Assistant (user-facing only – no URL or token)
    ha_notify_service: Optional[str] = None,
) -> int:
    if type not in NOTIFICATION_TYPES:
        raise ValueError(f"Unsupported notification type: {type}")

    cursor = await conn.execute(
        """
        INSERT INTO notifications (type, label, language, email_to, email_subject, ha_notify_service)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (type, label, language or "en", email_to, email_subject, ha_notify_service),
    )
    await conn.commit()
    return int(cursor.lastrowid)


async def list_notifications_public(conn: aiosqlite.Connection) -> list[dict]:
    """List notifications with only user-facing fields (no secrets)."""
    cursor = await conn.execute(
        """
        SELECT id, type, label, created_at, email_to, email_subject, ha_notify_service
        FROM notifications
        ORDER BY created_at DESC
        """,
    )
    rows = await cursor.fetchall()
    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "type": r["type"],
                "label": r["label"],
                "created_at": r["created_at"],
                "email_to": r["email_to"],
                "email_subject": r["email_subject"],
                "ha_notify_service": r["ha_notify_service"],
            }
        )
    return out


async def list_notifications_for_dispatch(conn: aiosqlite.Connection) -> list[dict]:
    """
    Internal: list email + Home Assistant notifications for dispatch.
    Only user-facing fields are returned; credentials come from app.config.
    """
    cursor = await conn.execute(
        """
        SELECT id, type, label, language, email_to, email_subject, ha_notify_service
        FROM notifications
        WHERE type IN ('email', 'home_assistant')
        ORDER BY created_at DESC
        """,
    )
    rows = await cursor.fetchall()
    out: list[dict] = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "type": r["type"],
                "label": r["label"],
                "language": r["language"] or "en",
                "email_to": r["email_to"],
                "email_subject": r["email_subject"],
                "ha_notify_service": r["ha_notify_service"],
            }
        )
    return out


async def delete_notification(conn: aiosqlite.Connection, notification_id: int) -> bool:
    cursor = await conn.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
    await conn.commit()
    return bool(cursor.rowcount)
