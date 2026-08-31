"""Shared serialization from DetectionJob ORM rows to API response schemas."""

from __future__ import annotations

from api.schemas.detection import DetectionItem, DetectionResponse
from database.models import DetectionJob


def job_to_detection_response(job: DetectionJob, annotated_output_url: str | None) -> DetectionResponse:
    return DetectionResponse(
        id=job.id,
        filename=job.filename,
        media_type=job.media_type,
        status=job.status,  # type: ignore[arg-type]
        error_message=job.error_message,
        detections=[
            DetectionItem(
                ship_class=d.ship_class,
                confidence=d.confidence,
                bbox_xyxy=(d.bbox_x1, d.bbox_y1, d.bbox_x2, d.bbox_y2),
                track_id=d.track_id,
                hazard_level=d.hazard_level,
                hazard_reason=d.hazard_reason,
            )
            for d in job.detections
        ],
        total_ships=job.total_ships,
        hazardous_count=job.hazardous_count,
        average_confidence=job.average_confidence,
        processing_time_seconds=job.processing_time_seconds,
        annotated_output_url=annotated_output_url,
        created_at=job.created_at,
    )
