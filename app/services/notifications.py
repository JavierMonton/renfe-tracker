"""Send notifications (email + Home Assistant) on tracked trip price changes.

Browser notifications are handled client-side by polling while the app is open.
SMTP and Home Assistant credentials are read from environment variables (app.config),
not from the database.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Optional

import httpx

from app import config
from app.db import notifications as db_notifications
from app.i18n import t

logger = logging.getLogger("renfe_tracker.notifications")


def build_price_change_summary(
    *,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
    direction: Optional[str] = None,
    trip_date: Optional[str] = None,
    train_identifier: Optional[str] = None,
    lang: str = "en",
) -> str:
    """Build plain-text message summary used across all notification systems."""

    def _fmt_price(p: Optional[float]) -> str:
        return "N/A" if p is None else f"€{p:.2f}"

    dep = departure_time.strip() if departure_time else "N/A"
    date_part = t(lang, "emailNotif.plainDatePart", date=trip_date) if trip_date else ""
    train_part = f" ({train_identifier})" if train_identifier else ""
    dep_prefix = t(lang, "emailNotif.plainDepPrefix")

    if direction == "down" and old_price is not None:
        diff = old_price - new_price
        verb = t(lang, "emailNotif.plainVerbDown", amount=f"{diff:.2f}")
    elif direction == "up" and old_price is not None:
        diff = new_price - old_price
        verb = t(lang, "emailNotif.plainVerbUp", amount=f"{diff:.2f}")
    else:
        verb = t(lang, "emailNotif.plainVerbChanged")

    return t(
        lang,
        "emailNotif.plainSummary",
        verb=verb,
        origin=origin,
        destination=destination,
        datePart=date_part,
        depPrefix=dep_prefix,
        departure=dep,
        trainPart=train_part,
        oldPrice=_fmt_price(old_price),
        newPrice=_fmt_price(new_price),
    )


def _build_email_html(
    *,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
    direction: Optional[str],
    trip_date: Optional[str],
    train_identifier: Optional[str],
    lang: str = "en",
) -> str:
    """Build an HTML email body for a price change notification."""

    dep = departure_time.strip() if departure_time else "N/A"
    date_str = trip_date or ""
    train_str = train_identifier or ""

    def _fmt(p: Optional[float]) -> str:
        return "N/A" if p is None else f"€{p:.2f}"

    # Direction-specific copy (translated)
    if direction == "down":
        direction_label = t(lang, "emailNotif.badgeDown")
        direction_heading = t(lang, "emailNotif.headingDown")
        badge_bg = "#dcfce7"
        badge_color = "#166534"
        new_price_color = "#16a34a"
    elif direction == "up":
        direction_label = t(lang, "emailNotif.badgeUp")
        direction_heading = t(lang, "emailNotif.headingUp")
        badge_bg = "#fee2e2"
        badge_color = "#991b1b"
        new_price_color = "#dc2626"
    else:
        direction_label = t(lang, "emailNotif.badgeChanged")
        direction_heading = t(lang, "emailNotif.headingChanged")
        badge_bg = "#e0e7ff"
        badge_color = "#3730a3"
        new_price_color = "#374151"

    # Difference row (only when we have an old price)
    if old_price is not None:
        diff = new_price - old_price
        diff_sign = "+" if diff >= 0 else "−"
        diff_abs = abs(diff)
        diff_color = "#16a34a" if diff < 0 else "#dc2626"
        diff_text = t(lang, "emailNotif.diffLabel", diff=f"{diff_sign}€{diff_abs:.2f}")
        diff_row = f"""
              <tr>
                <td colspan="3" style="text-align:center;padding-top:12px;">
                  <span style="font-size:14px;font-weight:600;color:{diff_color};">
                    {diff_text}
                  </span>
                </td>
              </tr>"""
    else:
        diff_row = ""

    meta_parts = []
    dep_prefix = t(lang, "emailNotif.plainDepPrefix")
    if date_str:
        meta_parts.append(date_str)
    if dep != "N/A":
        meta_parts.append(f"{dep_prefix} {dep}")
    if train_str:
        meta_parts.append(train_str)
    meta_line = " · ".join(meta_parts) if meta_parts else "&nbsp;"

    label_previous = t(lang, "emailNotif.labelPrevious")
    label_new_price = t(lang, "emailNotif.labelNewPrice")
    footer_text = t(lang, "emailNotif.footer")

    old_price_cell = (
        f"""<td style="text-align:center;padding:0 16px 0 0;">
                  <p style="margin:0;font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em;">{label_previous}</p>
                  <p style="margin:4px 0 0;font-size:22px;font-weight:700;color:#9ca3af;text-decoration:line-through;">{_fmt(old_price)}</p>
                </td>
                <td style="text-align:center;padding:0 12px;font-size:22px;color:#d1205c;">→</td>"""
        if old_price is not None
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:24px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.12);">
        <!-- Header gradient -->
        <tr>
          <td style="background:linear-gradient(90deg,#d1205c 0%,#a03078 35%,#6d2d82 65%,#4a2b7f 100%);padding:20px 28px;">
            <span style="font-size:18px;font-weight:700;color:#ffffff;letter-spacing:-0.01em;">Renfe Tracker</span>
          </td>
        </tr>
        <!-- Alert label + heading -->
        <tr>
          <td style="padding:28px 28px 0;">
            <span style="display:inline-block;background:{badge_bg};color:{badge_color};border-radius:9999px;padding:3px 12px;font-size:13px;font-weight:600;">{direction_label}</span>
            <h1 style="margin:10px 0 0;font-size:20px;font-weight:700;color:#111827;">{direction_heading}</h1>
          </td>
        </tr>
        <!-- Route + meta -->
        <tr>
          <td style="padding:16px 28px 0;">
            <p style="margin:0;font-size:17px;font-weight:600;color:#1f2937;">
              {origin}&nbsp;<span style="color:#d1205c;">→</span>&nbsp;{destination}
            </p>
            <p style="margin:4px 0 0;font-size:13px;color:#6b7280;">{meta_line}</p>
          </td>
        </tr>
        <!-- Price block -->
        <tr>
          <td style="padding:20px 28px;">
            <table cellpadding="0" cellspacing="0" style="width:100%;background:#f9fafb;border-radius:8px;padding:18px 12px;">
              <tr>
                {old_price_cell}
                <td style="text-align:center;padding:0;">
                  <p style="margin:0;font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:0.05em;">{label_new_price}</p>
                  <p style="margin:4px 0 0;font-size:28px;font-weight:700;color:{new_price_color};">{_fmt(new_price)}</p>
                </td>
              </tr>{diff_row}
            </table>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="padding:0 28px 24px;border-top:1px solid #f3f4f6;">
            <p style="margin:16px 0 0;font-size:12px;color:#9ca3af;">{footer_text}</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _build_telegram_html(
    *,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
    direction: Optional[str],
    trip_date: Optional[str],
    train_identifier: Optional[str],
    lang: str = "en",
) -> str:
    """Build an HTML message for Telegram using its supported subset (<b>, <i>, <s>, <code>)."""

    def _fmt(p: Optional[float]) -> str:
        return "N/A" if p is None else f"€{p:.2f}"

    # Direction heading
    if direction == "down":
        heading = t(lang, "emailNotif.badgeDown")
    elif direction == "up":
        heading = t(lang, "emailNotif.badgeUp")
    else:
        heading = t(lang, "emailNotif.badgeChanged")

    # Route line
    route = f"<b>{origin}</b> → <b>{destination}</b>"

    # Meta line: date | departure | train
    meta_parts: list[str] = []
    if trip_date:
        meta_parts.append(trip_date)
    dep = departure_time.strip() if departure_time else None
    if dep:
        meta_parts.append(dep)
    if train_identifier:
        meta_parts.append(train_identifier)
    meta_line = " | ".join(meta_parts) if meta_parts else ""

    # Price line
    if old_price is not None:
        diff = new_price - old_price
        diff_sign = "+" if diff >= 0 else "−"
        price_line = f"<s>{_fmt(old_price)}</s> → <b>{_fmt(new_price)}</b> ({diff_sign}€{abs(diff):.2f})"
    else:
        price_line = f"<b>{_fmt(new_price)}</b>"

    # Assemble
    lines = [f"<b>{heading}</b>", "", route]
    if meta_line:
        lines.append(meta_line)
    lines.append("")
    lines.append(price_line)
    return "\n".join(lines)


async def dispatch_price_change_notifications(
    conn,
    *,
    trip_id: int,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
    direction: Optional[str] = None,
    trip_date: Optional[str] = None,
    train_identifier: Optional[str] = None,
) -> None:
    """
    Best-effort notification dispatch.

    Failures are logged and swallowed so the scheduler never stops price tracking.
    """
    notifications = await db_notifications.list_notifications_for_dispatch(conn)
    if not notifications:
        return

    for n in notifications:
        ntype = n.get("type")
        lang = n.get("language") or "en"
        try:
            summary = build_price_change_summary(
                origin=origin,
                destination=destination,
                departure_time=departure_time,
                old_price=old_price,
                new_price=new_price,
                direction=direction,
                trip_date=trip_date,
                train_identifier=train_identifier,
                lang=lang,
            )
            if ntype == "email":
                await _send_email_notification(
                    n,
                    summary,
                    origin=origin,
                    destination=destination,
                    departure_time=departure_time,
                    old_price=old_price,
                    new_price=new_price,
                    direction=direction,
                    trip_date=trip_date,
                    train_identifier=train_identifier,
                    lang=lang,
                )
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


async def _send_email_notification(
    n: dict,
    summary: str,
    *,
    origin: str,
    destination: str,
    departure_time: Optional[str],
    old_price: Optional[float],
    new_price: float,
    direction: Optional[str],
    trip_date: Optional[str],
    train_identifier: Optional[str],
    lang: str = "en",
) -> None:
    smtp_host = config.SMTP_HOST
    smtp_port = config.SMTP_PORT
    smtp_username = config.SMTP_USERNAME
    smtp_password = config.SMTP_PASSWORD
    smtp_use_starttls = config.SMTP_USE_STARTTLS
    email_from = config.SMTP_FROM

    email_to = n.get("email_to")

    # Build subject: use user-provided custom subject if set, otherwise auto-generate (translated)
    configured_subject = n.get("email_subject")
    if configured_subject:
        subject = configured_subject
    elif direction == "down":
        subject = t(lang, "emailNotif.subjectDown", origin=origin, destination=destination)
    elif direction == "up":
        subject = t(lang, "emailNotif.subjectUp", origin=origin, destination=destination)
    else:
        subject = t(lang, "emailNotif.subjectChanged", origin=origin, destination=destination)

    if not smtp_host or not smtp_username or not smtp_password:
        logger.warning(
            "Email notification skipped: SMTP_HOST / SMTP_USERNAME / SMTP_PASSWORD not configured "
            "(notification_id=%s). Set these environment variables to enable email alerts.",
            n.get("id"),
        )
        return
    if not email_to:
        logger.warning("Email notification missing email_to; skipping (id=%s)", n.get("id"))
        return

    to_addrs = [a.strip() for a in str(email_to).split(",") if a.strip()]
    if not to_addrs:
        logger.warning("Email notification has empty recipient list; skipping (id=%s)", n.get("id"))
        return

    html_body = _build_email_html(
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        old_price=old_price,
        new_price=new_price,
        direction=direction,
        trip_date=trip_date,
        train_identifier=train_identifier,
        lang=lang,
    )

    def _send_blocking() -> None:
        msg = EmailMessage()
        msg["From"] = email_from or smtp_username
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = subject
        # Plain-text fallback first, then HTML alternative
        msg.set_content(summary)
        msg.add_alternative(html_body, subtype="html")

        with smtplib.SMTP(str(smtp_host), int(smtp_port), timeout=10) as smtp:
            smtp.ehlo()
            if smtp_use_starttls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(str(smtp_username), str(smtp_password))
            smtp.send_message(msg)

    await asyncio.to_thread(_send_blocking)


async def _send_home_assistant_notification(n: dict, summary: str) -> None:
    ha_url = (config.HA_URL or "").rstrip("/")
    ha_token = config.HA_TOKEN
    ha_notify_service = n.get("ha_notify_service")

    if not ha_url or not ha_token:
        logger.warning(
            "Home Assistant notification skipped: HA_URL / HA_TOKEN not configured "
            "(notification_id=%s). Set these environment variables to enable HA alerts.",
            n.get("id"),
        )
        return
    if not ha_notify_service:
        logger.warning(
            "Home Assistant notification missing ha_notify_service; skipping (id=%s)", n.get("id")
        )
        return

    url = f"{ha_url}/api/services/notify/{ha_notify_service}"
    headers = {"Authorization": f"Bearer {ha_token}"}
    payload = {"message": summary}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"HA notify failed with status={resp.status_code}")
