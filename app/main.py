"""Renfe Tracker – FastAPI app. API under /api, static files at /."""
import logging
import os

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

# Static files last so /api takes precedence
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

scheduler = AsyncIOScheduler()

def _scheduler_heartbeat():
    logging.getLogger("renfe_tracker").info("Scheduler heartbeat (every 60s)")


async def _run_price_check_job(db_path: str) -> None:
    from app.services.price_check import run_price_check
    await run_price_check(db_path)


@app.on_event("startup")
async def startup():
    db_path = get_sqlite_path()
    ensure_data_dir(db_path)
    await init_db(db_path)
    app.state.db_path = db_path
    await get_connection(db_path)
    scheduler.add_job(_scheduler_heartbeat, "interval", seconds=60, id="heartbeat")
    scheduler.add_job(_run_price_check_job, "interval", minutes=5, id="price_check", args=[db_path])
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)
    await close_connection()
