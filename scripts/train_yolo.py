"""Train or fine-tune YOLO on the prepared bounding-box dataset.

Targets are crosswalks and pedestrian signal states.

Usage:
    python scripts/train_yolo.py --epochs 50 --batch 16 --imgsz 640 --model yolov8n.pt
"""

import argparse
import json
from pathlib import Path
from ultralytics import YOLO
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "configs" / "classes.yaml"


def disable_optional_color_transforms(trainer):
    """Keep configured HSV augmentation, but disable optional grayscale/CLAHE.

    Ultralytics may add these implicitly when Albumentations is installed.
    Grayscale would erase the target signal color.
    """
    def visit(transform):
        if type(transform).__name__ == 'Albumentations':
            transform.transform = None
        for child in getattr(transform, 'transforms', []):
            visit(child)
    visit(trainer.train_loader.dataset.transforms)


def main():
    parser = argparse.ArgumentParser(description="Train a YOLO model for Pedestrians Aid")
    parser.add_argument(
        "--model",
        type=str,
        default=str(PROJECT_ROOT / "weights" / "yolov8n.pt"),
        help="Base model for transfer learning (e.g. yolov8n.pt, yolo11n.pt, yolov8s.pt)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs (default: 50)"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size (default: 16)"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size (default: 640)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Compute device (0 for CUDA, or 'cpu')"
    )

    parser.add_argument('--patience', type=int, default=25)
    parser.add_argument('--name', default='pedestrians_aid_yolo')
    args = parser.parse_args()

    data_config = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    dataset_path = Path(data_config["path"])
    if not dataset_path.is_absolute():
        dataset_path = PROJECT_ROOT / dataset_path
    data_config["path"] = str(dataset_path.resolve())
    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    for split in ("train", "val"):
        image_dir = dataset_path / data_config[split]
        if not image_dir.exists() or not any(
            p.is_file() and p.suffix.lower() in image_extensions for p in image_dir.iterdir()
        ):
            parser.error(f"No images in {image_dir}. Prepare a Label Studio export and train/val split.")

    resolved_config = PROJECT_ROOT / "runs" / "dataset_resolved.yaml"
    resolved_config.parent.mkdir(parents=True, exist_ok=True)
    resolved_config.write_text(yaml.safe_dump(data_config, sort_keys=False), encoding="utf-8")

    print(f"[*] Starting training...")
    print(f" - Base model: {args.model}")
    print(f" - Configuration: {CONFIG_FILE.resolve()}")
    print(f" - Epochs: {args.epochs}, Batch: {args.batch}, ImgSz: {args.imgsz}")

    model = YOLO(args.model)
    model.add_callback('on_pretrain_routine_end', disable_optional_color_transforms)

    results = model.train(
        data=str(resolved_config),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        plots=True,
        save=True,
        project=str(PROJECT_ROOT / "runs" / "train"),
        name=args.name,
        patience=args.patience,
        workers=0,
        seed=42,
        hsv_h=0.0,
        hsv_s=0.2,
        hsv_v=0.2,
        degrees=5.0,
        translate=0.05,
        scale=0.2,
        flipud=0.0,
        fliplr=0.0,
        mosaic=0.0,
        mixup=0.0,
    )

    per_class = {}
    for i, cls in enumerate(results.box.ap_class_index):
        p, r, ap50, ap = results.box.class_result(i)
        per_class[data_config['names'][int(cls)]] = {
            'precision': float(p), 'recall': float(r),
            'mAP50': float(ap50), 'mAP50_95': float(ap),
        }
    summary = {
        'metrics': {k: float(v) for k, v in results.results_dict.items()},
        'per_class': per_class,
        'best_weights': str(model.trainer.best),
        'device': args.device,
        'validation': 'Whole yellow-crossing location held out; no separate final test set.',
        'unassessed_classes': [n for n in data_config['names'].values() if n not in per_class],
    }
    matrix = getattr(model.trainer.validator, 'confusion_matrix', None)
    if matrix is not None:
        summary['confusion_matrix'] = matrix.matrix.tolist()
        summary['confusion_matrix_note'] = 'Rows: predicted class; columns: true class; last row/column: background. Thresholds follow Ultralytics validation defaults.'
    (Path(model.trainer.save_dir) / 'experiment_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8')

    print("\n[OK] Training complete!")
    print(f"Best weights saved to: {model.trainer.best if hasattr(model, 'trainer') else 'runs/train/pedestrians_aid_yolo/weights/best.pt'}")


if __name__ == "__main__":
    main()
