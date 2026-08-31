from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas.detection import HistoryItem
from core.config import settings
from core.security import require_role
from database.models import DetectionJob, User
from database.session import get_db
from reports.generator import generate_pdf_report

router = APIRouter(tags=["history"])


@router.get("/history", response_model=list[HistoryItem])
def get_history(
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("viewer")),
) -> list[HistoryItem]:
    jobs = db.execute(select(DetectionJob).order_by(DetectionJob.created_at.desc())).scalars().all()
    return [
        HistoryItem(
            id=job.id,
            filename=job.filename,
            media_type=job.media_type,
            status=job.status,  # type: ignore[arg-type]
            total_ships=job.total_ships,
            hazardous_count=job.hazardous_count,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.delete("/history/{job_id}")
def delete_history_item(
    job_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("analyst")),
) -> dict:
    job = db.get(DetectionJob, job_id)
    if job is None:
        raise HTTPException(404, f"Detection job {job_id} not found")
    db.delete(job)
    db.commit()
    return {"deleted": job_id}


@router.get("/report/{job_id}")
def get_report(
    job_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role("viewer")),
) -> FileResponse:
    """
    Generates (on first request) or serves (on repeat requests) a PDF
    detection report for the given job. Generation happens lazily here
    rather than at upload time, so upload latency isn't paying the PDF
    cost every single time.
    """
    job = db.get(DetectionJob, job_id)
    if job is None:
        raise HTTPException(404, f"Detection job {job_id} not found")
    if job.status != "completed":
        raise HTTPException(409, f"Job {job_id} is not finished yet (status={job.status}); no report to generate.")

    settings.ensure_directories()
    report_path = settings.report_dir / f"job_{job_id}_report.pdf"

    if not report_path.exists():
        annotated_image_path = job.output_path if job.media_type == "image" else None
        generate_pdf_report(job, report_path, annotated_image_path=annotated_image_path)
        job.report_path = str(report_path)
        db.commit()

    download_name = f"{Path(job.filename).stem}_report.pdf"
    return FileResponse(path=report_path, media_type="application/pdf", filename=download_name)
