"""Notification configuration persistence (email + Home Assistant + browser notifications)."""

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
    # Email
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    smtp_username: Optional[str] = None,
    smtp_password: Optional[str] = None,
    smtp_use_starttls: Optional[bool] = None,
    email_to: Optional[str] = None,
    email_from: Optional[str] = None,
    email_subject: Optional[str] = None,
    # Home Assistant
    ha_url: Optional[str] = None,
    ha_token: Optional[str] = None,
    ha_notify_service: Optional[str] = None,
) -> int:
    if type not in NOTIFICATION_TYPES:
        raise ValueError(f"Unsupported notification type: {type}")

    cursor = await conn.execute(
        """
        INSERT INTO notifications (
            type, label,
            email_to, email_from, email_subject,
            smtp_host, smtp_port, smtp_username, smtp_password, smtp_use_starttls,
            ha_url, ha_token, ha_notify_service,
            -- Web Push columns are intentionally left NULL in browser-only mode
            webpush_vapid_subject, webpush_vapid_public_key, webpush_vapid_private_key
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            type,
            label,
            email_to,
            email_from,
            email_subject,
            smtp_host,
            smtp_port,
            smtp_username,
            smtp_password,
            int(bool(smtp_use_starttls)) if smtp_use_starttls is not None else None,
            ha_url,
            ha_token,
            ha_notify_service,
            None,
            None,
            None,
        ),
    )
    await conn.commit()
    return int(cursor.lastrowid)


async def list_notifications_public(conn: aiosqlite.Connection) -> list[dict]:
    """
    List notifications without exposing secrets (SMTP password, HA token).
    """
    cursor = await conn.execute(
        """
        SELECT
            id, type, label, created_at,
            email_to, email_from, email_subject,
            smtp_host, smtp_port, smtp_username, smtp_password,
            ha_url, ha_token, ha_notify_service
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
                # Email (sanitized)
                "email_to": r["email_to"],
                "email_from": r["email_from"],
                "email_subject": r["email_subject"],
                "smtp_host": r["smtp_host"],
                "smtp_port": r["smtp_port"],
                "smtp_username": "******" if r["smtp_username"] else None,
                "has_smtp_password": bool(r["smtp_password"]),
                # HA (sanitized)
                "ha_url": r["ha_url"],
                "notify_service": r["ha_notify_service"],
                "has_ha_token": bool(r["ha_token"]),
            }
        )
    return out


async def list_notifications_for_dispatch(conn: aiosqlite.Connection) -> list[dict]:
    """
    Internal: list email + Home Assistant notifications including secrets needed for delivery.
    Browser notifications are handled client-side by polling.
    """
    cursor = await conn.execute(
        """
        SELECT
            id, type, label, created_at,
            email_to, email_from, email_subject,
            smtp_host, smtp_port, smtp_username, smtp_password, smtp_use_starttls,
            ha_url, ha_token, ha_notify_service
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
                "created_at": r["created_at"],
                # Email (including password)
                "email_to": r["email_to"],
                "email_from": r["email_from"],
                "email_subject": r["email_subject"],
                "smtp_host": r["smtp_host"],
                "smtp_port": r["smtp_port"],
                "smtp_username": r["smtp_username"],
                "smtp_password": r["smtp_password"],
                "smtp_use_starttls": bool(r["smtp_use_starttls"]) if r["smtp_use_starttls"] is not None else True,
                # HA (including token)
                "ha_url": r["ha_url"],
                "ha_token": r["ha_token"],
                "ha_notify_service": r["ha_notify_service"],
            }
        )
    return out


async def delete_notification(conn: aiosqlite.Connection, notification_id: int) -> bool:
    cursor = await conn.execute("DELETE FROM notifications WHERE id = ?", (notification_id,))
    await conn.commit()
    return bool(cursor.rowcount)

