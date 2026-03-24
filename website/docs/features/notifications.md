---
id: notifications
sidebar_position: 4
title: Notifications
---

# Notifications

Whenever a tracked trip changes price, Renfe Tracker can notify you immediately. Three notification systems are supported, and you can configure as many as you like — all active notifications fire on every price change.

## Notification message format

Every notification (regardless of type) contains:

```
Trip - {origin} → {destination}, {departure_time}, changed price from {old_price} to {new_price}
```

For example:

> Trip - MADRID → BARCELONA, 07:00, changed price from €45.10 to €39.50

---

## Email {#email}

Sends an email via SMTP whenever a price changes.

### Server-side setup (environment variables)

Configure the SMTP server connection when starting the container:

```yaml
environment:
  SMTP_HOST: smtp.gmail.com
  SMTP_PORT: 587
  SMTP_USERNAME: alerts@example.com
  SMTP_PASSWORD: your-app-password
  SMTP_USE_STARTTLS: "true"
  SMTP_FROM: alerts@example.com   # optional, defaults to SMTP_USERNAME
```

### Per-notification setup (UI)

After configuring the server connection, go to **Notifications → Add notification → Email** and fill in:

- **Recipient address** — where the alerts will be sent.
- **Subject** — email subject line (you can include anything you like).

### Gmail tip

If you use Gmail, generate an **App Password** (not your regular password) in your Google account security settings and use that as `SMTP_PASSWORD`. Make sure 2-factor authentication is enabled on the account.

---

## Home Assistant {#home-assistant}

Posts a notification to a Home Assistant notify service whenever a price changes.

### Server-side setup (environment variables)

```yaml
environment:
  HA_URL: http://homeassistant.local:8123
  HA_TOKEN: your-long-lived-access-token
```

Generate the token in Home Assistant: **Profile → Long-lived access tokens → Create token**.

### Per-notification setup (UI)

Go to **Notifications → Add notification → Home Assistant** and enter:

- **Service name** — the HA notify service to call, e.g. `mobile_app_my_phone` or `notify`.

The app calls `POST /api/services/notify/{service}` on your HA instance with the price change message as the body.

### Automations

Once the notification lands in Home Assistant, you can attach any HA automation to it — send it to a Telegram bot, flash a light, trigger a script, etc.

---

## Browser notifications {#browser}

Sends in-browser notifications via the Web Push API so you get alerts even when the Renfe Tracker tab is not open (as long as the browser is running).

### How it works

The browser notification system works differently from the other two:

- A background script (`BrowserNotificationsManager`) runs in the browser and polls the `/trips` API every 60 seconds.
- When it detects a new price event since its last check, it fires a browser notification using the [Notifications API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API).

### Setup

1. Go to **Notifications → Add notification → Browser**.
2. Click **Enable browser notifications** — the browser will ask for permission.
3. Grant permission.

That's it. Notifications will appear as OS-level alerts from your browser.

:::note
Browser notifications require the Renfe Tracker tab to have been opened at least once in the browser session so the polling script can start. Notifications are delivered as long as the browser is running; they do not survive a browser restart without re-opening the tab.
:::

---

## Managing notifications

Go to **Notifications** in the top navigation to see all configured notification channels. You can delete any of them from there. Adding a new one uses the same **Add notification** flow described above.

All notification dispatches are **best-effort**: if delivery fails (SMTP error, HA unreachable, etc.) the error is logged but the scheduler job continues normally — a failed notification never stops price checking.
