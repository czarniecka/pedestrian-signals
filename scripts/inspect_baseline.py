"""Run inference and save overlays/JSON for validation or new unlabeled images."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--source', default=str(ROOT/'data/dataset/images/val'))
    parser.add_argument('--limit', type=int, default=12)
    parser.add_argument('--conf', type=float, default=0.25)
    parser.add_argument('--imgsz', type=int, default=960)
    parser.add_argument('--device', default='0')
    args = parser.parse_args()
    photos = sorted(p for p in Path(args.source).iterdir()
                    if p.suffix.lower() in {'.jpg','.jpeg','.png','.bmp','.webp'} and p.is_file())
    if not photos or args.limit < 1:
        parser.error('No images found, or invalid limit.')
    selected = photos[::max(1, len(photos)//args.limit)][:args.limit]
    model = YOLO(args.weights)
    predictions = model.predict(source=[str(p) for p in selected], imgsz=args.imgsz,
                                conf=args.conf, device=args.device, verbose=False)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    individual_dir = output.parent/(output.stem+'_images')
    individual_dir.mkdir(exist_ok=True)
    columns = 2 if len(selected)<=4 else 4
    tile_w, tile_h = (500, 710) if len(selected)<=4 else (300, 360)
    canvas = Image.new('RGB', (columns*tile_w, math.ceil(len(selected)/columns)*tile_h), 'white')
    records = []
    for i, (source, pred) in enumerate(zip(selected, predictions)):
        plotted = Image.fromarray(pred.plot()[:, :, ::-1])
        plotted.save(individual_dir/(source.stem+'.jpg'), quality=95)
        tile = ImageOps.contain(plotted, (tile_w-5, tile_h-35))
        x, y = i%columns*tile_w, i//columns*tile_h
        canvas.paste(tile, (x,y))
        detections = [{'class':model.names[int(b.cls.item())],
                       'confidence':float(b.conf.item()),
                       'xyxy':b.xyxy[0].cpu().tolist()} for b in pred.boxes]
        records.append({'filename':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                        'detections':detections,'speed_ms':pred.speed})
        ImageDraw.Draw(canvas).text((x,y+tile_h-30), source.name+' | detections: '+str(len(detections)), fill='black')
    canvas.save(output, quality=95)
    output.with_suffix('.json').write_text(json.dumps({
        'weights':str(Path(args.weights).resolve()),
        'weights_sha256':hashlib.sha256(Path(args.weights).read_bytes()).hexdigest(),
        'confidence_threshold':args.conf,'image_size':args.imgsz,
        'ground_truth_used':False,'images':records},indent=2),encoding='utf-8')
    for record in records:
        print(record['filename'], [(b['class'],round(b['confidence'],3)) for b in record['detections']], flush=True)
    print(str(output))


if __name__ == '__main__':
    main()
