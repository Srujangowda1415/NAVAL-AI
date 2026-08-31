"""
Video pipeline: Video -> frame-by-frame tracked YOLO detection -> hazard
classification per detection -> annotated frame -> rebuilt annotated video
-> per-track summary (one row per unique ship across the whole video,
rather than one row per frame).

Tracking (ByteTrack/BoT-SORT, via Detector.predict_video_stream) is what
lets us collapse "the same ship seen in 400 frames" into a single summary
entry with its best (highest-confidence) observation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

import cv2

from core.config import settings
from inference.annotator import annotate_frame
from inference.detector import Detection, Detector
from inference.hazard_classifier import hazard_classifier

logger = logging.getLogger(__name__)


@dataclass
class TrackSummary:
    track_id: int | None
    ship_class: str
    best_confidence: float
    hazard_level: str
    hazard_reason: str
    first_seen_frame: int
    last_seen_frame: int
    bbox_xyxy: tuple[float, float, float, float]  # bbox at the best-confidence frame


@dataclass
class VideoResult:
    annotated_video_path: str
    track_summaries: list[TrackSummary] = field(default_factory=list)
    total_frames: int = 0
    processing_time_seconds: float = 0.0


def process_video(video_path: Path | str, output_path: Path | str) -> VideoResult:
    """
    Runs the full video pipeline and writes an annotated .mp4 to output_path.
    Enforces settings.max_video_duration_seconds to avoid runaway processing
    on an oversized upload.
    """
    video_path = Path(video_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"Could not open video at {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = frame_count / fps if fps else 0
    cap.release()  # detector.predict_video_stream opens its own capture via ultralytics

    if duration_seconds > settings.max_video_duration_seconds:
        raise ValueError(
            f"Video is {duration_seconds:.0f}s, which exceeds the "
            f"{settings.max_video_duration_seconds}s limit (MAX_VIDEO_DURATION_SECONDS in .env)."
        )

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    detector = Detector.get_instance()
    tracks: dict[int | None, TrackSummary] = {}
    start = time.perf_counter()
    n_frames = 0

    try:
        for frame_idx, result in detector.predict_video_stream(video_path):
            n_frames += 1

            for det in result.detections:
                hazard = hazard_classifier.classify(det.ship_class, det.confidence)
                det.hazard_level = hazard.hazard_level
                det.hazard_reason = hazard.reason
                _update_track_summary(tracks, det, frame_idx)

            if result.orig_img is not None:
                annotated_frame = annotate_frame(result.orig_img, result.detections)
                writer.write(annotated_frame)
    finally:
        writer.release()

    elapsed = time.perf_counter() - start
    logger.info(
        "Processed video %s: %d frames, %d unique tracked ships, %.1fs",
        video_path.name, n_frames, len(tracks), elapsed,
    )

    return VideoResult(
        annotated_video_path=str(output_path),
        track_summaries=sorted(tracks.values(), key=lambda t: t.first_seen_frame),
        total_frames=n_frames,
        processing_time_seconds=elapsed,
    )


def _update_track_summary(tracks: dict[int | None, TrackSummary], det: Detection, frame_idx: int) -> None:
    """
    Keep one summary row per track_id: extend the seen-frame range every
    time, but only overwrite class/confidence/bbox when this frame's
    confidence beats the best one recorded so far for that ship.
    """
    key = det.track_id
    existing = tracks.get(key)

    if existing is None:
        tracks[key] = TrackSummary(
            track_id=det.track_id,
            ship_class=det.ship_class,
            best_confidence=det.confidence,
            hazard_level=det.hazard_level,
            hazard_reason=det.hazard_reason,
            first_seen_frame=frame_idx,
            last_seen_frame=frame_idx,
            bbox_xyxy=det.bbox_xyxy,
        )
        return

    existing.last_seen_frame = frame_idx
    if det.confidence > existing.best_confidence:
        existing.ship_class = det.ship_class
        existing.best_confidence = det.confidence
        existing.hazard_level = det.hazard_level
        existing.hazard_reason = det.hazard_reason
        existing.bbox_xyxy = det.bbox_xyxy
