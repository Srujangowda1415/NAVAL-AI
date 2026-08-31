"""
Background job run by the RQ worker (backend/worker.py) for video uploads.

Kept separate from api/routes/upload.py so it has no dependency on FastAPI —
it's enqueued by the API process but executed by a completely separate
worker process (or several, scaled independently — see docker-compose.yml).
"""

from __future__ import annotations

import logging
from pathlib import Path

from core.config import settings
from database.models import DetectionJob, ShipDetection
from database.session import SessionLocal
from inference.video_processor import process_video

logger = logging.getLogger(__name__)


def process_video_job(job_id: int) -> None:
    """
    Loads the DetectionJob row, runs the video pipeline, and writes results
    (or the error) back to the same row. Never raises — a failure is recorded
    on the job as status="failed" so the frontend can show it, rather than
    the job silently vanishing from history.
    """
    db = SessionLocal()
    try:
        job = db.get(DetectionJob, job_id)
        if job is None:
            logger.error("process_video_job: job %s not found — nothing to do", job_id)
            return

        job.status = "processing"
        db.commit()

        output_path = settings.output_dir / f"{Path(job.upload_path).stem}_annotated.mp4"

        try:
            video_result = process_video(job.upload_path, output_path)
        except Exception as e:  # noqa: BLE001 — any failure here must be recorded on the job, not swallowed
            logger.exception("Video processing failed for job %s", job_id)
            job.status = "failed"
            job.error_message = str(e)[:500]
            db.commit()
            return

        tracks = video_result.track_summaries
        job.output_path = str(output_path)
        job.total_ships = len(tracks)
        job.hazardous_count = sum(1 for t in tracks if t.hazard_level == "hazardous")
        job.average_confidence = sum(t.best_confidence for t in tracks) / len(tracks) if tracks else 0.0
        job.processing_time_seconds = video_result.processing_time_seconds
        job.detections = [
            ShipDetection(
                ship_class=t.ship_class,
                confidence=t.best_confidence,
                hazard_level=t.hazard_level,
                hazard_reason=t.hazard_reason,
                track_id=t.track_id,
                bbox_x1=t.bbox_xyxy[0],
                bbox_y1=t.bbox_xyxy[1],
                bbox_x2=t.bbox_xyxy[2],
                bbox_y2=t.bbox_xyxy[3],
            )
            for t in tracks
        ]
        job.status = "completed"
        db.commit()
        logger.info("Video job %s completed: %d ships tracked", job_id, len(tracks))
    finally:
        db.close()
