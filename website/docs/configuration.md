---
id: configuration
sidebar_position: 3
title: Configuration
---

# Configuration

All configuration is done through environment variables. When using Docker Compose, set them in your `docker-compose.yml` or a `.env` file in the same directory.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `./data` | Directory where the SQLite database and GTFS data are stored. Inside Docker this is `/data`. |
| `SQLITE_PATH` | `{DATA_DIR}/renfe_tracker.db` | Override the database file path. |
| `RENFE_GTFS_DIR` | `{DATA_DIR}/renfe_schedule` | Directory for Renfe GTFS schedule data (downloaded automatically). |
| `RENFE_MOCK` | `0` | Set to `1` to return mock trains instead of querying Renfe. Useful for testing the UI. |
| `RENFE_POSSIBLE_TRAINS` | `1` | Set to `0` to disable the possible trains feature. |
| `RENFE_REFERENCE_WEEKS` | `10` | How many same-weekday reference weeks to use for price range estimation and possible train inference. Set to `0` to disable. |
| `RENFE_PRICE_HISTORY_DAYS` | `365` | How many days of global price history to keep. Older records are deleted by the nightly maintenance job. |
| `PORT` | `8000` | Host port exposed by the container. |
| `PUID` | _(unset)_ | If set, the entrypoint will `chown /data` to this user ID. |
| `PGID` | _(unset)_ | Group ID companion to `PUID`. |

## Email (SMTP)

These variables configure the SMTP connection used for email alerts. The recipient address and subject are configured per-notification in the UI.

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | Port — `587` (STARTTLS, default), `465` (SSL), or `25` (plain) |
| `SMTP_USERNAME` | SMTP login username |
| `SMTP_PASSWORD` | SMTP login password |
| `SMTP_USE_STARTTLS` | `true` or `false`. Default `true`. Set to `false` for plain/SSL servers. |
| `SMTP_FROM` | Sender address. Defaults to `SMTP_USERNAME` if not set. |

## Home Assistant

| Variable | Description |
|----------|-------------|
| `HA_URL` | Base URL of your Home Assistant instance, e.g. `http://homeassistant.local:8123` |
| `HA_TOKEN` | Long-lived access token generated in HA's profile page |

## Example `.env` file

```dotenv
PORT=9000
PUID=1000
PGID=1000

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=youraddress@gmail.com
SMTP_PASSWORD=your-app-password

HA_URL=http://192.168.1.100:8123
HA_TOKEN=eyJhbGciOiJIUz...
```

Then reference it from `docker-compose.yml`:

```yaml
services:
  app:
    build: .
    env_file: .env
    ports:
      - "${PORT:-8000}:8000"
    volumes:
      - ./data:/data
    restart: unless-stopped
```
