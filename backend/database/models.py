"""ORM models for the naval detection system."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    """
    Roles (least to most privileged):
      - viewer:  read-only — history, reports, job status
      - analyst: viewer + can upload images/videos and delete jobs
      - admin:   analyst + user management (see api/routes/auth.py)
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="viewer")
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DetectionJob(Base):
    """One uploaded image or video and its aggregate detection results."""

    __tablename__ = "detection_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    media_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "image" | "video"
    upload_path: Mapped[str] = mapped_column(String(512), nullable=False)
    output_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    report_path: Mapped[str | None] = mapped_column(String(512), nullable=True)

    total_ships: Mapped[int] = mapped_column(Integer, default=0)
    hazardous_count: Mapped[int] = mapped_column(Integer, default=0)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    processing_time_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # "pending" (queued, not started) | "processing" | "completed" | "failed"
    # Image jobs go straight to "completed" since they're processed synchronously.
    # Video jobs start "pending" and are updated by the RQ worker (see
    # inference/tasks.py) as the job progresses.
    status: Mapped[str] = mapped_column(String(16), default="completed")
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # "standard" | "all_weather" — which model weights were used for this job
    model_variant: Mapped[str] = mapped_column(String(32), default="standard")

    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    detections: Mapped[list["ShipDetection"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class ShipDetection(Base):
    """One detected ship within a DetectionJob."""

    __tablename__ = "ship_detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("detection_jobs.id"), nullable=False)

    ship_class: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    hazard_level: Mapped[str] = mapped_column(String(16), nullable=False)
    hazard_reason: Mapped[str] = mapped_column(String(255), default="")
    track_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    bbox_x1: Mapped[float] = mapped_column(Float)
    bbox_y1: Mapped[float] = mapped_column(Float)
    bbox_x2: Mapped[float] = mapped_column(Float)
    bbox_y2: Mapped[float] = mapped_column(Float)

    job: Mapped["DetectionJob"] = relationship(back_populates="detections")
