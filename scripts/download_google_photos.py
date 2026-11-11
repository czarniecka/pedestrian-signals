"""Download images from a shared Google Photos album and save RGB JPEGs.

Supports HEIC images and applies EXIF orientation.

Usage:
    python scripts/download_google_photos.py --url "https://photos.app.goo.gl/XXXXXXXXXX"
"""

import argparse
import io
import os
import re
import sys
from pathlib import Path
from PIL import Image, ImageOps
import pillow_heif
import requests
from tqdm import tqdm

# Register HEIC support
pillow_heif.register_heif_opener()

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "images"
GOOGLE_PHOTOS_URL_PATTERN = re.compile(r'https:\/\/lh3\.googleusercontent\.com\/[a-zA-Z0-9_\-]+')


def extract_photo_urls_from_album(album_url: str) -> list[str]:
    """Fetch a shared Google Photos album page and extract direct image links."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"[*] Fetching album metadata: {album_url}")
    session = requests.Session()
    response = session.get(album_url, headers=headers, allow_redirects=True)

    if response.status_code != 200:
        raise RuntimeError(f"Could not open the album. HTTP status: {response.status_code}")

    html_text = response.text
    matches = GOOGLE_PHOTOS_URL_PATTERN.findall(html_text)
    
    unique_urls = []
    seen = set()
    for url in matches:
        if url not in seen:
            seen.add(url)
            if not url.endswith(("/a/", "/a", "/default-user")):
                unique_urls.append(url)

    print(f"[+] Found {len(unique_urls)} potential items in the album.")
    return unique_urls


def download_and_standardize_image(url: str, output_path: Path, max_dimension: int = 0) -> bool:
    """
    Download an original or high-resolution image,
    apply EXIF orientation and save it as a standard RGB JPEG.
    """
    download_url = f"{url}=d" if max_dimension == 0 else f"{url}=w{max_dimension}-h{max_dimension}-no"
    
    try:
        resp = requests.get(download_url, timeout=30)
        if resp.status_code != 200 or len(resp.content) < 1024:
            # Try an alternative high-quality image URL
            alt_url = f"{url}=w2560-h2560-no"
            resp = requests.get(alt_url, timeout=30)
            if resp.status_code != 200:
                return False

        # Check whether the downloaded content is a video, such as MP4 or MOV
        content_type = resp.headers.get("Content-Type", "")
        if "video" in content_type:
            # Skip videos when saving individual images
            return False

        # Open with Pillow, including HEIC support through pillow-heif
        img_bytes = io.BytesIO(resp.content)
        with Image.open(img_bytes) as img:
            # Apply EXIF orientation, such as for portrait iPhone photos
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            if img.mode != "RGB":
                img = img.convert("RGB")

            img.save(output_path, "JPEG", quality=95)
            return True

    except Exception as e:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download and standardize Google Photos images as JPEGs in data/raw/images"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Google Photos album URL, such as https://photos.app.goo.gl/..."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="img_",
        help="Filename prefix (default: img_)"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=0,
        help="Optional maximum side length in pixels (0 = original)"
    )

    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        photo_urls = extract_photo_urls_from_album(args.url)
    except Exception as e:
        print(f"[!] Could not process the album: {e}")
        sys.exit(1)

    if not photo_urls:
        print("[!] No images found in the album.")
        sys.exit(1)

    print(f"[*] Starting download and conversion to: {output_dir.resolve()}")
    
    existing_files = list(output_dir.glob(f"{args.prefix}*.jpg"))
    start_idx = len(existing_files) + 1
    saved_count = 0

    for i, url in enumerate(tqdm(photo_urls, desc="Downloading and standardizing"), start=start_idx):
        filename = f"{args.prefix}{i:04d}.jpg"
        target_path = output_dir / filename

        if target_path.exists():
            continue

        if download_and_standardize_image(url, target_path, max_dimension=args.max_size):
            saved_count += 1

    print(f"\n[OK] Done! Saved {saved_count} standardized JPEG images to {output_dir.resolve()}")


if __name__ == "__main__":
    main()
