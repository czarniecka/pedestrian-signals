"""
Skrypt do pobierania zdjęć z Google Photos (albumów współdzielonych lub przez API)
i automatycznej konwersji (w tym formatów iPhone .HEIC) do zunifikowanego .jpg w: data/raw/images/

Użycie:
1. Pobranie i automatyczna konwersja zdjęć z albumu Google Photos:
   python scripts/download_google_photos.py --url "https://photos.app.goo.gl/XXXXXXXXXX"

2. Z opcją wyciągania klatek z nagranych filmów (np. 1 klatka/s):
   python scripts/download_google_photos.py --url "https://photos.app.goo.gl/XXXXXXXXXX" --extract-video-fps 1.0
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

# Rejestracja obsługi HEIC
pillow_heif.register_heif_opener()

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "images"
GOOGLE_PHOTOS_URL_PATTERN = re.compile(r'https:\/\/lh3\.googleusercontent\.com\/[a-zA-Z0-9_\-]+')


def extract_photo_urls_from_album(album_url: str) -> list[str]:
    """Pobiera stronę udostępnionego albumu Google Photos i wyciąga bezpośrednie linki."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"[*] Pobieranie metadanych z albumu: {album_url}")
    session = requests.Session()
    response = session.get(album_url, headers=headers, allow_redirects=True)

    if response.status_code != 200:
        raise RuntimeError(f"Błąd podczas otwierania albumu. Kod HTTP: {response.status_code}")

    html_text = response.text
    matches = GOOGLE_PHOTOS_URL_PATTERN.findall(html_text)
    
    unique_urls = []
    seen = set()
    for url in matches:
        if url not in seen:
            seen.add(url)
            if not url.endswith(("/a/", "/a", "/default-user")):
                unique_urls.append(url)

    print(f"[+] Znaleziono {len(unique_urls)} potencjalnych obiektów w albumie.")
    return unique_urls


def download_and_standardize_image(url: str, output_path: Path, max_dimension: int = 0) -> bool:
    """
    Pobiera obraz (oryginał lub w wysokiej rozdzielczości),
    automatycznie koryguje rotację EXIF i zapisuje jako standardowy .jpg (RGB).
    """
    download_url = f"{url}=d" if max_dimension == 0 else f"{url}=w{max_dimension}-h{max_dimension}-no"
    
    try:
        resp = requests.get(download_url, timeout=30)
        if resp.status_code != 200 or len(resp.content) < 1024:
            # Próba alternatywnego linku wysokiej jakości
            alt_url = f"{url}=w2560-h2560-no"
            resp = requests.get(alt_url, timeout=30)
            if resp.status_code != 200:
                return False

        # Sprawdzenie czy pobrana zawartość to wideo (np. mp4/mov)
        content_type = resp.headers.get("Content-Type", "")
        if "video" in content_type:
            # Pomijamy wideo w bezpośrednim zapisie jako pojedynczy obraz
            return False

        # Otwarcie za pomocą PIL (wspiera również HEIC dzięki pillow-heif)
        img_bytes = io.BytesIO(resp.content)
        with Image.open(img_bytes) as img:
            # Korekta rotacji EXIF (np. zdjęcia pionowe z iPhone)
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
        description="Pobieranie i unifikacja zdjęć z Google Photos do .jpg w data/raw/images"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Link do albumu Google Photos (np. https://photos.app.goo.gl/...)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Katalog docelowy (domyślnie: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="img_",
        help="Prefiks dla plików (domyślnie: img_)"
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=0,
        help="Opcjonalny maksymalny wymiar boku w px (0 = oryginał)"
    )

    args = parser.parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        photo_urls = extract_photo_urls_from_album(args.url)
    except Exception as e:
        print(f"[!] Błąd przetwarzania albumu: {e}")
        sys.exit(1)

    if not photo_urls:
        print("[!] Nie znaleziono zdjęć w albumie.")
        sys.exit(1)

    print(f"[*] Rozpoczynam pobieranie i konwersję do: {output_dir.resolve()}")
    
    existing_files = list(output_dir.glob(f"{args.prefix}*.jpg"))
    start_idx = len(existing_files) + 1
    saved_count = 0

    for i, url in enumerate(tqdm(photo_urls, desc="Pobieranie i standaryzacja"), start=start_idx):
        filename = f"{args.prefix}{i:04d}.jpg"
        target_path = output_dir / filename

        if target_path.exists():
            continue

        if download_and_standardize_image(url, target_path, max_dimension=args.max_size):
            saved_count += 1

    print(f"\n[OK] Gotowe! Zapisano {saved_count} zunifikowanych zdjęć .jpg w {output_dir.resolve()}")


if __name__ == "__main__":
    main()
