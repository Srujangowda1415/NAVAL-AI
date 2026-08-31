"""
Naval Vessel Detection & Classification System — FastAPI entrypoint.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import auth, health, history, jobs, upload
from core.config import settings
from database.models import Base
from database.session import engine

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Naval Vessel Detection & Classification API",
    description="Detects, classifies, and hazard-scores ships in images and video.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    settings.ensure_directories()
    # For local/dev use. In production, use Alembic migrations instead
    # (see backend/database/ and add `alembic upgrade head` to deploy steps).
    Base.metadata.create_all(bind=engine)

    # Serve annotated images/videos (from /upload-image, /upload-video) and
    # generated PDF reports directly. Mounted at startup, after
    # ensure_directories(), so the dirs are guaranteed to exist first.
    app.mount("/outputs", StaticFiles(directory=str(settings.output_dir)), name="outputs")
    app.mount("/reports", StaticFiles(directory=str(settings.report_dir)), name="reports")

    logger.info("Naval AI backend started in %s mode", settings.app_env)
