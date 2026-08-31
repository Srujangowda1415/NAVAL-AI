from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.schemas.detection import DetectionResponse
from api.serializers import job_to_detection_response
from core.security import require_role
from database.models import DetectionJob, User
from database.session import get_db

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=DetectionResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("viewer")),
) -> DetectionResponse:
    """
    Poll this after /upload-video's 202 response. status will be
    "pending" -> "processing" -> "completed" (or "failed", with
    error_message set). detections/total_ships/etc. are only meaningful
    once status="completed".
    """
    job = db.get(DetectionJob, job_id)
    if job is None:
        raise HTTPException(404, f"Job {job_id} not found")

    annotated_url = f"/outputs/{job.output_path.split('/')[-1]}" if job.output_path else None
    return job_to_detection_response(job, annotated_url)
