"""
Synthesizes weather-diverse training data by applying realistic weather
effects to existing clear-weather images.

Why this exists: the stated use case is detecting ships in all weather
conditions, but no single public dataset gives real, labeled ship images
across fog/rain/snow/night for your full 20-class taxonomy — see the
notes in download_datasets.py. This script closes that gap the way
several published ship-detection papers do it (e.g. the "SeaShips_weather"
approach): apply weather transforms on top of clear-weather images you
already have. Bounding boxes are unaffected (these are pixel-level
transforms — no crop/rotate/perspective here), so YOLO labels are just
copied over unchanged.

Only augments the TRAIN split — never valid/test, so evaluation still
measures performance on genuine, unmodified images.

Usage:
    python augment_weather.py --dataset-dir ../../datasets --variants-per-image 2
"""

from __future__ import annotations

import argparse
import logging
import random
import shutil
import sys
from pathlib import Path

import albumentations as A
import cv2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Each entry: (name, transform). Kept as standalone single-effect transforms
# rather than one randomly-combining pipeline, so the output filename
# (e.g. "_wx-fog") tells you exactly which condition each image represents —
# useful later if you want to check per-weather-condition accuracy.
WEATHER_TRANSFORMS: dict[str, A.Compose] = {
    "fog": A.Compose([A.RandomFog(fog_coef_range=(0.3, 0.7), alpha_coef=0.08, p=1.0)]),
    "rain": A.Compose([A.RandomRain(rain_type="heavy", blur_value=4, brightness_coefficient=0.8, p=1.0)]),
    "snow": A.Compose([A.RandomSnow(snow_point_range=(0.15, 0.35), brightness_coeff=1.8, p=1.0)]),
    "night": A.Compose(
        [
            A.RandomBrightnessContrast(brightness_limit=(-0.55, -0.35), contrast_limit=(-0.1, 0.1), p=1.0),
            A.RandomShadow(shadow_intensity_range=(0.3, 0.5), p=0.6),
        ]
    ),
    "haze_glare": A.Compose(
        [
            A.RandomFog(fog_coef_range=(0.15, 0.35), alpha_coef=0.06, p=0.8),
            A.RandomSunFlare(flare_roi=(0, 0, 1, 0.5), src_radius=150, p=0.5),
        ]
    ),
}


def augment_split(images_dir: Path, labels_dir: Path, weather_types: list[str], variants_per_image: int) -> int:
    image_paths = sorted(p for p in images_dir.glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"})
    if not image_paths:
        logger.error("No images found in %s", images_dir)
        return 0

    n_written = 0
    for img_path in image_paths:
        label_path = labels_dir / f"{img_path.stem}.txt"
        image = cv2.imread(str(img_path))
        if image is None:
            logger.warning("Could not read %s — skipping", img_path.name)
            continue

        chosen = random.sample(weather_types, k=min(variants_per_image, len(weather_types)))
        for weather in chosen:
            transform = WEATHER_TRANSFORMS[weather]
            augmented = transform(image=image)["image"]

            out_stem = f"{img_path.stem}_wx-{weather}"
            out_image_path = images_dir / f"{out_stem}{img_path.suffix}"
            out_label_path = labels_dir / f"{out_stem}.txt"

            cv2.imwrite(str(out_image_path), augmented)
            if label_path.exists():
                shutil.copy2(label_path, out_label_path)
            else:
                out_label_path.touch()  # background/no-ship image — empty label is correct
            n_written += 1

    return n_written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset-dir", type=Path, default=Path("../../datasets"))
    parser.add_argument(
        "--weather-types",
        nargs="*",
        default=list(WEATHER_TRANSFORMS.keys()),
        choices=list(WEATHER_TRANSFORMS.keys()),
    )
    parser.add_argument(
        "--variants-per-image",
        type=int,
        default=2,
        help="How many different weather variants to generate per source image (each drawn without replacement from --weather-types)",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    train_images = args.dataset_dir / "train" / "images"
    train_labels = args.dataset_dir / "train" / "labels"
    if not train_images.exists():
        logger.error(
            "No train/images/ found under %s — run prepare_dataset.py first.", args.dataset_dir
        )
        sys.exit(1)

    logger.info(
        "Augmenting %s with weather types %s (%d variants/image)...",
        train_images, args.weather_types, args.variants_per_image,
    )
    n_written = augment_split(train_images, train_labels, args.weather_types, args.variants_per_image)
    logger.info("Wrote %d weather-augmented image+label pairs into %s", n_written, train_images)
    logger.info(
        "valid/ and test/ were NOT touched — evaluation still runs on genuine, unmodified images."
    )


if __name__ == "__main__":
    main()
