from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.db.schema import init_db
from app.services.notifications import build_price_change_summary


def test_build_price_change_summary_format() -> None:
    summary = build_price_change_summary(
        origin="Madrid",
        destination="Zaragoza",
        departure_time="09:30",
        old_price=10.0,
        new_price=12.5,
    )
    assert summary == "Price changed: Madrid → Zaragoza, dep. 09:30. Price: €10.00 → €12.50"


def test_build_price_change_summary_old_price_unknown() -> None:
    summary = build_price_change_summary(
        origin="Madrid",
        destination="Zaragoza",
        departure_time=None,
        old_price=None,
        new_price=12.5,
    )
    assert summary == "Price changed: Madrid → Zaragoza, dep. N/A. Price: N/A → €12.50"


def test_notifications_email_crud(client: TestClient) -> None:
    payload = {
        "type": "email",
        "label": "Test email",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "user",
        "smtp_password": "pass",
        "smtp_use_starttls": True,
        "email_to": "to@example.com",
        "email_from": "from@example.com",
        "email_subject": "Price change alert",
    }

    r = client.post("/api/notifications", json=payload)
    assert r.status_code == 200
    notification_id = r.json()["notification_id"]

    r2 = client.get("/api/notifications")
    assert r2.status_code == 200
    notifications = r2.json().get("notifications", [])

    notif = next(n for n in notifications if n["id"] == notification_id)
    assert notif["type"] == "email"
    assert notif["email_to"] == "to@example.com"
    assert "smtp_password" not in notif
    assert "ha_token" not in notif

    r3 = client.delete(f"/api/notifications/{notification_id}")
    assert r3.status_code == 200
    assert r3.json()["deleted"] is True

    r4 = client.get("/api/notifications")
    notifications2 = r4.json().get("notifications", [])
    assert all(n["id"] != notification_id for n in notifications2)


def test_notifications_browser_crud(client: TestClient) -> None:
    payload = {
        "type": "browser",
        "label": "Test browser",
    }

    r = client.post("/api/notifications", json=payload)
    assert r.status_code == 200
    notification_id = r.json()["notification_id"]

    r2 = client.get("/api/notifications")
    assert r2.status_code == 200
    notifications = r2.json().get("notifications", [])

    notif = next(n for n in notifications if n["id"] == notification_id)
    assert notif["type"] == "browser"
    assert notif["label"] == "Test browser"

    r3 = client.delete(f"/api/notifications/{notification_id}")
    assert r3.status_code == 200
    assert r3.json()["deleted"] is True


def test_notifications_home_assistant_crud_and_masking(client: TestClient) -> None:
    # HA URL and token are configured via env vars, not stored in DB.
    # Only ha_notify_service is user-facing and stored.
    payload = {
        "type": "home_assistant",
        "label": "HA notifier",
        "ha_notify_service": "mobile_app_javier",
    }

    created = client.post("/api/notifications", json=payload)
    assert created.status_code == 200
    notification_id = created.json()["notification_id"]

    listed = client.get("/api/notifications")
    assert listed.status_code == 200
    notifications = listed.json().get("notifications", [])

    notif = next(n for n in notifications if n["id"] == notification_id)
    assert notif["type"] == "home_assistant"
    assert notif["ha_notify_service"] == "mobile_app_javier"
    assert "ha_url" not in notif
    assert "ha_token" not in notif

    removed = client.delete(f"/api/notifications/{notification_id}")
    assert removed.status_code == 200
    assert removed.json()["deleted"] is True


def test_notifications_email_public_list_returns_masked_secret_indicators(client: TestClient) -> None:
    # SMTP credentials are configured via env vars, not stored in DB.
    # Only user-facing fields (email_to, email_subject) are stored and returned.
    payload = {
        "type": "email",
        "label": "Masked email",
        "email_to": "to@example.com",
        "email_subject": "Price change alert",
    }

    created = client.post("/api/notifications", json=payload)
    assert created.status_code == 200
    notification_id = created.json()["notification_id"]

    listed = client.get("/api/notifications")
    assert listed.status_code == 200
    notifications = listed.json().get("notifications", [])
    notif = next(n for n in notifications if n["id"] == notification_id)

    assert notif["email_to"] == "to@example.com"
    assert notif["email_subject"] == "Price change alert"
    assert "smtp_password" not in notif
    assert "smtp_username" not in notif


def test_notifications_init_db_migrates_legacy_notification_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy_notifications.sqlite"

    # Simulate an old notifications table that predates newer columns.
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            label TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            smtp_host TEXT,
            smtp_port INTEGER,
            smtp_username TEXT,
            smtp_password TEXT,
            email_to TEXT,
            email_from TEXT,
            email_subject TEXT,
            ha_url TEXT,
            ha_token TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    asyncio.run(init_db(str(db_path)))

    conn = sqlite3.connect(db_path)
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(notifications)").fetchall()
    }
    conn.close()

    assert "smtp_use_starttls" in columns
    assert "ha_notify_service" in columns
    assert "webpush_vapid_subject" in columns
    assert "webpush_vapid_public_key" in columns
    assert "webpush_vapid_private_key" in columns

