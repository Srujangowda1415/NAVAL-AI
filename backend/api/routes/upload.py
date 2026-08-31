"""Image and video upload + detection endpoints.

Images are processed synchronously (fast — typically well under a second).
Videos are enqueued to a background worker (see core/queue.py, worker.py,
inference/tasks.py) so a multi-minute video doesn't block the request or
tie up an API server process — see /jobs/{id} to poll for completion.
"""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from api.schemas.detection import DetectionResponse, JobAcceptedResponse
from api.serializers import job_to_detection_response
from core.config import settings
from core.queue import video_queue
from core.security import require_role
from database.models import DetectionJob, ShipDetection, User
from database.session import get_db
from inference.annotator import annotate_image_file
from inference.detector import Detector
from inference.hazard_classifier import hazard_classifier
from inference.tasks import process_video_job

router = APIRouter(tags=["detection"])

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".avi", ".mov"}


def _save_upload(file: UploadFile, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "").suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = dest_dir / unique_name
    with dest_path.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)
    return dest_path


def _output_url(output_path: Path) -> str:
    """Files under settings.output_dir are served at /outputs/<name> (see main.py static mount)."""
    return f"/outputs/{output_path.name}"


@router.post("/upload-image", response_model=DetectionResponse)
def upload_image(
    file: UploadFile,
    model: str = Query(default="standard", description="Model variant: 'standard' or 'all_weather'"),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("analyst")),
) -> DetectionResponse:
    if model not in ("standard", "all_weather"):
        raise HTTPException(400, "model must be 'standard' or 'all_weather'")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(400, f"Unsupported image type '{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXTS)}")

    settings.ensure_directories()
    saved_path = _save_upload(file, settings.upload_dir)

    detector = Detector.get_all_weather_instance() if model == "all_weather" else Detector.get_instance()
    result = detector.predict_image(saved_path)

    for det in result.detections:
        hazard = hazard_classifier.classify(det.ship_class, det.confidence)
        det.hazard_level = hazard.hazard_level
        det.hazard_reason = hazard.reason

    output_path = settings.output_dir / f"{saved_path.stem}_annotated.jpg"
    annotate_image_file(str(saved_path), result.detections, str(output_path))

    job = DetectionJob(
        filename=file.filename or saved_path.name,
        media_type="image",
        upload_path=str(saved_path),
        output_path=str(output_path),
        status="completed",  # images are processed synchronously, right here
        uploaded_by_id=user.id,
        model_variant=model,
        total_ships=len(result.detections),
        hazardous_count=sum(1 for d in result.detections if d.hazard_level == "hazardous"),
        average_confidence=(
            sum(d.confidence for d in result.detections) / len(result.detections) if result.detections else 0.0
        ),
        processing_time_seconds=result.processing_time_seconds,
    )
    job.detections = [
        ShipDetection(
            ship_class=d.ship_class,
            confidence=d.confidence,
            hazard_level=d.hazard_level,
            hazard_reason=d.hazard_reason,
            track_id=d.track_id,
            bbox_x1=d.bbox_xyxy[0],
            bbox_y1=d.bbox_xyxy[1],
            bbox_x2=d.bbox_xyxy[2],
            bbox_y2=d.bbox_xyxy[3],
        )
        for d in result.detections
    ]
    db.add(job)
    db.commit()
    db.refresh(job)

    return job_to_detection_response(job, _output_url(output_path))


@router.post("/upload-video", response_model=JobAcceptedResponse, status_code=202)
def upload_video(
    file: UploadFile,
    model: str = Query(default="standard", description="Model variant: 'standard' or 'all_weather'"),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("analyst")),
) -> JobAcceptedResponse:
    """
    Accepts the video, queues it for background processing, and returns
    immediately (HTTP 202) with the job id. Poll GET /jobs/{id} for progress
    and, once status="completed", the full detection results.
    """
    if model not in ("standard", "all_weather"):
        raise HTTPException(400, "model must be 'standard' or 'all_weather'")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTS:
        raise HTTPException(400, f"Unsupported video type '{ext}'. Allowed: {sorted(ALLOWED_VIDEO_EXTS)}")

    settings.ensure_directories()
    saved_path = _save_upload(file, settings.upload_dir)

    job = DetectionJob(
        filename=file.filename or saved_path.name,
        media_type="video",
        upload_path=str(saved_path),
        status="pending",
        uploaded_by_id=user.id,
        model_variant=model,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    video_queue.enqueue(process_video_job, job.id, job_id=f"video-job-{job.id}")

    return JobAcceptedResponse(id=job.id, filename=job.filename, media_type=job.media_type, status=job.status)
