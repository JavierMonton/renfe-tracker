"""Send notifications (email + Home Assistant) on tracked trip price changes.

Browser notifications are handled client-side by polling while the app is open.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

import httpx

from app.db import notifications as db_notifications

logger = logging.getLogger("renfe_tracker.notifications")


def build_price_change_summary(
    *,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
) -> str:
    """Build message summary used across all notification systems."""

    def _fmt_price(p: Optional[float]) -> str:
        if p is None:
            return "N/A"
        return f"{p:.2f}"

    dep = departure_time.strip() if departure_time else "N/A"
    return (
        f"Trip - {origin} -> {destination}, {dep}, "
        f"changed price from {_fmt_price(old_price)} to {_fmt_price(new_price)}"
    )


async def dispatch_price_change_notifications(
    conn,
    *,
    trip_id: int,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
) -> None:
    """
    Best-effort notification dispatch.

    Failures are logged and swallowed so the scheduler never stops price tracking.
    """
    summary = build_price_change_summary(
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        old_price=old_price,
        new_price=new_price,
    )

    notifications = await db_notifications.list_notifications_for_dispatch(conn)
    if not notifications:
        return

    for n in notifications:
        ntype = n.get("type")
        try:
            if ntype == "email":
                await _send_email_notification(n, summary)
            elif ntype == "home_assistant":
                await _send_home_assistant_notification(n, summary)
            else:
                # browser is client-side; ignore here.
                continue
        except Exception as e:
            logger.warning(
                "Notification dispatch failed (notification_id=%s, trip_id=%s, type=%s): %s",
                n.get("id"),
                trip_id,
                ntype,
                e,
                exc_info=True,
            )


async def _send_email_notification(n: dict, summary: str) -> None:
    smtp_host = n.get("smtp_host")
    smtp_port = n.get("smtp_port") or 587
    email_to = n.get("email_to")
    email_from = n.get("email_from") or email_to
    smtp_username = n.get("smtp_username")
    smtp_password = n.get("smtp_password")
    smtp_use_starttls = n.get("smtp_use_starttls")
    subject = n.get("email_subject") or "Renfe Tracker - price changed"

    if not smtp_host or not email_to or not email_from:
        logger.warning("Email notification missing host/to/from; skipping (id=%s)", n.get("id"))
        return
    if smtp_username is None or smtp_password is None:
        logger.warning("Email notification missing credentials; skipping (id=%s)", n.get("id"))
        return

    to_addrs = [a.strip() for a in str(email_to).split(",") if a.strip()]
    if not to_addrs:
        logger.warning("Email notification has empty recipient list; skipping (id=%s)", n.get("id"))
        return

    def _send_blocking() -> None:
        msg = EmailMessage()
        msg["From"] = email_from
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        msg.set_content(summary)

        with smtplib.SMTP(str(smtp_host), int(smtp_port), timeout=10) as smtp:
            smtp.ehlo()
            if bool(smtp_use_starttls):
                smtp.starttls()
                smtp.ehlo()
            smtp.login(str(smtp_username), str(smtp_password))
            smtp.send_message(msg)

    await asyncio.to_thread(_send_blocking)


async def _send_home_assistant_notification(n: dict, summary: str) -> None:
    ha_url = (n.get("ha_url") or "").rstrip("/")
    ha_token = n.get("ha_token")
    ha_notify_service = n.get("ha_notify_service")

    if not ha_url or not ha_token or not ha_notify_service:
        logger.warning(
            "Home Assistant notification missing ha_url/ha_token/ha_notify_service; skipping (id=%s)",
            n.get("id"),
        )
        return

    url = f"{ha_url}/api/services/notify/{ha_notify_service}"
    headers = {"Authorization": f"Bearer {ha_token}"}
    payload = {"message": summary}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"HA notify failed with status={resp.status_code}")

