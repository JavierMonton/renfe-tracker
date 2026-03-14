"""Renfe Tracker – FastAPI app. API under /api, static files at /."""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.config import get_sqlite_path, ensure_data_dir
from app.db.schema import init_db
from app.db.connection import get_connection, close_connection
from app.api.trips import router as trips_router
from app.api.search import router as search_router

app = FastAPI(title="Renfe Tracker")

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

@app.on_event("startup")
async def startup():
    db_path = get_sqlite_path()
    ensure_data_dir(db_path)
    await init_db(db_path)
    app.state.db_path = db_path
    await get_connection(db_path)
    scheduler.add_job(_scheduler_heartbeat, "interval", seconds=60, id="heartbeat")
    scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)
    await close_connection()
