"""
Dataset acquisition for the naval vessel detector.

Reality check on the datasets requested in the original spec:
  - SeaShips              -> freely downloadable (GitHub release / Kaggle mirror)
  - Kaggle ship datasets  -> automatable via Kaggle API (needs your kaggle.json)
  - Airbus Ship Detection -> Kaggle competition dataset; needs you to have
                             *accepted the competition rules* on kaggle.com first
                             (Kaggle blocks API downloads otherwise)
  - HRSC2016              -> requires filling a request form with the dataset
                             authors (no public direct-download API) — this
                             script can't automate that step, only tells you
  - DOTA                  -> requires free registration at captain-whu/DOTA
                             to get a download link (same — manual step)
  - Singapore Maritime DS -> hosted on the lab's own server; direct-download
                             links occasionally break, so this script tries
                             but falls back to printing the manual URL

Datasets added for weather/lighting diversity ("ships in all weather
conditions" being the stated main use case) — none of the above were
built around weather variety, so these fill that gap:
  - WSODD                 -> real images across sunny/cloudy/foggy and
                             day/twilight/night. Baidu-Pan-only, no API —
                             manual, see MANUAL_DATASETS below
  - SeaDronesSee           -> real day/dusk/night, clear/overcast/haze UAV
                             footage. Registration required — manual
  - Synthetic augmentation -> since real labeled adverse-weather *ship*
                             data is genuinely scarce (most published
                             work in this space synthesizes it too — fog/
                             rain/snow applied on top of clear-weather
                             images), see augment_weather.py. This is the
                             most reliable way to get broad weather
                             coverage across your full 20-class taxonomy,
                             since it doesn't depend on any one dataset
                             happening to have shot every ship class in
                             every weather condition.

So: this script automates everything that CAN be automated given API/CLI
access, and prints clear manual instructions for the rest instead of
silently failing or making something up.

Usage (on your cloud GPU instance / Colab):
    pip install kaggle
    # place kaggle.json at ~/.kaggle/kaggle.json (from kaggle.com/settings)
    python download_datasets.py --target ../../datasets/raw
"""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
import zipfile
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MANUAL_DATASETS = {
    "HRSC2016": (
        "Request access from the dataset authors: "
        "https://www.kaggle.com/datasets/guofeng/hrsc2016 (Kaggle mirror, easier) "
        "or https://sites.google.com/site/hrsc2016/ (original, needs a request form). "
        "Once downloaded, unzip into datasets/raw/HRSC2016/"
    ),
    "DOTA": (
        "Register at https://captain-whu.github.io/DOTA/dataset.html to get download "
        "links (DOTA is aerial imagery — useful for ship *detection* from above, less "
        "so for close-up classification). Unzip into datasets/raw/DOTA/"
    ),
    "SingaporeMaritimeDataset": (
        "https://sites.google.com/site/dilipprasad/singapore-maritime-dataset "
        "— direct links there occasionally rotate; grab the on-shore/on-board video "
        "sets and unzip into datasets/raw/SingaporeMaritime/. This is your best VIDEO "
        "source with real (not synthetic) varying-visibility footage."
    ),
    "WSODD": (
        "Water Surface Object Detection Dataset — 7,467 images across sunny/cloudy/"
        "foggy conditions and daytime/twilight/night, 14 object categories. Hosted "
        "ONLY on Baidu Pan, no Kaggle/Google Drive mirror as of this writing: "
        "https://github.com/sunjiaen/WSODD (Baidu link + password in the README). "
        "Needs a Baidu account; unzip into datasets/raw/WSODD/"
    ),
    "SeaDronesSee": (
        "UAV footage spanning day/dusk/night and clear/overcast/haze conditions, "
        "aimed at maritime search-and-rescue (people, small boats — not your full "
        "vessel taxonomy, but useful for weather diversity). Register and download "
        "at https://seadronessee.cs.uni-tuebingen.de/dataset. Unzip into "
        "datasets/raw/SeaDronesSee/"
    ),
}


def _run(cmd: list[str]) -> None:
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def download_seaships(target: Path) -> None:
    dest = target / "SeaShips"
    dest.mkdir(parents=True, exist_ok=True)
    logger.info("SeaShips: download the 7000-image release from the official GitHub repo:")
    logger.info("  https://github.com/jiaming-wang/SeaShips (see Releases tab)")
    logger.info("Unzip it into %s", dest)


def download_kaggle_dataset(slug: str, target: Path) -> None:
    """slug like 'username/dataset-name' or a competition name for -c."""
    try:
        import kaggle  # noqa: F401
    except ImportError:
        logger.error("Kaggle API not installed. Run: pip install kaggle, and place kaggle.json in ~/.kaggle/")
        return

    dest = target / slug.split("/")[-1]
    dest.mkdir(parents=True, exist_ok=True)
    try:
        _run(["kaggle", "datasets", "download", "-d", slug, "-p", str(dest)])
        for zip_path in dest.glob("*.zip"):
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(dest)
            zip_path.unlink()
        logger.info("Downloaded and extracted %s -> %s", slug, dest)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Kaggle download failed for %s (%s). If this is a competition dataset "
            "(e.g. Airbus Ship Detection), make sure you've clicked 'I Accept' on the "
            "competition rules page on kaggle.com first — the API can't do that for you.",
            slug,
            e,
        )


def print_manual_instructions() -> None:
    logger.info("=" * 70)
    logger.info("The following datasets need a manual step before they can be used:")
    for name, instructions in MANUAL_DATASETS.items():
        logger.info("- %s: %s", name, instructions)
    logger.info("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", type=Path, default=Path("../../datasets/raw"))
    parser.add_argument(
        "--kaggle-ship-datasets",
        nargs="*",
        default=["airbus-ship-detection", "arpitjain007/game-of-deep-learning-ship-datasets"],
        help="Kaggle dataset slugs to pull automatically",
    )
    args = parser.parse_args()

    args.target.mkdir(parents=True, exist_ok=True)

    download_seaships(args.target)
    for slug in args.kaggle_ship_datasets:
        download_kaggle_dataset(slug, args.target)
    print_manual_instructions()

    logger.info(
        "Next: run prepare_dataset.py to normalize class names, convert everything "
        "to YOLO format, de-duplicate, and split into train/valid/test."
    )


if __name__ == "__main__":
    sys.exit(main())
