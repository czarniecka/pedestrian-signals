# Pedestrians Aid — pierwszy model detekcji

Aktualny zakres: ramki przejść i sygnalizatorów dla pieszych z osobnymi klasami stanu.
Anotacja ręczna w Label Studio.

## Pliki

- `data/raw/images/`: oryginalne 169 JPG i 15 MP4; do Label Studio importuj JPG.
- `configs/label_studio.xml`: wklej w Settings → Labeling Interface → Code.
- `docs/ANNOTATION_GUIDE.md`: zasady oznaczania i eksportu.
- `data/exports/label_studio/`: miejsce na eksporty YOLO oraz JSON.
- `data/dataset/`: ręczne anotacje z projektu PNW, 115 zdjęć train i 37 val.
- `configs/classes.yaml`: definicje klas nowego treningu.
- `weights/yolov8n.pt`: zachowane wagi bazowe detektora.
- `docs/SPECIFICATION.md`: pierwotna, szersza specyfikacja; nie definiuje zakresu dzisiejszego PoC.

## Kolejność pracy

1. Wklej konfigurację XML do projektu Label Studio i zaimportuj JPG.
2. Oznacz zdjęcia według instrukcji.
3. Eksportuj YOLO oraz JSON. Sprawdź mapowanie klas eksportu.
4. Podziel dane według skrzyżowania/sesji. Umieść zdjęcia w
   `data/dataset/images/{train,val}` i etykiety w `data/dataset/labels/{train,val}`.
   Eksport sam nie tworzy tego podziału.
5. Z katalogu projektu uruchom:

```powershell
python scripts/train_yolo.py --epochs 60 --batch 8 --imgsz 640
```

Augmentacje działają podczas treningu razem z ramkami. Zmiana odcienia jest wyłączona.

## Przygotowany zbiór i pierwszy trening

`scripts/prepare_label_studio_dataset.py` odczytuje wyłącznie anotacje i dane z lokalnej
bazy w trybie read-only. Wybiera najnowszą zatwierdzoną, nieanulowaną anotację zadania
z ramkami i zapisuje jej kopię JSON w `data/exports/label_studio/annotated_tasks_snapshot.json`.
Nie czyta poświadczeń i nie zmienia Label Studio.

Wybrano 152 zdjęcia z obiektami; pozostałe 17 nie ma zatwierdzonych anotacji.
Podział jest zapisany w `data/dataset/split_manifest.json`, a walidacja geometrii,
liczby klas i kontrola duplikatów w `data/dataset/preparation_report.json`.
Całe nagranie żółtego przejścia (2026-08-16) i UUID-owe zdjęcie tej lokalizacji
trafiły do val. Serie centrum miasta pozostają razem w train, również między kamerami.
To konserwatywny podział po lokalizacji, ustalony na podstawie wizualnego przeglądu.
Walidacja obejmuje jedną lokalizację; nie ma jeszcze osobnego finalnego testu.

Preprocessing: RGB, najdłuższy bok maksymalnie 1920 px, zachowane proporcje,
brak kadrowania i zmiany odcienia. Ramki znormalizowane pozostają zgodne ze zdjęciami.
Skrypt odmawia nadpisania istniejącego zbioru, aby chronić podział i etykiety.

```powershell
python scripts/train_yolo.py --epochs 80 --patience 25 --batch 4 --imgsz 960 --device 0 --name manual_scene_split_v1_batch4
```

Augmentacje wyłącznie train: obrót ±5°, translacja 5%, skala 0.8–1.2,
umiarkowana jasność/nasycenie. Wyłączone: zmiana odcienia, odbicia, mosaic,
mixup i opcjonalny pakiet augmentacji Albumentations (w tym grayscale).
Trening używa pretrained YOLOv8n, RTX 4060 i seed 42.
Klasa `traffic_light_unknown` nie ma żadnych przykładów i nie może być oceniona.
Zbiór z samymi pozytywnymi zdjęciami nie pozwala ocenić fałszywych alarmów na pustych scenach.

## Porządki 2026-10-14

Stary edytor, pseudoetykiety, poprzednie zbiory, wyniki treningów, modele segmentacji
oraz YOLO-World i stary dziennik eksperymentów są w `archive/legacy_2026-10-14/`.
Zachowano tam również poprzedni README, konfigurację dziewięciu klas i skrypt treningowy.
Archiwum jest lokalne i ignorowane przez Git. Nie kopiuj starych etykiet do nowego zbioru:
nie odpowiadają nowej definicji klas.

Pozostawiono narzędzia pobierania i konwersji. Konwersję orientacji/formatu wykonuj
przed anotacją, nie na zdjęciach z gotowymi ramkami.

## Lokalne Label Studio

Uruchomienie z katalogu projektu:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_label_studio.ps1
```

Adres: http://localhost:8080. Pierwszy start wymaga utworzenia lokalnego konta.
Aplikacja jest zainstalowana w `.venv-label-studio/`; jej baza i pliki projektów
są w `.label-studio/`. Zachowaj ten folder — zawiera anotacje zapisane w aplikacji.
Dostęp do lokalnych plików jest ograniczony do `data/raw/images/`.

Do projektu Label Studio `PNW` zaimportowano 169 zdjęć: pierwsze 20 przez upload,
pozostałe 149 przez Local Files source storage `Raw photos`.
Folder `data/raw/images/label_studio/` zawiera dowiązania twarde do tych 149 JPG;
nie przenoś go ani nie modyfikuj zdjęć po anotacji. Dowiązania współdzielą zawartość
z oryginałami i nie zajmują dodatkowego miejsca na kopie obrazów.
Nie importuj ponownie przygotowanych JSON-ów do tego samego projektu — utworzyłoby to duplikaty.
