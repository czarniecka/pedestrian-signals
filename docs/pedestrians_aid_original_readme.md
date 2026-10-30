# Pedestrians Aid: first detection model

English translation of the README imported from the original repository.
Environment and hard-link descriptions below refer to that original repository.
See `IMPORTED_WORK.md` for setup after migration.

Current scope: bounding boxes for crosswalks and pedestrian signals, with separate state classes.
Manual annotation in Label Studio.

## Files

- `data/raw/images/`: 169 original JPG images and 15 MP4 videos. Import JPGs into Label Studio.
- `configs/label_studio.xml`: paste into Settings > Labeling Interface > Code.
- `docs/ANNOTATION_GUIDE.md`: annotation and export rules.
- `data/exports/label_studio/`: YOLO and JSON export directory.
- `data/dataset/`: manual annotations from the PNW project, 115 train images and 37 val images.
- `configs/classes.yaml`: class definitions for the new training run.
- `weights/yolov8n.pt`: preserved base detector weights.
- `docs/SPECIFICATION.md`: original broader specification, which does not define the current PoC scope.

## Workflow

1. Paste the XML configuration into the Label Studio project and import JPG files.
2. Annotate images according to the guide.
3. Export YOLO and JSON. Check the export's class mapping.
4. Split data by intersection or session. Place images in `data/dataset/images/{train,val}`
   and labels in `data/dataset/labels/{train,val}`. The export does not create this split.
5. Run from the project directory:

```sh
python scripts/train_yolo.py --epochs 60 --batch 8 --imgsz 640
```

Training augmentation transforms images and boxes together. Hue shifts are disabled.

## Prepared dataset and first training run

`scripts/prepare_label_studio_dataset.py` reads annotations and local database data
in read-only mode. It selects the latest approved, non-cancelled bounding-box annotation
for each task and saves a JSON copy in `data/exports/label_studio/annotated_tasks_snapshot.json`.
It does not read credentials or modify Label Studio.

The selection includes 152 images containing objects. The other 17 have no approved annotations.
The split is recorded in `data/dataset/split_manifest.json`. Geometry checks, class counts
and duplicate checks are in `data/dataset/preparation_report.json`.
The whole yellow-crossing recording from 2026-08-16 and the UUID-named image of that location
were assigned to val. City-center sequences remain together in train, including across cameras.
This is a conservative location-based split established by visual review.
Validation covers one location. There is no separate final test yet.

Preprocessing: RGB, longest side at most 1920 px, preserved aspect ratio,
no cropping or hue shifts. Normalized boxes remain aligned with the images.
The script refuses to overwrite an existing dataset to protect the split and labels.

```sh
python scripts/train_yolo.py --epochs 80 --patience 25 --batch 4 --imgsz 960 --device 0 --name manual_scene_split_v1_batch4
```

Training-only augmentations: rotation +/-5 degrees, translation 5%, scale 0.8-1.2,
moderate brightness/saturation. Hue shifts, flips, mosaic, mixup and optional
Albumentations augmentations, including grayscale, are disabled.
Training uses pretrained YOLOv8n, an RTX 4060 and seed 42.
`traffic_light_unknown` has no examples and cannot be assessed.
A positive-only dataset cannot evaluate false alarms on empty scenes.

## Cleanup on 2026-10-14

The old editor, pseudo-labels, previous datasets, training results, segmentation models,
YOLO-World and the old experiment log are in `archive/legacy_2026-10-14/`.
The previous README, nine-class configuration and training script are preserved there too.
The archive is local and ignored by Git. Do not copy old labels into the new dataset
because they do not match the new class definitions.

Download and conversion tools were retained. Convert orientation and format before annotation,
not on images with completed boxes.

## Local Label Studio

Run from the project directory:

```sh
python scripts/start_label_studio.py
```

Address: http://localhost:8080. Initial setup requires a local account.
The application is installed in `.venv-label-studio/`. Its database and project files
are in `.label-studio/`. Preserve that directory because it contains saved annotations.
Local file access is restricted to `data/raw/images/`.

The PNW project received 169 images: the first 20 through upload and the remaining 149
through the `Raw photos` Local Files source storage.
In the original repository, `data/raw/images/label_studio/` contains hard links to those
149 JPGs. Do not move it or modify images after annotation. Hard links share the originals'
contents and do not require additional image-copy storage.
Do not reimport the prepared JSON files into the same project because this would create duplicates.
