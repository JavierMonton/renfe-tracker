"""Application-wide configuration from environment variables.

Notification secrets (SMTP credentials, Home Assistant token/URL) are set here
and never accepted through the UI or stored in the database.
"""

from __future__ import annotations

import os

# ---------------------------------------------------------------------------
# Email (SMTP) – connection-level settings
# ---------------------------------------------------------------------------
SMTP_HOST: str | None = os.getenv("SMTP_HOST")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
# Any value other than "0", "false", or "no" means STARTTLS is enabled (default on).
SMTP_USE_STARTTLS: bool = os.getenv("SMTP_USE_STARTTLS", "true").lower() not in ("0", "false", "no")
# Sender address; falls back to SMTP_USERNAME when not set.
SMTP_FROM: str | None = os.getenv("SMTP_FROM") or SMTP_USERNAME

# ---------------------------------------------------------------------------
# Home Assistant
# ---------------------------------------------------------------------------
HA_URL: str | None = os.getenv("HA_URL")
HA_TOKEN: str | None = os.getenv("HA_TOKEN")


def email_configured() -> bool:
    """Return True when the minimum SMTP env vars are present."""
    return bool(SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD)


def ha_configured() -> bool:
    """Return True when the minimum Home Assistant env vars are present."""
    return bool(HA_URL and HA_TOKEN)


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")


def telegram_configured() -> bool:
    """Return True when the minimum Telegram env vars are present."""
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
