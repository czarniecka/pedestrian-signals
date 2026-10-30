"""
Skrypt do standaryzacji i konwersji zdjęć w projekcie Pedestrians Aid:
1. Konwertuje formaty Apple iPhone (.heic, .HEIC, .heif) do zunifikowanego formatu .jpg (RGB).
2. Automatycznie koryguje rotację zdjęć na podstawie metadanych EXIF (zapobiega obróconym zdjęciom z telefonu).
3. Ignoruje pliki wideo (.mov, .mp4, itp.) lub opcjonalnie wyciąga z nich klatki (np. 1 klatka co X sekund).
4. Unifikuje nazewnictwo i czyści niekompatybilne formaty.

Użycie:
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

# Rejestracja obsługi formatu HEIF/HEIC w Pillow
pillow_heif.register_heif_opener()

IMAGE_EXTENSIONS_TO_CONVERT = {".heic", ".heif", ".png", ".webp", ".bmp", ".tiff", ".jpeg"}
RAW_EXTENSIONS_ALL = {".jpg", ".jpeg", ".heic", ".heif", ".png", ".webp", ".bmp", ".tiff"}
VIDEO_EXTENSIONS = {".mov", ".mp4", ".avi", ".mkv", ".m4v", ".3gp"}


def fix_image_orientation(img: Image.Image) -> Image.Image:
    """Koryguje orientację zdjęcia z metadanych EXIF."""
    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        return img


def convert_image_to_jpg(source_path: Path, target_path: Path, quality: int = 95) -> bool:
    """Konwertuje dowolny format obrazu (w tym HEIC) na standardowy JPEG w przestrzeni RGB."""
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
        print(f"\n[!] Błąd konwersji {source_path.name}: {e}")
        return False


def extract_frames_from_video(video_path: Path, output_dir: Path, fps_sample: float = 1.0) -> int:
    """
    Opcjonalne wyciąganie klatek z wideo (np. 1 klatka co sekundę).
    Przydatne, gdy zespół nagrał przejście przez pasy telefonem.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"[!] Nie można otworzyć wideo: {video_path.name}")
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
    """Przetwarza cały folder ze zdjęciami i wideo."""
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
    print(f" Analiza plików w katalogu: {input_dir}")
    print(f" - Zdjęcia HEIC/inne do konwersji: {len(images_to_convert)}")
    print(f" - Gotowe pliki JPG:              {len(standard_jpgs)}")
    print(f" - Wykryte pliki wideo:           {len(videos)}")
    print(f"=======================================================\n")

    # 1. Konwersja HEIC / innych formatów
    converted_count = 0
    for img_path in tqdm(images_to_convert, desc="Konwersja obrazów (HEIC -> JPG)"):
        target_name = f"{img_path.stem}.jpg"
        target_path = output_dir / target_name
        
        # Jeśli konwertujemy w tym samym katalogu i plik o tej nazwie istnieje
        if target_path == img_path:
            continue

        if convert_image_to_jpg(img_path, target_path, quality=quality):
            converted_count += 1
            if delete_originals and img_path.resolve() != target_path.resolve():
                try:
                    img_path.unlink()
                except Exception as e:
                    print(f"[!] Błąd usuwania oryginału {img_path.name}: {e}")

    # 2. Weryfikacja i standaryzacja istniejących JPG (korekta obrotu EXIF)
    for jpg_path in tqdm(standard_jpgs, desc="Sprawdzanie rotacji EXIF w JPG"):
        try:
            with Image.open(jpg_path) as img:
                transposed = fix_image_orientation(img)
                # Sprawdzamy czy orientacja się zmieniła
                if transposed is not img:
                    transposed.save(jpg_path, "JPEG", quality=quality)
        except Exception:
            pass

    # 3. Obsługa wideo (jeśli włączona flaga)
    extracted_frames_total = 0
    if extract_video_fps > 0 and videos:
        print(f"\n[*] Ekstrakcja klatek z {len(videos)} filmów wideo (próbkowanie: {extract_video_fps} FPS)...")
        for vid_path in tqdm(videos, desc="Przetwarzanie wideo"):
            frames = extract_frames_from_video(vid_path, output_dir, fps_sample=extract_video_fps)
            extracted_frames_total += frames
        print(f"[+] Wyciągnięto łącznie {extracted_frames_total} klatek z filmów.")
    elif videos:
        print(f"[*] Pominięto {len(videos)} plików wideo (aby wyciągnąć klatki, dodaj parametr --extract-video-fps 1.0)")

    print(f"\n[OK] Zakończono standaryzację!")
    print(f" - Przekonwertowano pomyślnie: {converted_count} plików")
    final_jpgs = list(output_dir.glob("*.jpg"))
    print(f" - Łączna liczba gotowych plików .jpg w {output_dir.name}: {len(final_jpgs)}")


def main():
    parser = argparse.ArgumentParser(
        description="Konwersja zdjęć iPhone (.heic), standaryzacja orientacji EXIF i unifikacja do .jpg"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/images",
        help="Ścieżka do folderu wejściowego (domyślnie: data/raw/images)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Ścieżka do folderu wyjściowego (domyślnie ten sam co wejściowy)"
    )
    parser.add_argument(
        "--delete-originals",
        action="store_true",
        help="Usuwa oryginalne pliki .heic po pomyślnej konwersji do .jpg"
    )
    parser.add_argument(
        "--extract-video-fps",
        type=float,
        default=0.0,
        help="Jeśli > 0, wyciąga klatki z filmów wideo z podaną częstotliwością FPS (np. 1.0 = 1 klatka na sekundę)"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=95,
        help="Jakość kompresji JPEG (1-100, domyślnie 95)"
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        print(f"[!] Podana ścieżka nie istnieje: {input_path}")
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
