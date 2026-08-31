"""
Shared utilities for converting heterogeneous ship datasets into a single
YOLO-format dataset matching `datasets/naval_dataset.yaml`.

Every per-dataset converter script (see prepare_seaships.py, etc.) imports
from here so class-name normalization and YOLO label writing stay
consistent across sources.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DATASET_YAML = Path(__file__).resolve().parent.parent.parent / "datasets" / "naval_dataset.yaml"


def load_class_names() -> dict[str, int]:
    """Return {class_name: class_id} from naval_dataset.yaml (single source of truth)."""
    with open(DATASET_YAML, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return {name: idx for idx, name in cfg["names"].items()}


# Maps messy / inconsistent labels found across public datasets to our
# canonical class names in naval_dataset.yaml. Extend this as you onboard
# more datasets — never invent a new canonical name without adding it to
# naval_dataset.yaml AND backend/config/hazard_rules.yaml first.
CLASS_NAME_ALIASES: dict[str, str] = {
    "ore carrier": "bulk_carrier",
    "bulk cargo carrier": "bulk_carrier",
    "general cargo ship": "cargo_ship",
    "container": "container_ship",
    "fishing boat": "fishing_vessel",
    "fishing ship": "fishing_vessel",
    "passenger": "passenger_ship",
    "cruise": "cruise_ship",
    "tanker": "oil_tanker",
    "tug": "tug_boat",
    "sailboat": "sail_boat",
    "warship": "frigate",  # generic warship labels default to frigate; re-tag manually if you can be more specific
}


def normalize_class_name(raw_name: str, known_classes: dict[str, int]) -> str | None:
    """
    Map a raw dataset label to one of our canonical class names.
    Returns None (and logs) if the label can't be confidently mapped —
    those boxes should be skipped rather than mislabeled.
    """
    cleaned = raw_name.strip().lower().replace("-", " ").replace("_", " ")
    if cleaned in known_classes:
        return cleaned
    canonical = cleaned.replace(" ", "_")
    if canonical in known_classes:
        return canonical
    if cleaned in CLASS_NAME_ALIASES:
        return CLASS_NAME_ALIASES[cleaned]
    logger.warning("Unmapped class label %r — skipping box. Add an alias in dataset_utils.py if needed.", raw_name)
    return None


def write_yolo_label(label_path: Path, boxes: list[tuple[int, float, float, float, float]]) -> None:
    """boxes: list of (class_id, x_center, y_center, width, height), all normalized 0-1."""
    label_path.parent.mkdir(parents=True, exist_ok=True)
    with open(label_path, "w", encoding="utf-8") as f:
        for cls_id, xc, yc, w, h in boxes:
            f.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")


def voc_bbox_to_yolo(
    xmin: float, ymin: float, xmax: float, ymax: float, img_w: int, img_h: int
) -> tuple[float, float, float, float]:
    """Convert a Pascal-VOC style bbox (pixel corners) to YOLO normalized (xc, yc, w, h)."""
    xc = ((xmin + xmax) / 2) / img_w
    yc = ((ymin + ymax) / 2) / img_h
    w = (xmax - xmin) / img_w
    h = (ymax - ymin) / img_h
    return xc, yc, w, h


def file_hash(path: Path, chunk_size: int = 65536) -> str:
    """Content hash used for de-duplicating images that appear in multiple source datasets."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def dedupe_images(image_dir: Path) -> int:
    """Remove exact-duplicate images (by content hash) within a directory. Returns count removed."""
    seen: dict[str, Path] = {}
    removed = 0
    for img_path in sorted(image_dir.glob("*")):
        if not img_path.is_file():
            continue
        h = file_hash(img_path)
        if h in seen:
            logger.info("Duplicate of %s -> removing %s", seen[h].name, img_path.name)
            label_path = img_path.parent.parent / "labels" / (img_path.stem + ".txt")
            img_path.unlink()
            if label_path.exists():
                label_path.unlink()
            removed += 1
        else:
            seen[h] = img_path
    return removed


def split_dataset(
    source_images: Path, source_labels: Path, dest_root: Path, train_ratio: float = 0.8, val_ratio: float = 0.15
) -> None:
    """
    Split a flat (images/, labels/) pair into dest_root/{train,valid,test}/{images,labels}.
    test_ratio = 1 - train_ratio - val_ratio.
    """
    import random

    random.seed(42)
    image_files = sorted(p for p in source_images.glob("*") if p.is_file())
    random.shuffle(image_files)

    n = len(image_files)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    splits = {
        "train": image_files[:n_train],
        "valid": image_files[n_train : n_train + n_val],
        "test": image_files[n_train + n_val :],
    }

    for split_name, files in splits.items():
        img_dest = dest_root / split_name / "images"
        lbl_dest = dest_root / split_name / "labels"
        img_dest.mkdir(parents=True, exist_ok=True)
        lbl_dest.mkdir(parents=True, exist_ok=True)
        for img_path in files:
            label_path = source_labels / (img_path.stem + ".txt")
            shutil.copy2(img_path, img_dest / img_path.name)
            if label_path.exists():
                shutil.copy2(label_path, lbl_dest / label_path.name)
            else:
                logger.warning("No label found for %s — copying image with empty label", img_path.name)
                (lbl_dest / label_path.name).touch()

    logger.info(
        "Split %d images -> train=%d valid=%d test=%d", n, len(splits["train"]), len(splits["valid"]), len(splits["test"])
    )
