"""
Renders detection results onto images/video frames: bounding boxes,
class + confidence + hazard labels, color-coded by hazard level.

Kept separate from detector.py so the same annotation logic can be reused
for single images (upload-image) and video frames (upload-video) without
duplicating drawing code.
"""

from __future__ import annotations

import cv2
import numpy as np

# BGR (OpenCV) colors per hazard level — matches the dark navy/steel-blue UI palette
HAZARD_COLORS: dict[str, tuple[int, int, int]] = {
    "safe": (90, 180, 60),        # green
    "suspicious": (0, 200, 235),  # amber/yellow
    "hazardous": (40, 40, 220),   # red
    "unknown": (160, 160, 160),   # gray
}

FONT = cv2.FONT_HERSHEY_SIMPLEX


def annotate_frame(frame: np.ndarray, detections: list) -> np.ndarray:
    """
    detections: list of objects with .bbox_xyxy, .ship_class, .confidence,
    .hazard_level, and optionally .track_id (duck-typed — works with both
    inference.detector.Detection and anything with the same attributes).
    Returns a new annotated frame (does not mutate the input).
    """
    out = frame.copy()

    for det in detections:
        x1, y1, x2, y2 = (int(v) for v in det.bbox_xyxy)
        color = HAZARD_COLORS.get(det.hazard_level, HAZARD_COLORS["unknown"])

        cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness=2)

        id_part = f"#{det.track_id} " if getattr(det, "track_id", None) is not None else ""
        label = f"{id_part}{det.ship_class} {det.confidence:.0%} [{det.hazard_level.upper()}]"

        (text_w, text_h), baseline = cv2.getTextSize(label, FONT, 0.5, 1)
        label_y1 = max(y1 - text_h - baseline - 4, 0)
        cv2.rectangle(out, (x1, label_y1), (x1 + text_w + 6, y1), color, thickness=-1)
        text_color = (255, 255, 255) if sum(color) < 450 else (0, 0, 0)
        cv2.putText(out, label, (x1 + 3, y1 - baseline - 2), FONT, 0.5, text_color, 1, cv2.LINE_AA)

    return out


def annotate_image_file(image_path: str, detections: list, output_path: str) -> None:
    frame = cv2.imread(image_path)
    if frame is None:
        raise ValueError(f"Could not read image at {image_path}")
    annotated = annotate_frame(frame, detections)
    cv2.imwrite(output_path, annotated)
