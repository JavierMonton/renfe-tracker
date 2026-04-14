"""Renfe Tracker – FastAPI app. API under /api, static files at /."""
import logging
import os

# Ensure scheduler and app logs are visible (INFO). Root may already be configured by uvicorn.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)
for _name in ("renfe_tracker", "app"):
    logging.getLogger(_name).setLevel(logging.INFO)

logger = logging.getLogger("renfe_tracker")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.config import get_sqlite_path, ensure_data_dir
from app.db.schema import init_db
from app.db.connection import get_connection, close_connection
from app.api.trips import router as trips_router
from app.api.search import router as search_router
from app.api.notifications import router as notifications_router

app = FastAPI(title="Renfe Tracker")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """Return 400 with a single detail string so frontend always gets JSON detail."""
    errors = exc.errors()
    detail = errors[0].get("msg", "Validation error") if errors else "Validation error"
    if errors and "loc" in errors[0]:
        loc = errors[0]["loc"]
        if len(loc) > 1 and loc[-1] != "body":
            detail = f"{loc[-1]}: {detail}"
    return JSONResponse(status_code=400, content={"detail": detail})

# CORS: allow frontend (permissive for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API under /api
app.include_router(trips_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(notifications_router, prefix="/api")


@app.get("/health")
async def health():
    """Health check endpoint for status, db and scheduler."""
    db_ok = False
    try:
        from app.db.connection import get_connection
        conn = await get_connection(app.state.db_path)
        await conn.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass

    scheduler_ok = scheduler.running

    if db_ok and scheduler_ok:
        return {"status": "ok", "db": "ok", "scheduler": "ok"}

    return JSONResponse(
        status_code=503,
        content={
            "status": "degraded",
            "db": "ok" if db_ok else "error",
            "scheduler": "ok" if scheduler_ok else "error",
        },
    )

# Static files last so /api takes precedence
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
frontend_dist_dir = os.path.join(repo_root, "frontend", "dist")
legacy_static_dir = os.path.join(os.path.dirname(__file__), "static")
static_dir = frontend_dist_dir if os.path.isdir(frontend_dist_dir) else legacy_static_dir
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

scheduler = AsyncIOScheduler()

# Sweep interval: how often we look for due trips. Each trip is due when last_checked_at + check_interval_minutes.
PRICE_CHECK_SWEEP_MINUTES = 1


def _scheduler_heartbeat():
    logger.info("Scheduler heartbeat (every 60s)")


async def _run_price_check_job(db_path: str) -> None:
    from app.services.price_check import run_price_check
    await run_price_check(db_path)


async def _run_maintenance_job(db_path: str) -> None:
    from app.services.maintenance import run_maintenance
    await run_maintenance(db_path)


@app.on_event("startup")
async def startup():
    db_path = get_sqlite_path()
    ensure_data_dir(db_path)
    await init_db(db_path)
    app.state.db_path = db_path
    await get_connection(db_path)

    logger.info("Scheduler starting")
    scheduler.add_job(_scheduler_heartbeat, "interval", seconds=60, id="heartbeat")
    scheduler.add_job(
        _run_price_check_job,
        "interval",
        minutes=PRICE_CHECK_SWEEP_MINUTES,
        id="price_check",
        args=[db_path],
    )
    scheduler.add_job(
        _run_maintenance_job,
        "cron",
        hour=3,
        minute=0,
        id="maintenance",
        args=[db_path],
    )
    scheduler.start()
    logger.info(
        "Scheduler started (price check sweep every %s min)",
        PRICE_CHECK_SWEEP_MINUTES,
    )

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)
    await close_connection()
