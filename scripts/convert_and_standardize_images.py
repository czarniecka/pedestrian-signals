"""Standardize image formats and orientation for Pedestrians Aid.

1. Convert iPhone HEIC/HEIF and other supported images to RGB JPEG.
2. Apply EXIF orientation metadata.
3. Skip videos or optionally extract frames at the requested rate.
4. Use consistent filenames and optionally remove converted originals.

Usage:
    python scripts/convert_and_standardize_images.py --input data/raw/images
    python scripts/convert_and_standardize_images.py --input data/raw/images --delete-originals
    python scripts/convert_and_standardize_images.py --input data/raw/images --extract-video-fps 1.0
"""

import argparse
import os
import sys
from pathlib import Path
from PIL import Image, ImageOps
import pillow_heif
import cv2
from tqdm import tqdm

# Register HEIF/HEIC support in Pillow
pillow_heif.register_heif_opener()

IMAGE_EXTENSIONS_TO_CONVERT = {".heic", ".heif", ".png", ".webp", ".bmp", ".tiff", ".jpeg"}
RAW_EXTENSIONS_ALL = {".jpg", ".jpeg", ".heic", ".heif", ".png", ".webp", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mov", ".mp4", ".avi", ".mkv", ".m4v", ".3gp"}


def fix_image_orientation(img: Image.Image) -> Image.Image:
    """Apply image orientation from EXIF metadata."""
    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        return img


def convert_image_to_jpg(source_path: Path, target_path: Path, quality: int = 95) -> bool:
    """Convert an image, including HEIC, to a standard RGB JPEG."""
    try:
        with Image.open(source_path) as img:
            img = fix_image_orientation(img)
            if img.mode in ("RGBA", "P", "LA"):
                img = img.convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            img.save(target_path, "JPEG", quality=quality)
            return True
    except Exception as e:
        print(f"\n[!] Conversion failed for {source_path.name}: {e}")
        return False


def extract_frames_from_video(video_path: Path, output_dir: Path, fps_sample: float = 1.0) -> int:
    """
    Optionally extract video frames, for example one frame per second.
    Useful for phone recordings of a crosswalk.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[!] Could not open video: {video_path.name}")
        return 0

    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, int(video_fps / fps_sample))
    
    saved_count = 0
    frame_idx = 0
    video_stem = video_path.stem

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_step == 0:
            frame_filename = f"vid_{video_stem}_f{frame_idx:06d}.jpg"
            target_path = output_dir / frame_filename
            cv2.imwrite(str(target_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            saved_count += 1

        frame_idx += 1

    cap.release()
    return saved_count


def process_directory(
    input_dir: Path,
    output_dir: Path,
    delete_originals: bool = False,
    extract_video_fps: float = 0.0,
    quality: int = 95
):
    """Process a directory of images and videos."""
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    all_files = [f for f in input_dir.iterdir() if f.is_file()]
    
    images_to_convert = []
    standard_jpgs = []
    videos = []

    for f in all_files:
        ext = f.suffix.lower()
        if ext in VIDEO_EXTENSIONS:
            videos.append(f)
        elif ext in {".heic", ".heif"}:
            images_to_convert.append(f)
        elif ext in IMAGE_EXTENSIONS_TO_CONVERT:
            images_to_convert.append(f)
        elif ext == ".jpg":
            standard_jpgs.append(f)

    print(f"\n=======================================================")
    print(f" Analyzing files in directory: {input_dir}")
    print(f" - HEIC/other images to convert: {len(images_to_convert)}")
    print(f" - Existing JPG files:              {len(standard_jpgs)}")
    print(f" - Video files found:           {len(videos)}")
    print(f"=======================================================\n")

    # 1. Convert HEIC and other image formats
    converted_count = 0
    for img_path in tqdm(images_to_convert, desc="Converting images (HEIC -> JPG)"):
        target_name = f"{img_path.stem}.jpg"
        target_path = output_dir / target_name
        
        # Skip conversion when the target path is the source path
        if target_path == img_path:
            continue

        if convert_image_to_jpg(img_path, target_path, quality=quality):
            converted_count += 1
            if delete_originals and img_path.resolve() != target_path.resolve():
                try:
                    img_path.unlink()
                except Exception as e:
                    print(f"[!] Could not delete original file {img_path.name}: {e}")

    # 2. Check and standardize existing JPGs using EXIF orientation
    for jpg_path in tqdm(standard_jpgs, desc="Checking JPG EXIF orientation"):
        try:
            with Image.open(jpg_path) as img:
                transposed = fix_image_orientation(img)
                # Check whether orientation has changed
                if transposed is not img:
                    transposed.save(jpg_path, "JPEG", quality=quality)
        except Exception:
            pass

    # 3. Process videos when enabled
    extracted_frames_total = 0
    if extract_video_fps > 0 and videos:
        print(f"\n[*] Extracting frames from {len(videos)} videos (sampling: {extract_video_fps} FPS)...")
        for vid_path in tqdm(videos, desc="Processing videos"):
            frames = extract_frames_from_video(vid_path, output_dir, fps_sample=extract_video_fps)
            extracted_frames_total += frames
        print(f"[+] Extracted {extracted_frames_total} video frames in total.")
    elif videos:
        print(f"[*] Skipped {len(videos)} videos (add --extract-video-fps 1.0 to extract frames)")

    print(f"\n[OK] Standardization complete!")
    print(f" - Successfully converted: {converted_count} files")
    final_jpgs = list(output_dir.glob("*.jpg"))
    print(f" - Total JPG files in {output_dir.name}: {len(final_jpgs)}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert iPhone HEIC images, apply EXIF orientation and standardize to JPEG"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/images",
        help="Input directory (default: data/raw/images)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="Delete original input images after successful JPEG conversion"
    )
    parser.add_argument(
        "--extract-video-fps",
        type=float,
        default=0.0,
        help="If > 0, extract video frames at this FPS (1.0 = one frame per second)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="JPEG compression quality (1-100, default: 95)"
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        print(f"[!] Input path does not exist: {input_path}")
        sys.exit(1)

    process_directory(
        input_dir=input_path,
        output_dir=output_path,
        delete_originals=args.delete_originals,
        extract_video_fps=args.extract_video_fps,
        quality=args.quality
    )


if __name__ == "__main__":
    main()
