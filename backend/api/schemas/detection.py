"""Pydantic schemas for detection API requests/responses."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

JobStatus = Literal["pending", "processing", "completed", "failed"]


class DetectionItem(BaseModel):
    ship_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox_xyxy: tuple[float, float, float, float]
    track_id: int | None = None
    hazard_level: str
    hazard_reason: str


class DetectionResponse(BaseModel):
    id: int
    filename: str
    media_type: str  # "image" | "video"
    status: JobStatus
    error_message: str | None = None
    detections: list[DetectionItem]
    total_ships: int
    hazardous_count: int
    average_confidence: float
    processing_time_seconds: float
    annotated_output_url: str | None
    created_at: datetime


class JobAcceptedResponse(BaseModel):
    """Returned immediately by /upload-video — the job is queued, not finished.

    Poll GET /jobs/{id} (returns this same shape once status flips to
    "processing"/"completed"/"failed", with the full DetectionResponse
    fields populated once "completed") until status is a terminal state.
    """

    id: int
    filename: str
    media_type: str
    status: JobStatus


class HistoryItem(BaseModel):
    id: int
    filename: str
    media_type: str
    status: JobStatus
    total_ships: int
    hazardous_count: int
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    app_env: str
