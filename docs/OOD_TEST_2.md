# New test_2 images, 2026-10-15

The unchanged `manual_scene_split_v1_batch4/weights/best.pt` model was run on four PNG
images from `data/dataset/images/test_2`. Settings: GPU, imgsz=960, confidence=0.25,
default NMS. No training, weight changes, test-time augmentation or addition of these
images to the training set took place. No labels were used and no mAP or recall was calculated.

The images show the same new location with small changes in framing and signal state.
They are four correlated views rather than four independent scenes.

| Image | Predictions above threshold | Visual assessment |
|---|---|---|
| img.png | traffic_light_red 0.358 | The box points to a small red pedestrian signal in the background. The crossings and green signal on the right were missed. |
| img_1.png | crosswalk 0.383 | The box is much too large, covering tram tracks and a substantial part of the sidewalk. A visible small green signal in the background was missed. |
| img_2.png | crosswalk 0.761 | Similarly incorrect, very large pavement box despite high confidence. The pedestrian signal was missed. |
| img_3.png | crosswalk 0.685; traffic_light_red 0.417 | Incorrect large pavement box. The red-light box points to a three-section vehicle signal rather than a pedestrian signal. The small pedestrian signal in the background was missed. |

This is a qualitative assessment of visible results, not a measurement against ground truth.
Confidence is not the probability of a correct and safe decision.

## Findings

Performance at this location is much weaker than the previous validation suggested.
Errors are especially visible in crossing localization and distinguishing pedestrian
signals from vehicle signals. Small signals against trees are sometimes missed.
The earlier high green-light mAP on 10 objects from one location does not establish generalization.

The next data collection should include pavement without crossings, tram tracks,
patterned sidewalks and vehicle signals as difficult background examples.
Signal-box boundaries should also be standardized, and existing annotations should
be checked for vehicle signals. These are directions for further review, not a claim
that a specific incorrect label has already been found.

Test_2 remains outside training. If these images are later used for learning, the entire
location must belong to one subset, and a new test at another location will be needed.
After reviewing these results, this set is suitable for error analysis rather than
independent confirmation of future improvements.

## Files

- `runs/inference/test_2_2026-10-15/predictions.jpg`: overview of all four results.
- `runs/inference/test_2_2026-10-15/predictions_images/`: individual full-resolution visualizations.
- `runs/inference/test_2_2026-10-15/predictions.json`: all boxes, confidence scores and source/weight hashes.

Reproduction command:

```sh
python scripts/inspect_baseline.py --weights runs/train/manual_scene_split_v1_batch4/weights/best.pt --source data/dataset/images/test_2 --limit 4 --output runs/inference/test_2_2026-10-15/predictions.jpg
```
