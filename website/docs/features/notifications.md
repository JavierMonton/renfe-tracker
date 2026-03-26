---
id: notifications
sidebar_position: 4
title: Notifications
---

# Notifications

Whenever a tracked trip changes price, Renfe Tracker can notify you immediately. Four notification systems are supported, and you can configure as many as you like — all active notifications fire on every price change.

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

## Telegram {#telegram}

Sends a formatted message to a Telegram chat, group, or channel via a bot whenever a price changes.

### Server-side setup (environment variables)

Create a bot through [@BotFather](https://t.me/BotFather) to get a bot token, then obtain the chat ID of the target chat (your personal chat, a group, or a channel).

```yaml
environment:
  TELEGRAM_BOT_TOKEN: "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
  TELEGRAM_CHAT_ID: "123456789"
```

The token and chat ID are read from environment variables only — they are never stored in the database.

### Getting your chat ID

- **Personal chat:** Start a conversation with your bot, then call `https://api.telegram.org/bot<TOKEN>/getUpdates` and look for the `chat.id` field in the response.
- **Group or channel:** Add the bot to the group/channel, send a message, and use `getUpdates` as above.

### Per-notification setup (UI)

Go to **Notifications → Add notification → Telegram**. No additional fields are required — the bot token and chat ID come from the environment variables above.

### Message format

Messages are sent with Telegram's HTML parse mode and include the route, date, departure time, train identifier, and a price comparison showing the old price (strikethrough) and the new price with the difference:

```
Price decreased

Madrid → Barcelona
2026-03-25 | 07:00 | AVE 02250

~~€45.10~~ → €39.50 (−€5.60)
```

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
