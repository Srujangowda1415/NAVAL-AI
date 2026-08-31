"""
Converts raw downloaded datasets (datasets/raw/<DatasetName>/) into the
unified YOLO-format dataset at datasets/{train,valid,test}/{images,labels}/,
matching datasets/naval_dataset.yaml.

Most of these public ship datasets (SeaShips, HRSC2016, the Kaggle mirrors)
ship Pascal-VOC-style XML annotations, so the default converter here handles
that format. If a dataset you download uses a different annotation format
(some Kaggle sets are just class-labeled folders with no bounding boxes —
those are only useful for a classifier, not a detector, and are skipped
with a warning), add a small converter function following the same pattern
as `convert_voc_xml_dataset` below.

Usage:
    python prepare_dataset.py --raw-dir ../../datasets/raw --out-dir ../../datasets
"""

from __future__ import annotations

import argparse
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from dataset_utils import (
    dedupe_images,
    load_class_names,
    normalize_class_name,
    split_dataset,
    voc_bbox_to_yolo,
    write_yolo_label,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def convert_voc_xml_dataset(dataset_dir: Path, staging_images: Path, staging_labels: Path) -> tuple[int, int]:
    """
    Walk a dataset directory looking for (image, matching .xml annotation)
    pairs anywhere inside it, convert boxes to YOLO format, and copy both
    into the flat staging dirs. Returns (images_converted, boxes_converted).
    """
    import shutil

    known_classes = load_class_names()
    xml_files = list(dataset_dir.rglob("*.xml"))
    if not xml_files:
        logger.warning("No .xml annotations found under %s — skipping (wrong format or unbuilt classifier-only set)", dataset_dir)
        return 0, 0

    staging_images.mkdir(parents=True, exist_ok=True)
    staging_labels.mkdir(parents=True, exist_ok=True)

    n_images, n_boxes = 0, 0
    for xml_path in xml_files:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        size_el = root.find("size")
        if size_el is None:
            continue
        img_w = int(size_el.findtext("width", "0"))
        img_h = int(size_el.findtext("height", "0"))
        if img_w == 0 or img_h == 0:
            continue

        filename = root.findtext("filename") or (xml_path.stem + ".jpg")
        image_path = xml_path.parent / filename
        if not image_path.exists():
            # try common alternate extensions
            for ext in (".jpg", ".jpeg", ".png", ".bmp"):
                candidate = xml_path.with_suffix(ext)
                if candidate.exists():
                    image_path = candidate
                    break
        if not image_path.exists():
            logger.warning("Image not found for annotation %s — skipping", xml_path.name)
            continue

        boxes: list[tuple[int, float, float, float, float]] = []
        for obj in root.findall("object"):
            raw_name = obj.findtext("name", "")
            cls_name = normalize_class_name(raw_name, known_classes)
            if cls_name is None:
                continue
            bnd = obj.find("bndbox")
            if bnd is None:
                continue
            xmin = float(bnd.findtext("xmin", "0"))
            ymin = float(bnd.findtext("ymin", "0"))
            xmax = float(bnd.findtext("xmax", "0"))
            ymax = float(bnd.findtext("ymax", "0"))
            xc, yc, w, h = voc_bbox_to_yolo(xmin, ymin, xmax, ymax, img_w, img_h)
            boxes.append((known_classes[cls_name], xc, yc, w, h))

        if not boxes:
            continue  # skip images with no recognized ships rather than writing empty labels for a real dataset

        dest_image = staging_images / f"{dataset_dir.name}_{image_path.name}"
        dest_label = staging_labels / f"{dataset_dir.name}_{image_path.stem}.txt"
        shutil.copy2(image_path, dest_image)
        write_yolo_label(dest_label, boxes)
        n_images += 1
        n_boxes += len(boxes)

    logger.info("%s: converted %d images, %d boxes", dataset_dir.name, n_images, n_boxes)
    return n_images, n_boxes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=Path("../../datasets/raw"))
    parser.add_argument("--out-dir", type=Path, default=Path("../../datasets"))
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    args = parser.parse_args()

    if not args.raw_dir.exists():
        logger.error("Raw dir %s doesn't exist. Run download_datasets.py first.", args.raw_dir)
        sys.exit(1)

    staging = args.out_dir / "_staging"
    staging_images = staging / "images"
    staging_labels = staging / "labels"

    total_images, total_boxes = 0, 0
    for dataset_dir in sorted(p for p in args.raw_dir.iterdir() if p.is_dir()):
        n_images, n_boxes = convert_voc_xml_dataset(dataset_dir, staging_images, staging_labels)
        total_images += n_images
        total_boxes += n_boxes

    if total_images == 0:
        logger.error(
            "No images converted. Check that datasets/raw/ actually contains extracted "
            "datasets with Pascal-VOC XML annotations, or add a converter for the format "
            "you have (see convert_voc_xml_dataset as a template)."
        )
        sys.exit(1)

    logger.info("Total staged: %d images, %d boxes across all datasets", total_images, total_boxes)

    removed = dedupe_images(staging_images)
    logger.info("Removed %d exact-duplicate images", removed)

    split_dataset(staging_images, staging_labels, args.out_dir, args.train_ratio, args.val_ratio)
    logger.info("Done. Dataset ready at %s (train/valid/test). naval_dataset.yaml already points here.", args.out_dir)


if __name__ == "__main__":
    main()
