"""Export completed bounding boxes from the local Label Studio database, read-only.

Scene assignment was reviewed on contact sheets. No credentials are read.
"""
import hashlib
import json
import math
import sqlite3
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
NAMES = ['crosswalk', 'traffic_light_red', 'traffic_light_green',
         'traffic_light_off', 'traffic_light_unknown']
OUT = ROOT / 'data/dataset'
EXPORT = ROOT / 'data/exports/label_studio'


def image_name(data):
    url = data.get('image', data.get('$undefined$'))
    if not url:
        raise ValueError('Missing image field')
    name = unquote(url).replace('\\', '/').rsplit('/', 1)[-1]
    return name.split('-', 1)[1] if url.startswith('/data/upload/') else name


def scene(name):
    # 20260816 is one continuous recording of a construction crossing.
    # The UUID image shows the same yellow crossing; keep it with that session.
    if name.startswith('PXL_20260816_') or name == 'c9ea620c-56ff-4b5c-93f1-0c90c5b64c53.jpg':
        return 'yellow_crossing_held_out'
    # Conservatively keep all city-center views together, even across cameras/dates.
    # Some IMG and PXL_20260813 images show recurring intersections/backgrounds.
    if name.startswith(('IMG_', 'PXL_20260813_')) or name.startswith('c5ec66b7-'):
        return 'city_center_training'
    if name.startswith('d88be509-'):
        return 'fenced_crossing_training'
    raise ValueError(f'Unreviewed scene: {name}')


def dhash(image):
    a = np.asarray(image.convert('L').resize((9, 8), Image.Resampling.LANCZOS))
    bits = (a[:, 1:] > a[:, :-1]).flatten()
    return sum(int(bit) << i for i, bit in enumerate(bits))


def main():
    if any((OUT / 'images').rglob('*.jpg')):
        raise RuntimeError('Dataset already contains images; refuse to overwrite it.')
    db = ROOT / '.label-studio/label_studio.sqlite3'
    con = sqlite3.connect('file:' + db.as_posix() + '?mode=ro', uri=True)
    rows = con.execute('''SELECT c.id,c.task_id,c.result,c.updated_at,t.data
        FROM task_completion c JOIN task t ON t.id=c.task_id
        WHERE t.project_id=1 AND c.was_cancelled=0
        ORDER BY c.updated_at,c.id''').fetchall()
    latest = {r[1]: r for r in rows}
    total_tasks = con.execute('SELECT count(*) FROM task WHERE project_id=1').fetchone()[0]
    con.close()
    samples, exported, excluded, adjustments = [], [], [], []
    counts = {'train': Counter(), 'val': Counter()}
    for task_id, (ann_id, _, raw_result, updated, data) in sorted(latest.items()):
        data = json.loads(data)
        result = json.loads(raw_result)
        boxes = [r for r in result if r.get('type') == 'rectanglelabels']
        if not boxes:
            excluded.append(task_id)
            continue
        name = image_name(data)
        source = ROOT / 'data/raw/images' / name
        with Image.open(source) as im:
            im.load()
            if im.getexif().get(274, 1) != 1:
                raise ValueError(f'Unresolved EXIF orientation: {name}')
            width, height = im.size
            labels = []
            for box in boxes:
                if box.get('image_rotation', 0) != 0 or box['value'].get('rotation', 0) != 0:
                    raise ValueError(f'Rotated annotation: {name}')
                if (box['original_width'], box['original_height']) != im.size:
                    raise ValueError(f'Annotation/image dimension mismatch: {name}')
                v = box['value']
                if len(v['rectanglelabels']) != 1:
                    raise ValueError(f'Multiple labels for one box: {name}')
                cls = NAMES.index(v['rectanglelabels'][0])
                coords = [v[k] / 100 for k in ('x', 'y', 'width', 'height')]
                if not all(math.isfinite(x) for x in coords):
                    raise ValueError(f'Non-finite coordinates: {name}')
                x, y, w, h = coords
                x1, y1, x2, y2 = max(0, x), max(0, y), min(1, x+w), min(1, y+h)
                if x2 <= x1 or y2 <= y1:
                    raise ValueError(f'Empty annotation: {name}')
                if [x1, y1, x2, y2] != [x, y, x+w, y+h]:
                    adjustments.append({'task_id': task_id, 'box_id': box['id'], 'action': 'clipped_to_image'})
                labels.append((cls, (x1+x2)/2, (y1+y2)/2, x2-x1, y2-y1))
            group = scene(name)
            split = 'val' if group == 'yellow_crossing_held_out' else 'train'
            # Downscale without cropping, preserving normalized boxes and color.
            scale = min(1.0, 1920 / max(im.size))
            new_size = (round(width*scale), round(height*scale))
            rgb = im.convert('RGB').resize(new_size, Image.Resampling.LANCZOS)
            pixel_hash = hashlib.sha256(rgb.tobytes()).hexdigest()
            perceptual = dhash(rgb)
            for folder in ('images', 'labels'):
                (OUT / folder / split).mkdir(parents=True, exist_ok=True)
            rgb.save(OUT / 'images' / split / name, quality=95)
            (OUT / 'labels' / split / (Path(name).stem + '.txt')).write_text(
                '\n'.join(str(b[0])+' '+' '.join(f'{x:.8f}' for x in b[1:]) for b in labels)+'\n',
                encoding='utf-8')
            counts[split].update(NAMES[b[0]] for b in labels)
            samples.append({'task_id': task_id, 'annotation_id': ann_id, 'filename': name,
                'scene_group': group, 'split': split, 'original_size': [width,height],
                'processed_size': list(new_size), 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'pixel_sha256': pixel_hash, 'dhash': f'{perceptual:016x}', 'object_count': len(labels)})
            exported.append({'id': task_id, 'data': {'image': str(source), 'source_filename': name},
                'annotations': [{'id': ann_id, 'result': result, 'updated_at': updated}]})

    train = [s for s in samples if s['split']=='train']
    val = [s for s in samples if s['split']=='val']
    assert {s['scene_group'] for s in train}.isdisjoint(s['scene_group'] for s in val)
    assert {s['filename'] for s in train}.isdisjoint(s['filename'] for s in val)
    for field in ('source_sha256', 'pixel_sha256'):
        assert {s[field] for s in train}.isdisjoint(s[field] for s in val), field
    similarities = []
    for a in train:
        for b in val:
            distance = (int(a['dhash'],16)^int(b['dhash'],16)).bit_count()
            similarities.append((distance,a['filename'],b['filename']))
    report = {'source_project': 'PNW', 'total_source_tasks': total_tasks,
        'completed_tasks': len(latest), 'selected_positive_images': len(samples),
        'unannotated_or_skipped': total_tasks-len(latest), 'empty_completed_excluded': excluded,
        'images': {'train':len(train),'val':len(val)}, 'objects':counts,
        'absent_classes': [n for n in NAMES if not counts['train'][n]],
        'adjustments':adjustments, 'closest_cross_split_dhash_pairs':sorted(similarities)[:10],
        'preprocessing':'RGB; longest side <=1920; preserve aspect; JPEG95; no crop, no EXIF rotation',
        'split_policy':'Entire yellow-crossing location held out, including UUID view; city-center series kept together across cameras; no random frame split.',
        'limitations':['Scene identity inferred from visual review and filenames, not GPS.',
                      'Validation covers only one held-out location and is not a broad generalization test.',
                      'Only positive images used at user request; false alarm rate on empty scenes is untested.',
                      'No separate final test set for this initial experiment.']}
    EXPORT.mkdir(parents=True,exist_ok=True)
    (EXPORT/'annotated_tasks_snapshot.json').write_text(json.dumps(exported,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'split_manifest.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
    (OUT/'preparation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # Small visual QA sample, in both splits, with boxes overlaid.
    for split, subset in [('train',train),('val',val)]:
        canvas=Image.new('RGB',(1200,900),'white')
        for i,s in enumerate(subset[::max(1,len(subset)//12)][:12]):
            im=Image.open(OUT/'images'/split/s['filename']).convert('RGB'); draw=ImageDraw.Draw(im)
            for line in (OUT/'labels'/split/(Path(s['filename']).stem+'.txt')).read_text().splitlines():
                c,x,y,w,h=map(float,line.split());W,H=im.size
                draw.rectangle(((x-w/2)*W,(y-h/2)*H,(x+w/2)*W,(y+h/2)*H),outline=['blue','red','lime','gray','orange'][int(c)],width=4)
            tile=ImageOps.contain(im,(290,265));x=i%4*300;y=i//4*300;canvas.paste(tile,(x,y))
            ImageDraw.Draw(canvas).text((x,y+270),s['filename'][:28],fill='black')
        canvas.save(ROOT/'data/processed'/f'prepared_{split}_labels.jpg')
    print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)


if __name__ == '__main__':
    main()
