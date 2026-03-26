# Renfe Tracker — CLAUDE.md

Self-hosted Docker app for tracking Spanish Renfe train prices. Alerts when prices change.
Single-user deployment; no cloud services needed.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI |
| Database | SQLite (aiosqlite, single file in volume) |
| Scheduler | APScheduler (in-process, async) |
| Renfe Client | Vendored `renfe_mcp` (GTFS + DWR scraper) |
| Frontend | React 19 + TypeScript + Tailwind CSS v4 + Vite |
| Router | React Router v7 |
| Deployment | Docker Compose, single container, port 8000 |

---

## Project Structure

```
app/
├── main.py                    # FastAPI app, scheduler startup, static serving
├── api/
│   ├── trips.py               # CRUD tracked trips
│   ├── search.py              # Train search + station options
│   └── notifications.py       # Notification config CRUD
├── db/
│   ├── schema.py              # Table creation + column migrations
│   ├── connection.py          # SQLite singleton
│   ├── config.py              # DATA_DIR / SQLITE_PATH resolution
│   ├── trips.py               # Trip ORM layer
│   ├── price_events.py        # Price change records
│   ├── price_samples.py       # Per-trip price samples (min/max range)
│   ├── price_history.py       # Global price history by weekday
│   └── notifications.py       # Notification config ORM
└── services/
    ├── price_check.py         # Main scheduler job
    ├── notifications.py       # Email + Home Assistant dispatch
    ├── possible_trains.py     # Infer trains not yet published
    └── maintenance.py         # Daily cleanup of old price_history

frontend/src/
├── App.tsx                    # Routes + header nav
├── api/
│   ├── client.ts              # Fetch wrapper (/api base)
│   └── types.ts               # TypeScript interfaces
├── pages/
│   ├── HomePage.tsx           # Tracked trips list
│   ├── SearchPage.tsx         # Search form
│   ├── ResultsPage.tsx        # Search results + track dialog
│   ├── TripDetailPage.tsx     # Price events timeline
│   ├── NotificationsPage.tsx  # List notifications
│   └── NotificationCreatePage.tsx  # Add email/HA/browser
└── BrowserNotificationsManager.tsx  # Client-side polling for changes
```

---

## Database Tables

- **trips**: origin, destination, date, train_identifier, check_interval_minutes, last_checked_at, last_price_change_direction
- **price_events**: price changes detected per trip (trip_id, price_detected, detected_at)
- **price_samples**: unique prices observed per trip; UNIQUE(trip_id, price) + last_seen_at; used for estimated range
- **price_history**: global prices by route+weekday+train; UNIQUE(origin, destination, weekday, train_identifier, departure_time, price)
- **notifications**: type ('email'|'home_assistant'|'browser'), type-specific fields, secrets stored plaintext
- **push_subscriptions**: reserved for future Web Push (exists but unused)

---

## Scheduler Jobs

1. **Price check** (every 1 min): for each due trip, call Renfe, compare price, insert price_event if changed, dispatch notifications
2. **Heartbeat** (every 60s): logging only
3. **Maintenance** (daily 3am): delete price_history older than RENFE_PRICE_HISTORY_DAYS (default 365)

### Price Change Logic
- Prices rounded to 2 decimals (Decimal ROUND_HALF_UP) before comparison
- On change: insert price_event, update last_price_change_direction ('up'/'down'/None), dispatch notifications
- Always update last_checked_at; also upsert price_samples + price_history

---

## Notifications

Four types:
- **Email**: SMTP with STARTTLS, dispatched via `asyncio.to_thread(smtplib...)`
- **Home Assistant**: POST to `/api/services/notify/{service}` with long-lived token
- **Telegram**: POST to Telegram Bot API `sendMessage` with HTML formatting, bot token and chat ID from env vars
- **Browser/Push**: Client-side only — `BrowserNotificationsManager.tsx` polls `/trips` every 60s; push_subscriptions table + VAPID keys exist but are not yet used (PWA conversion planned)

Notification message format:
```
Trip - {origin} -> {destination}, {departure_time}, changed price from {old_price} to {new_price}
```

Dispatch is best-effort (logs errors, never crashes scheduler).
API returns redacted secrets in public endpoints; full credentials only for internal dispatch.

---

## Estimated Price Ranges

- **price_samples**: per-trip prices from initial search + scheduler reference checks
- **price_history**: global prices across all trips by weekday
- Reference dates = same weekday across multiple weeks (up to RENFE_REFERENCE_WEEKS, default 10)
- Range shown on search results and tracked trip list (computed as min/max of stored samples)

---

## Possible Trains

Trains not yet published for the requested date but expected based on recurring weekday patterns:
- Fetch trains for same weekday on reference dates
- Any train in union but missing from requested date → marked `is_possible=true`
- Shown with dashed border + "Tren posible" badge in frontend

---

## Key Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| DATA_DIR | ./data | Volume mount for SQLite |
| SQLITE_PATH | {DATA_DIR}/renfe_tracker.db | DB file |
| RENFE_GTFS_DIR | {DATA_DIR}/renfe_schedule | GTFS data |
| RENFE_MOCK | 0 | Return mock trains (no Renfe queries) |
| RENFE_POSSIBLE_TRAINS | 1 | Enable possible trains inference |
| RENFE_REFERENCE_WEEKS | 10 | Weeks to fetch for price range |
| RENFE_PRICE_HISTORY_DAYS | 365 | Retention for price_history |
| PORT | 8000 | Host port |
| TELEGRAM_BOT_TOKEN | (none) | Telegram bot API token from @BotFather |
| TELEGRAM_CHAT_ID | (none) | Target Telegram chat/group/channel ID |

---

## Running Locally

```bash
docker compose up --build
# App: http://localhost:8000
# SQLite: ./data/renfe_tracker.db
# GTFS auto-downloaded on first query
```

For development without Docker:
```bash
# Backend
uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev   # Vite dev server on :5173 (proxies /api to :8000)
```

---

## Frontend Routes

| Route | Page | Purpose |
|-------|------|---------|
| `/` | HomePage | Tracked trips grouped by route |
| `/search` | SearchPage | Date + station form |
| `/results` | ResultsPage | Trains + track dialog |
| `/trip/:id` | TripDetailPage | Price events timeline |
| `/notifications` | NotificationsPage | List + delete |
| `/notifications/new` | NotificationCreatePage | Add notification |

---

## UI Theme

Tailwind CSS v4 with custom Renfe-inspired CSS variables:
- `--color-renfe-header`: header background
- `--color-renfe-red`: primary CTA buttons
- `--color-renfe-purple`: accents and focus rings

Cards use `rounded-xl`, `ring-1`, `shadow-sm`. Responsive 1→2 column grids.

---

## Internationalisation (i18n)

### Frontend App

- **Library:** i18next + react-i18next
- **Locales:** `en`, `es`, `ca` (English, Spanish, Catalan)
- **Config:** `frontend/src/i18n/index.ts` — detects language from localStorage (`'lang'`), then browser, fallback `en`
- **Translation files:** `frontend/src/i18n/{en,es,ca}.json` (~173 keys each)
- **Key namespaces:** `common`, `nav`, `home`, `search`, `results`, `trip`, `notifications`, `configuration`
- **Language switcher:** rendered in the app footer (EN / ES / CA buttons), writes to localStorage

### Docusaurus Website

- **Locales:** `en` (default), `es`, `ca` — configured in `website/docusaurus.config.ts`
- **Translation files:** `website/i18n/{es,ca}/`
  - `docusaurus-plugin-content-docs/current/` — full translated copies of all doc pages
  - `docusaurus-plugin-content-docs/current.json` — sidebar category labels
  - `docusaurus-theme-classic/{navbar,footer}.json` — navbar/footer UI strings
- Navbar includes a locale-selector dropdown

---

## Documentation Website (`website/`)

Docusaurus 3.7.0 static site, deployed to GitHub Pages at `https://JavierMonton.github.io/renfe-tracker/`.

- **Config:** `website/docusaurus.config.ts`, sidebars in `website/sidebars.ts`
- **Docs served at:** `/` (base URL `/renfe-tracker/`, trailing slash disabled)
- **Content:** `website/docs/`
  - `intro.md` (slug `/`) → `installation.md` → `configuration.md`
  - `features/` category: `trip-tracking.md`, `price-range.md`, `possible-trains.md`, `notifications.md`
- **Custom CSS:** `website/src/css/custom.css` (Renfe colour palette)
- **Static assets:** `website/static/img/` (screenshots + logo)
- **Node version:** ≥18

---

## CI/CD (GitHub Actions)

Three workflows in `.github/workflows/`:

| File | Trigger | What it does |
|------|---------|--------------|
| `deploy-docs.yml` | Push to `main` touching `website/**` (or manual) | Runs `npm ci && npm run build` in `website/`, deploys to `gh-pages` branch via `peaceiris/actions-gh-pages` |
| `pr-tests.yml` | Pull request (open/sync/reopen) | Installs `uv`, runs `ruff check` + `pytest` against Python 3.11 backend |
| `release-docker.yml` | Push of `v*.*.*` tag | Builds multi-platform Docker image, pushes to Docker Hub as `{DOCKERHUB_USERNAME}/renfe-tracker:{tag}` and `:latest` |

Docker Hub credentials stored as repository secrets `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`.

---

## Current Status

- Core features complete: trip tracking, price checking, price history, possible trains, email/HA/Telegram notifications, browser polling
- In progress: PWA conversion + true Web Push (push_subscriptions table exists, VAPID not yet wired up)
- Notifications UI pages exist but the browser/push flow is not yet fully functional

---

## Planning Documents (`.cursor/`)

- `Requeriments.md` — full product requirements
- `requirements_notifications.md` — notifications feature spec (email, HA, browser/PWA)
- `ESTIMATED_PRICE_RANGE_PLAN.md` — price sampling strategy
- `SCHEDULER_PLAN.md` — scheduler design
- `TRACKER_PLAN.md` — trip tracking flow
- `tasks/` — per-feature task breakdowns
