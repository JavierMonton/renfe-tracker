# Renfe Tracker – Plan and Architecture

This document is the single source of truth for the manager-architect. Use it when implementing tasks delegated to backend-developer, frontend-web-developer, and docker-expert-developer.

---

## 1. Purpose (from requirements)

- **Product:** Renfe Tracker – track, learn, and suggest trains and prices for user-given dates.
- **Users:** Self-hosters only; each user runs the app locally (Docker).
- **Scope:** Media/larga distancia only; one-way trips; one adult; no special discounts.

---

## 2. Tech stack (decisions for implementers)

| Layer        | Choice | Rationale |
|-------------|--------|-----------|
| Backend     | **Python 3 + FastAPI** | Good for API, async, and scraping; simple to run in Docker. |
| Database    | **SQLite** | Single user, self-hosted; no extra process; file-based, easy to persist in Docker. |
| Scheduler   | **APScheduler** (in-process) | Simple, no extra service; sufficient for periodic Renfe checks. |
| Renfe client| **httpx + (BeautifulSoup or selectors)** | Server-side requests; handle cookies/session as needed. |
| Frontend    | **Static SPA or server-rendered** | Backend will serve static assets. Frontend developer chooses (e.g. React/Vue/HTMX) so the UI can match Renfe look and stay maintainable. |
| Delivery    | **Docker Compose** | One app service (backend serves API + static frontend); SQLite and config in host-mounted volumes. |

---

## 3. High-level architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Host (user machine)                                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Docker Compose                                        │  │
│  │  ┌─────────────────────────────────────────────────┐   │  │
│  │  │  renfe-tracker (single container)              │   │  │
│  │  │  - FastAPI (API + static files)                 │   │  │
│  │  │  - APScheduler (periodic Renfe queries)        │   │  │
│  │  │  - SQLite DB file (in mounted volume)          │   │  │
│  │  └─────────────────────────────────────────────────┘   │  │
│  │         │ volumes: data (DB), optional config          │  │
│  └───────────────────────────────────────────────────────┘  │
│  Volumes: ./data (or named) → SQLite + any file storage     │
└─────────────────────────────────────────────────────────────┘
```

- **No separate DB container:** SQLite file in a host-mounted volume.
- **Single process:** FastAPI app starts scheduler on startup; same process.

---

## 4. Main components

### 4.1 Backend (Python/FastAPI)

- **API:** REST endpoints for: trips (CRUD), search (trigger + results), tracked trips, price events.
- **Database:** SQLite; one file (e.g. `data/renfe_tracker.db`) in a Docker volume.
- **Renfe client:** Module that queries the Renfe website (search form, results page); handles session/cookies; returns structured data (trains, prices). Can start with a stub that returns mock data so frontend and flow can be built.
- **Scheduler:** APScheduler; jobs for (a) periodic price checks for tracked trips, (b) optional “learn possible trains/prices” jobs. Configurable interval per tracked trip (e.g. every 1 hour).

### 4.2 Frontend

- **Pages:**  
  1. **Home:** Table of tracked trips + “Track new trip” button.  
  2. **Search:** Form (date, origin, destination) → submit → results.  
  3. **Results:** List of trains (name, duration, price, estimated price range; “possible train” badge + estimated availability when applicable).  
  4. **Track trip:** From a result, user selects a train, sets check interval (e.g. 1 h) → save as tracked trip.  
  5. **Tracked trip detail:** List of price-change events (price + date detected).
- **Look & feel:** Close to Renfe (colors, typography, form style); no ads/extra links. Frontend developer can use Renfe’s public site for reference.

### 4.3 Docker

- **One service:** Build and run the app (FastAPI + static assets).
- **Port:** e.g. 8000 (configurable).
- **Volumes:** Persist SQLite (and any app data) on the host; optional config mount if needed.
- **Lightweight image:** Multi-stage if helpful; minimal dependencies.

---

## 5. Data model (core entities)

- **Trip (tracked):** id, origin, destination, date, train_identifier (or similar), check_interval_minutes, created_at, (optional: user-facing label).
- **PriceEvent:** id, trip_id, price_detected, detected_at (and any extra fields for “first time we saw this train” vs “price change”).
- **Search/Result cache (optional but useful):** Store raw or parsed results of Renfe searches for “possible trains” and price learning (origin, destination, date, weekday, fetched_at, trains list with prices). Schema can be added incrementally by backend.

Use these as the minimal set to get “track a trip and see price events” working; extend later for “possible trains” and price-range estimation.

---

## 6. API outline (for backend implementer)

- `GET /api/trips` – list tracked trips.
- `POST /api/trips` – create tracked trip (from search result + interval).
- `GET /api/trips/{id}` – get one trip + its price events.
- `GET /api/search/options` – origins/destinations (can be static or from Renfe).
- `POST /api/search` – body: `{ date, origin, destination }` → returns list of trains (and optional “possible” trains); can call Renfe client (or stub).
- (Optional) `PATCH /api/trips/{id}` – e.g. change interval or disable.
- (Optional) `DELETE /api/trips/{id}`.

Frontend will call these; backend serves the built frontend at `/` and `/api/*` for API.

---

## 7. Phases and task delegation

### Phase 1 – Runnable locally with minimal features

Goal: User can run the app in Docker, open the UI, see the home page, use a search form, and see (mock) results.

| # | Task | Subagent | Deliverable |
|---|------|----------|-------------|
| 1 | Docker setup | docker-expert-developer | `Dockerfile` + `docker-compose.yml` (or equivalent); port 8000; volume for `data/` (SQLite + persistence); app runs and serves something on `/`. |
| 2 | Backend core | backend-developer | FastAPI app; SQLite with `trips` and `price_events` tables; API endpoints above (stub search returning mock trains); serve static files from a `static/` (or `frontend/dist/`) directory; APScheduler registered and running (e.g. one no-op or log job). Project layout: e.g. `app/`, `requirements.txt`, env for DB path. |
| 3 | Frontend core | frontend-web-developer | Build that outputs static assets into backend’s static folder; Home (tracked trips table + “Track new trip”); Search (form: date, origin, destination); Results (list of trains with price); Renfe-like styling. Uses API for list trips and search (mock data is fine). |

### Phase 2 (later, not in first delegation)

- Renfe client (real scraping/session).
- “Possible trains” and price-range estimation.
- Track-trip flow (save trip, scheduler runs, save price events).
- Tracked trip detail page (price events).

---

## 7b. Possible trains (inference from same weekday)

**Requirement (from Requeriments.md):** Show "possible trains" that do not yet appear on Renfe for the requested date but are expected to appear. Renfe publishes more trains for near dates; for far dates (e.g. May 7) only a subset is shown. Trains are consistent by **weekday**: the same Thursday service runs at the same times.

**Rules:**
- **Weekday matters:** If the user searches for a Friday, infer from other Fridays; for a Thursday, from other Thursdays. The **closer** the reference date to today, the **more accurate** (Renfe shows more trains for near dates).
- **Train identity:** Same train = same `train_type` + `departure_time` (HH:MM) on the same route. Use this key to merge results and detect "appears on reference date but not on requested date".
- **Reference dates:** Given requested date and its weekday, choose 1–2 reference dates: same weekday, preferably in the **near future** (e.g. next 1–2 weeks from today). Call `get_train_prices(origin, destination, ref_date)` for each. Union of trains from reference dates = "all trains that typically run on this weekday". Trains in that union that are **not** in the requested-date result = **possible trains** (not yet published for the requested date).
- **API response:** Each train in the list must have `is_possible: boolean`. If `true`, the train is inferred (not yet published for this date). Optionally include `inferred_from_date` (YYYY-MM-DD) for display. Real (published) trains first, then possible trains; or single list sorted by departure time with visual distinction in the UI.
- **Performance:** Limit extra Renfe calls (e.g. max 2 reference dates). Consider env flag to disable possible-trains inference (e.g. `RENFE_POSSIBLE_TRAINS=0`).

**Frontend (Results page):** Possible trains: slightly different card style (e.g. muted/secondary color) and a tag or icon: "Possible train – not yet published for this date". "Track this trip" remains available for possible trains.

---

## 8. Repo layout (suggested)

```
renfe-tracker/
├── .cursor/
│   ├── Requeriments.md
│   └── PLAN_AND_ARCHITECTURE.md
├── app/                 # Backend (FastAPI)
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── db/
│   └── renfe_client.py  # or stub
├── frontend/            # Frontend source (builds to app/static or similar)
├── data/                # Mounted in Docker; SQLite here (gitignore)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

Docker expert and backend can agree on exact paths (e.g. `static` vs `frontend/dist`).

---

## 9. Success criteria for “run locally”

- From repo root: `docker compose up --build` (or `docker-compose up --build`).
- Open `http://localhost:8000` in browser.
- See home with tracked trips (empty at first) and “Track new trip”.
- Click “Track new trip” → search form; submit → results page with at least mock trains and prices.
- No crash; SQLite file created in `data/` (or configured volume).

Implementers: start with Phase 1 tasks above. Use this document for any ambiguity; keep changes small and incremental.

---

## 11. Estimated price range for tracked trips

See **`.cursor/ESTIMATED_PRICE_RANGE_PLAN.md`** for the full plan. Summary: persist individual price samples (from search and from scheduler reference-date checks) in a `price_samples` table; show computed min/max range on tracked trip list and detail; scheduler extends to "same weekday, other weeks" and upserts prices. Delegated tasks: **`.cursor/tasks/estimated-price-range-backend.md`** (backend-developer), **`.cursor/tasks/estimated-price-range-frontend.md`** (frontend-web-developer). No breaking changes to existing tracker or scheduler behaviour.

---

## 10. How to run locally (Phase 1)

```bash
# From repo root
docker compose up --build
```

Then open **http://localhost:8000**. You should see:
- Home: empty tracked trips table + "Track new trip"
- Track new trip → Search form (date, origin, destination) → Search → Results (mock trains) → "Seguir este viaje" on a train → back to Home with the new trip; click "Ver detalle" to see price events (empty until scheduler/real Renfe is wired).
- Database persists in `./data/renfe_tracker.db` on the host.
