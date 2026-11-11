# First model after manual annotation, 2026-10-14

YOLOv8n was trained from COCO weights on an RTX 4060. The best checkpoint is from epoch 47.
Early stopping ended training after 72 epochs. Training itself took about 22.1 minutes.

## Data and split protection

The local PNW Label Studio database was read in read-only mode to retrieve 152 approved
bounding-box tasks with 357 objects. The remaining 17 tasks had no approved annotations
and were excluded as requested. Neither annotations in the app nor original images were changed.

- Train: 115 images, 281 objects. Val: 37 images, 76 objects.
- The entire yellow-crossing session from 2026-08-16 and the UUID-named view of that location are in val.
- City-center sequences stay together in train, including across cameras and dates.
- Groups, filenames, original SHA-256 hashes and decoded processed-image hashes were checked for overlap.
  The minimum train-to-val dHash distance is 15/64. This additional check does not replace scene review.
- The split uses visual review and filenames rather than GPS metadata. It is recorded in `data/dataset/split_manifest.json`.
- No random frame split or validation augmentation was used.

## Preprocessing and training

RGB, longest side reduced to at most 1920 px without upscaling, preserved aspect ratio,
JPEG95. Images were neither cropped nor reoriented. Annotation dimensions and EXIF checks
passed for every image. Five boxes extending slightly outside the image were clipped to
its boundaries. These changes are recorded in `preparation_report.json`.

Model input: 960 px, batch 4, seed 42, AdamW, at most 80 epochs, patience 25, workers 0.
An initial batch of 8 was too slow while the GPU was shared with a game, so the actual experiment used batch 4.

Training augmentations transform images and boxes together: rotation +/-5 degrees,
translation 5%, scale 0.8-1.2, moderate brightness and saturation, HSV S/V 0.2.
Hue shifts, flips, mosaic, mixup and optional Albumentations transforms, including grayscale, were disabled.

Environment: Python 3.13.7, PyTorch 2.9.0+cu128, Ultralytics 8.4.143.

## Validation results for the best weights

Overall mAP50 is **0.810**, and mAP50-95 is **0.516**.
These are not percentages of correct road-crossing decisions.

| Class | Val objects | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|---:|
| Crosswalk | 37 | 0.861 | 0.568 | 0.613 | 0.392 |
| Red pedestrian light | 27 | 0.842 | 0.815 | 0.887 | 0.507 |
| Green pedestrian light | 10 | 0.869 | 1.000 | 0.995 | 0.645 |
| No illuminated signal | 2 | 0.344 | 0.500 | 0.745 | 0.522 |

Precision and recall follow the threshold-selection procedure used by Ultralytics.
They should not be interpreted as results at exactly confidence=0.25, which was used for previews.

## Findings and limitations

Signal recognition is promising as an initial experiment. Red-light recall is about 0.815.
Green-light recall is 1.0 on only 10 objects. This does not establish reliability or the absence of false green indications.

Crosswalk detection is weaker, with recall about 0.568 and mAP50 about 0.613.
Validation includes temporary yellow markings absent from the training sequence,
providing a real test of changed scene appearance.

Unlit signals have only 10 training objects and 2 validation objects, so conclusions
for this class are very unstable. `traffic_light_unknown` has no examples and remains
untested. It should not be considered trained.

Validation mainly covers one held-out location with many correlated frames. It was also
used to select the checkpoint. There is no separate untouched final test set.
Do not directly compare these numbers with the old 24/6 experiment because the data,
classes and split have changed.

Only images containing objects were used, as requested. False alarms on empty scenes
were not evaluated. Next steps are new locations, ESP-CAM material, difficult or unreadable
signals, and a separate test including negative images.

## Files

- Weights: `runs/train/manual_scene_split_v1_batch4/weights/best.pt`
- Exact metrics: `runs/train/manual_scene_split_v1_batch4/experiment_summary.json`
- Prediction preview at confidence 0.25: `runs/train/manual_scene_split_v1_batch4/validation_predictions.jpg`
- Training curves and confusion matrix: `results.png` and `confusion_matrix.png` in the experiment directory.
- Annotation snapshot: `data/exports/label_studio/annotated_tasks_snapshot.json`
- Data audit: `data/dataset/preparation_report.json` and `split_manifest.json`
