# Imported data and experiments

Copied from `pedestrians_aid` on 2026-10-30. The source was left unchanged.
`migration_manifest.json` records paths, sizes and SHA-256 hashes of the files at import time.
The Label Studio database was copied with SQLite's backup mechanism.
English translations subsequently changed some text files. The summary PDF remains in Polish.
Import hashes describe the original copies, not the translated versions.
The original PowerShell launcher was replaced by `scripts/start_label_studio.py`.

## Structure

| Directory | Contents |
|---|---|
| `src/pedestrian_signals/` | Existing application skeleton |
| `data/raw/images/` | Original images and videos, including the Label Studio local-files directory |
| `data/dataset/` | Manual YOLO labels, 115 train images, 37 val images, 4 test_2 images, split manifest and audit |
| `data/exports/label_studio/` | JSON annotation snapshot and historical import files |
| `data/processed/` | Contact sheets for reviewing images and labels |
| `configs/` | Five classes and the Label Studio interface |
| `scripts/` | Dataset preparation, training, inference, image download/conversion and Label Studio startup |
| `weights/` | Base YOLOv8n and YOLO26n weights. A weight file alone does not establish a completed experiment. |
| `runs/train/manual_scene_split_v1_batch4/` | Main training run, best.pt, last.pt, metrics, charts and previews |
| `runs/inference/test_2_2026-10-15/` | Predictions at a new location and JSON output |
| `archive/legacy_2026-10-14/` | Older data, pseudo-labels, scripts, detection and segmentation experiments |
| `archive/incomplete_training_start_2026-10-14/` | Incomplete startup attempt, not a separately trained model |
| `output/pdf/` | Project summary |
| `.label-studio/` | Local database and uploaded-file backup, excluded from Git |

## Models and results

The main checkpoint is `runs/train/manual_scene_split_v1_batch4/weights/best.pt`.
After manual annotation, YOLOv8n achieved mAP50 0.810 and mAP50-95 0.516.
The best epoch was 47, and training stopped after 72 epochs.
See `TRAINING_BASELINE.md` for details and limitations.
Validation covers one held-out location. There is no separate final test.
`OOD_TEST_2.md` describes errors at a new location, including confusion between
vehicle and pedestrian signals.

Older checkpoints and their original results are also preserved locally:

- Detection: `archive/legacy_2026-10-14/runs/detect/runs/train/yolov8n_detect/`.
- Segmentation: `archive/legacy_2026-10-14/runs/segment/runs/train/yolov8n_seg/`.
- YOLO-World: base weights in the archive and the old automatic annotation script.

The archive uses the former nine-class definition. Do not combine its labels with
the current five-class dataset. Historical JSON files, training arguments and documents
retain original paths as experiment records. The current training script resolves paths
relative to the new repository and recreates `runs/dataset_resolved.yaml`.

## Running the tools

Run commands from the repository root. The application package requires Python >=3.14.
Use a separate Python 3.13 environment for imported experiments, matching the original
training description. The existing `pyproject.toml` and `uv.lock` were left unchanged.

```sh
uv venv --python 3.13 .venv-ml
uv pip install --python .venv-ml -r requirements-ml.txt
uv run --no-project --python .venv-ml python scripts/train_yolo.py --epochs 80 --patience 25 --batch 4 --imgsz 960 --device 0 --name manual_scene_split_v2
uv run --no-project --python .venv-ml python scripts/inspect_baseline.py --weights runs/train/manual_scene_split_v1_batch4/weights/best.pt --source data/dataset/images/test_2 --limit 4 --device cpu --output runs/inference/test_2_recheck/predictions.jpg
```

The dependency list does not exactly reproduce the previous CUDA installation.
For GPU use, select a PyTorch build compatible with the local driver.
Original training versions are recorded in `TRAINING_BASELINE.md`.
The dataset-preparation script refuses to overwrite existing images. Preserve the current split.
Convert images before annotation. Do not modify already labeled images.

## Label Studio

Annotations are available in `data/exports/label_studio/annotated_tasks_snapshot.json`
and as YOLO labels. A consistent database backup and 20 uploads were also preserved.
The virtual environment, `.env` file and logs were not copied.
The database contains local accounts and should remain outside Git.
Recreate the old repository's virtual environment:

```sh
uv venv --python 3.13 .venv-label-studio
uv pip install --python .venv-label-studio label-studio
python scripts/start_label_studio.py
```

Before synchronizing storage, check its directory in Label Studio settings.
The historical entry may point to the old repository. Set the new `data/raw/images/label_studio` path.
Do not reimport `import_*.json` into the copied project because this creates duplicates.
Starting the application and running its database migrations were not part of the import.

## Files tracked in Git

Code, configuration, documentation, original images, videos, the prepared dataset,
annotation exports, previews, base weights and current-training checkpoints are tracked.
The repository also includes the current model's full results and the summary PDF.
Caches, machine-specific absolute-path configuration, environments, the Label Studio
database and the old archive remain local and ignored. Back up the database and archive separately.
The import manifest describes every copied file, including those left outside Git.
