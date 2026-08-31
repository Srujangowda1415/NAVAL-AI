"""
YOLO-based ship detector/classifier wrapper.

Wraps Ultralytics YOLO so the rest of the app never touches the model
object directly. Model weights path, device, and thresholds all come
from `core.config.settings` (env-driven), never hardcoded.

NOTE: this module imports `ultralytics`, which is a heavy dependency.
It is only imported lazily inside `Detector.__init__` so that the API
can still boot (e.g. for /health) even before weights are trained/placed.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    ship_class: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    track_id: int | None = None
    hazard_level: str = "unknown"
    hazard_reason: str = ""


@dataclass
class InferenceResult:
    detections: list[Detection] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    annotated_image_path: str | None = None
    orig_img: "object | None" = None  # raw numpy BGR frame; populated for video frames only


class Detector:
    """Singleton-style wrapper around a loaded YOLO model."""

    _instance: "Detector | None" = None
    _all_weather_instance: "Detector | None" = None

    def __init__(self, weights_path: Path | str | None = None, device: str | None = None, conf_threshold: float | None = None):
        from ultralytics import YOLO  # lazy import

        self.weights_path = Path(weights_path or settings.yolo_weights_path)
        self.device = device or settings.yolo_device
        self.conf_threshold = conf_threshold if conf_threshold is not None else settings.yolo_conf_threshold

        if not self.weights_path.exists():
            logger.warning(
                "YOLO weights not found at %s. Detector will fail on inference until "
                "a trained model is placed there (see backend/training/).",
                self.weights_path,
            )
            self.model = None
        else:
            self.model = YOLO(str(self.weights_path))
            logger.info("Loaded YOLO model from %s on device %s", self.weights_path, self.device)

    @classmethod
    def get_instance(cls) -> "Detector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def get_all_weather_instance(cls) -> "Detector":
        """Returns a singleton Detector loaded with the all-weather weights."""
        if cls._all_weather_instance is None:
            cls._all_weather_instance = cls(
                weights_path=settings.all_weather_weights_path,
                conf_threshold=settings.all_weather_conf_threshold,
            )
        return cls._all_weather_instance

    def predict_image(self, image_path: Path | str) -> InferenceResult:
        if self.model is None:
            raise RuntimeError(
                f"No YOLO weights loaded from {self.weights_path}. "
                "Train a model first (see backend/training/train.py) or update "
                "YOLO_WEIGHTS_PATH in .env."
            )

        start = time.perf_counter()
        results = self.model.predict(
            source=str(image_path),
            conf=self.conf_threshold,
            iou=settings.yolo_iou_threshold,
            device=self.device,
            verbose=False,
        )
        elapsed = time.perf_counter() - start

        detections: list[Detection] = []
        result = results[0]
        names = result.names
        for box in result.boxes:
            cls_id = int(box.cls.item())
            conf = float(box.conf.item())
            xyxy = tuple(float(v) for v in box.xyxy[0].tolist())
            detections.append(
                Detection(
                    ship_class=names[cls_id],
                    confidence=conf,
                    bbox_xyxy=xyxy,  # type: ignore[arg-type]
                )
            )

        return InferenceResult(detections=detections, processing_time_seconds=elapsed)

    def predict_video_stream(self, video_path: Path | str):
        """
        Generator yielding (frame_index, InferenceResult) for each frame,
        using YOLO's built-in tracker (ByteTrack/BoT-SORT, set via
        settings.tracker_type) for consistent ship IDs across frames.
        """
        if self.model is None:
            raise RuntimeError(f"No YOLO weights loaded from {self.weights_path}.")

        tracker_cfg = "bytetrack.yaml" if settings.tracker_type == "bytetrack" else "botsort.yaml"

        for frame_idx, result in enumerate(
            self.model.track(
                source=str(video_path),
                conf=self.conf_threshold,
                iou=settings.yolo_iou_threshold,
                device=self.device,
                tracker=tracker_cfg,
                stream=True,
                verbose=False,
            )
        ):
            names = result.names
            detections: list[Detection] = []
            for box in result.boxes:
                cls_id = int(box.cls.item())
                conf = float(box.conf.item())
                xyxy = tuple(float(v) for v in box.xyxy[0].tolist())
                track_id = int(box.id.item()) if box.id is not None else None
                detections.append(
                    Detection(
                        ship_class=names[cls_id],
                        confidence=conf,
                        bbox_xyxy=xyxy,  # type: ignore[arg-type]
                        track_id=track_id,
                    )
                )
            yield frame_idx, InferenceResult(detections=detections, orig_img=result.orig_img)
