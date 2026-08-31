"""
Trains the ship detector/classifier on a single cloud GPU (Colab, AWS EC2
GPU instance, Paperspace, etc.).

Defaults are tuned for a single mid-range GPU (e.g. Colab's T4/A100, or an
AWS g4dn/g5 instance) — mixed precision on, moderate batch size, resumable.
Adjust --batch down if you hit CUDA OOM on a smaller card (e.g. T4 16GB).

Usage:
    python train.py --data ../../datasets/naval_dataset.yaml --epochs 150

Resume an interrupted run:
    python train.py --resume ../../models/weights/last.pt

Export after training:
    python train.py --export-only --weights ../../models/weights/best.pt
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def check_gpu() -> str:
    import torch

    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        logger.info("CUDA GPU detected: %s", name)
        return "0"
    logger.warning("No CUDA GPU detected — falling back to CPU. Training will be very slow; "
                    "confirm your cloud instance actually attached a GPU runtime.")
    return "cpu"


def train(args: argparse.Namespace) -> None:
    from ultralytics import YOLO

    device = args.device or check_gpu()

    if args.resume:
        model = YOLO(args.resume)
        logger.info("Resuming training from %s", args.resume)
        model.train(resume=True)
        return

    # Start from a pretrained checkpoint (transfer learning) rather than
    # random weights — much faster convergence on a domain-specific set
    # like ships, especially with limited cloud GPU hours.
    model = YOLO(args.base_model)

    model.train(
        data=str(args.data),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        amp=True,                    # mixed precision — big speed/memory win on cloud GPUs
        patience=args.patience,      # early stopping
        optimizer="auto",
        cos_lr=True,
        # Augmentation — ships appear at many scales/angles/lighting conditions
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.0,
        flipud=0.1,                  # some aerial/satellite shots are meaningfully flipped
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,
        hsv_h=0.015,
        hsv_s=0.6,                   # water/sky lighting varies a lot — more saturation jitter than default
        hsv_v=0.4,
        project=str(args.output_dir),
        name=args.run_name,
        exist_ok=True,
        save=True,
        save_period=args.save_period,
        plots=True,                  # confusion matrix, PR curves, etc. written to runs dir
        val=True,
    )

    best_weights = Path(args.output_dir) / args.run_name / "weights" / "best.pt"
    dest = Path(args.weights_dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if best_weights.exists():
        import shutil

        shutil.copy2(best_weights, dest)
        logger.info("Copied best weights to %s (this is what backend/inference/detector.py loads)", dest)
    else:
        logger.error("Expected best.pt at %s but it wasn't found — check the run output above for errors.", best_weights)


def evaluate(args: argparse.Namespace) -> None:
    """Run validation and print mAP/precision/recall — also called automatically after train()."""
    from ultralytics import YOLO

    model = YOLO(args.weights)
    metrics = model.val(data=str(args.data), device=args.device or check_gpu())
    logger.info("mAP50: %.4f  mAP50-95: %.4f  Precision: %.4f  Recall: %.4f",
                metrics.box.map50, metrics.box.map, metrics.box.mp, metrics.box.mr)


def export(args: argparse.Namespace) -> None:
    """Export trained weights to ONNX (useful for faster CPU inference / non-Python deployment)."""
    from ultralytics import YOLO

    model = YOLO(args.weights)
    export_path = model.export(format="onnx", dynamic=True, simplify=True)
    logger.info("Exported ONNX model to %s", export_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", type=Path, default=Path("../../datasets/naval_dataset.yaml"))
    parser.add_argument("--base-model", default="yolo11m.pt", help="Pretrained checkpoint to fine-tune from")
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16, help="Lower to 8 if you hit CUDA OOM on a smaller GPU")
    parser.add_argument("--patience", type=int, default=25, help="Early stopping patience (epochs w/o improvement)")
    parser.add_argument("--save-period", type=int, default=10, help="Checkpoint every N epochs (survives Colab disconnects)")
    parser.add_argument("--device", default=None, help="Override auto-detected device, e.g. '0' or 'cpu'")
    parser.add_argument("--output-dir", default="../../models/runs")
    parser.add_argument("--run-name", default="naval_yolo")
    parser.add_argument("--weights-dest", default="../../models/weights/best.pt")
    parser.add_argument("--resume", default=None, help="Path to last.pt to resume an interrupted run")
    parser.add_argument("--evaluate-only", action="store_true")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--weights", default="../../models/weights/best.pt", help="Used by --evaluate-only/--export-only")
    args = parser.parse_args()

    if args.export_only:
        export(args)
    elif args.evaluate_only:
        evaluate(args)
    else:
        train(args)
        evaluate(argparse.Namespace(weights=args.weights_dest, data=args.data, device=args.device))


if __name__ == "__main__":
    sys.exit(main())
