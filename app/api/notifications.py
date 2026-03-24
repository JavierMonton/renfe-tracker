"""Notifications API: list/create/delete notification configs.

Notification secrets (SMTP credentials, Home Assistant URL/token) are configured
via environment variables, not through the UI. Only user-facing fields are accepted
and stored here.

Browser notifications are handled client-side by polling while the app is open.
"""

from __future__ import annotations

import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from app import config as app_config
from app.db.connection import get_connection
from app.db import notifications as db_notifications

logger = logging.getLogger("renfe_tracker.notifications.api")

router = APIRouter(prefix="/notifications", tags=["notifications"])

NotificationType = Literal["email", "home_assistant", "browser"]


class CreateNotificationBody(BaseModel):
    type: NotificationType
    label: Optional[str] = None
    language: Optional[str] = None

    # Email – user-facing only (SMTP connection details come from env vars)
    email_to: Optional[str] = None
    email_subject: Optional[str] = None

    # Home Assistant – user-facing only (URL and token come from env vars)
    ha_notify_service: Optional[str] = None

    @field_validator("label", "email_to", "email_subject", "ha_notify_service", "language")
    @classmethod
    def _strip_or_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    def validate_fields(self) -> "CreateNotificationBody":
        if self.type == "email":
            if not self.email_to:
                raise ValueError("email_to is required for email notifications")
        elif self.type == "home_assistant":
            if not self.ha_notify_service:
                raise ValueError("ha_notify_service is required for Home Assistant notifications")
        return self


@router.get("/config-status")
async def get_config_status():
    """Return which notification backends are configured via environment variables."""
    return {
        "email_configured": app_config.email_configured(),
        "ha_configured": app_config.ha_configured(),
    }


@router.get("")
async def list_notifications(request: Request):
    conn = await get_connection(request.app.state.db_path)
    items = await db_notifications.list_notifications_public(conn)
    return {"notifications": items}


@router.post("")
async def create_notification(body: CreateNotificationBody, request: Request):
    try:
        body.validate_fields()
        conn = await get_connection(request.app.state.db_path)
        notification_id = await db_notifications.create_notification(
            conn,
            type=body.type,
            label=body.label,
            language=body.language,
            email_to=body.email_to,
            email_subject=body.email_subject,
            ha_notify_service=body.ha_notify_service,
        )
        return {"notification_id": notification_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("create_notification failed: %s", e)
        raise HTTPException(status_code=503, detail="Service temporarily unavailable. Please try again.")


@router.delete("/{notification_id:int}")
async def delete_notification(notification_id: int, request: Request):
    conn = await get_connection(request.app.state.db_path)
    deleted = await db_notifications.delete_notification(conn, notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"deleted": True}
