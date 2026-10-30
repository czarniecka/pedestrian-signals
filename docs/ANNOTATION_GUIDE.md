# Annotation in Label Studio

Paste `configs/label_studio.xml` into Settings > Labeling Interface > Code.
The configuration expects an `image` data field. Import JPG files from `data/raw/images/`.
Use batches of about 20 images with Upload Files. The originals total about 723 MiB.
The default configuration limits each import to 100 files and request-body reads to 250 MiB.
Exceeding these limits may produce an unclear RawPostDataException error.
Alternatively, use local storage pointing to the image directory instead of uploading.
`data/exports/label_studio/import_raw_images.json` contains 169 local references.
Before using it, add Local Files source storage for that directory in the same project.
This is also required for permission to display the images.

| ID | Class | Rule |
|---|---|---|
| 0 | crosswalk | One box around the visible area of a single crossing, including all white stripes and the spaces between them. |
| 1 | traffic_light_red | A pedestrian signal with a clearly visible red light. |
| 2 | traffic_light_green | A pedestrian signal with a clearly visible green light. |
| 3 | traffic_light_off | A recognizable pedestrian signal facing the camera, with no visibly illuminated light. This describes the image and does not prove a device failure. |
| 4 | traffic_light_unknown | A recognizable pedestrian signal whose state is unreadable because of distance, blur, occlusion or overexposure. |

## Rules

- Include the entire signal head with both red and green sections, excluding the pole.
  Do not outline only the illuminated symbol. Use the same box geometry for all states.
- Label all recognizable pedestrian signals, including those for other crossings.
  Associating a signal with the correct crossing is a separate task.
- Do not label vehicle, bicycle or tram signals. If the object type is unclear,
  do not guess. Set the image aside for review before training.
- For an object cut off by the frame, include only its visible part.
- Do not add a yellow class for standard two-color pedestrian signals.
- Label all recognizable crossings. Do not label road signs as crossings.
- Approve a genuinely empty image with an empty annotation. Distinguish it from a skipped image.
- Do not rotate boxes. Standard YOLO detection uses axis-aligned boxes.

## Export

1. Save YOLO and an additional JSON export in `data/exports/label_studio/`.
2. Check the export mapping, such as classes.txt, against `configs/classes.yaml`.
   The category attributes set the IDs, but the completed export must also be checked.
3. YOLO row format: `class_id x_center y_center width height`, with coordinates in 0-1.
   Each label filename must match its image filename.
4. Assign an entire intersection or session sequence to one subset. Do not randomly split similar frames.
5. Augment training only. Keep validation on real images.

References: https://labelstud.io/templates/image_bbox and https://labelstud.io/guide/export
