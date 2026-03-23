"""Notifications API: list/create/delete notification configs.

Browser notifications are handled client-side by polling while the app is open.
Backend dispatch includes only email (SMTP) and Home Assistant.
"""

from __future__ import annotations

import logging
from typing import Any, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, field_validator

from app.db.connection import get_connection
from app.db import notifications as db_notifications

logger = logging.getLogger("renfe_tracker.notifications.api")

router = APIRouter(prefix="/notifications", tags=["notifications"])

NotificationType = Literal["email", "home_assistant", "browser"]


class CreateNotificationBody(BaseModel):
    type: NotificationType
    label: Optional[str] = None

    # Email
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_starttls: bool = True
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    email_subject: Optional[str] = None

    # Home Assistant
    ha_url: Optional[str] = None
    ha_token: Optional[str] = None
    ha_notify_service: Optional[str] = None

    @field_validator(
        "label",
        "smtp_host",
        "smtp_username",
        "smtp_password",
        "email_to",
        "email_from",
        "email_subject",
        "ha_url",
        "ha_token",
        "ha_notify_service",
    )
    @classmethod
    def _strip_or_none(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

    def validate(self) -> "CreateNotificationBody":
        if self.type == "email":
            if not self.smtp_host:
                raise ValueError("smtp_host is required for email notifications")
            if self.smtp_port <= 0:
                raise ValueError("smtp_port must be > 0")
            if not self.smtp_username or not self.smtp_password:
                raise ValueError("smtp_username and smtp_password are required for email notifications")
            if not self.email_to:
                raise ValueError("email_to is required for email notifications")
            # email_from is optional; dispatcher will default it to email_to.
        elif self.type == "home_assistant":
            if not self.ha_url:
                raise ValueError("ha_url is required for Home Assistant notifications")
            if not self.ha_token:
                raise ValueError("ha_token is required for Home Assistant notifications")
            if not self.ha_notify_service:
                raise ValueError("ha_notify_service is required for Home Assistant notifications")
        elif self.type == "browser":
            # No extra fields.
            pass
        else:  # pragma: no cover
            raise ValueError(f"Unsupported notification type: {self.type}")

        return self


@router.get("")
async def list_notifications(request: Request):
    conn = await get_connection(request.app.state.db_path)
    items = await db_notifications.list_notifications_public(conn)
    return {"notifications": items}


@router.post("")
async def create_notification(body: CreateNotificationBody, request: Request):
    try:
        body.validate()
        conn = await get_connection(request.app.state.db_path)
        notification_id = await db_notifications.create_notification(
            conn,
            type=body.type,
            label=body.label,
            # Email
            smtp_host=body.smtp_host,
            smtp_port=body.smtp_port,
            smtp_username=body.smtp_username,
            smtp_password=body.smtp_password,
            smtp_use_starttls=body.smtp_use_starttls,
            email_to=body.email_to,
            email_from=body.email_from,
            email_subject=body.email_subject,
            # HA
            ha_url=body.ha_url,
            ha_token=body.ha_token,
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

