# Przeniesione dane i eksperymenty

Kopia z `pedestrians_aid`, wykonana 2026-10-30. Źródło pozostało bez zmian.
Plik `migration_manifest.json` zawiera ścieżki, rozmiary i SHA-256 skopiowanych plików.
Kopia bazy Label Studio powstała przez mechanizm backupu SQLite.

## Struktura

| Katalog | Zawartość |
| --- | --- |
| `src/pedestrian_signals/` | Istniejący szkielet aplikacji |
| `data/raw/images/` | Oryginały zdjęć i nagrań, także katalog plików lokalnych Label Studio |
| `data/dataset/` | Ręczne etykiety YOLO, 115 zdjęć train, 37 val, 4 zdjęcia test_2, manifest podziału i audyt |
| `data/exports/label_studio/` | Snapshot anotacji JSON i historyczne pliki importu |
| `data/processed/` | Plansze do przeglądu danych i etykiet |
| `configs/` | Pięć klas oraz interfejs Label Studio |
| `scripts/` | Przygotowanie danych, trening, predykcje, pobieranie i konwersja zdjęć, start Label Studio |
| `weights/` | Bazowe YOLOv8n oraz YOLO26n, sam plik wag nie oznacza przeprowadzonego eksperymentu |
| `runs/train/manual_scene_split_v1_batch4/` | Główny trening, best.pt, last.pt, metryki, wykresy i podglądy |
| `runs/inference/test_2_2026-10-15/` | Predykcje na nowej lokalizacji i JSON |
| `archive/legacy_2026-10-14/` | Starsze dane, pseudoetykiety, skrypty oraz eksperymenty detekcji i segmentacji |
| `archive/incomplete_training_start_2026-10-14/` | Nieukończona próba startowa, nie osobny wytrenowany model |
| `output/pdf/` | Istniejące podsumowanie projektu |
| `.label-studio/` | Lokalna kopia bazy i uploadów, poza Gitem |

## Modele i wyniki

Główny checkpoint to `runs/train/manual_scene_split_v1_batch4/weights/best.pt`.
YOLOv8n po ręcznych anotacjach uzyskał mAP50 0.810 oraz mAP50-95 0.516.
Najlepsza epoka to 47, trening zakończył się po 72 epokach.
Szczegóły i ograniczenia opisuje `TRAINING_BASELINE.md`.
Walidacja obejmuje jedną odłożoną lokalizację. Nie ma osobnego finalnego testu.
`OOD_TEST_2.md` opisuje błędy na nowej lokalizacji, w tym pomylenie sygnalizatora samochodowego z pieszym.

Zachowano też starsze checkpointy i ich oryginalne wyniki:

- Detekcja: `archive/legacy_2026-10-14/runs/detect/runs/train/yolov8n_detect/`.
- Segmentacja: `archive/legacy_2026-10-14/runs/segment/runs/train/yolov8n_seg/`.
- YOLO-World: bazowe wagi w archiwum oraz stary skrypt automatycznej anotacji.

Archiwum ma dawną definicję dziewięciu klas. Nie łącz jego etykiet z bieżącym zbiorem pięciu klas.
Historyczne JSON-y, argumenty treningu i dokumenty zachowują oryginalne ścieżki jako zapis eksperymentów.
Bieżący skrypt treningu wylicza ścieżki względem nowego repo i ponownie tworzy `runs/dataset_resolved.yaml`.

## Uruchamianie

Polecenia wykonuj z głównego katalogu repo. Pakiet aplikacji ma wymaganie Python >=3.14.
Dla przeniesionych eksperymentów użyj osobnego środowiska Python 3.13, zgodnego z opisem poprzedniego treningu.
Nie zmieniono istniejącego `pyproject.toml` ani `uv.lock`.

```powershell
uv venv --python 3.13 .venv-ml
uv pip install --python .venv-ml/Scripts/python.exe -r requirements-ml.txt
.venv-ml/Scripts/python.exe scripts/train_yolo.py --epochs 80 --patience 25 --batch 4 --imgsz 960 --device 0 --name manual_scene_split_v2
.venv-ml/Scripts/python.exe scripts/inspect_baseline.py --weights runs/train/manual_scene_split_v1_batch4/weights/best.pt --source data/dataset/images/test_2 --limit 4 --device cpu --output runs/inference/test_2_recheck/predictions.jpg
```

Lista zależności nie odtwarza dokładnie dawnej instalacji CUDA. Dla GPU dobierz PyTorch do lokalnego sterownika.
Wersje użyte przy pierwotnym treningu są w `TRAINING_BASELINE.md`.
Skrypt przygotowania zbioru odmawia nadpisania istniejących zdjęć. Zachowaj obecny podział.
Konwersję zdjęć wykonuj przed anotacją. Nie zmieniaj gotowych zdjęć z etykietami.

## Label Studio

Anotacje są dostępne w `data/exports/label_studio/annotated_tasks_snapshot.json` oraz jako etykiety YOLO.
Zachowano także spójną kopię bazy i 20 uploadów. Nie skopiowano konta środowiska, pliku `.env` ani logów.
Baza zawiera lokalne konta i powinna pozostać poza Gitem.
Środowiska wirtualnego ze starego repo nie kopiowano, trzeba je utworzyć ponownie:

```powershell
uv venv --python 3.13 .venv-label-studio
uv pip install --python .venv-label-studio/Scripts/python.exe label-studio
powershell -ExecutionPolicy Bypass -File scripts/start_label_studio.ps1
```

Przed synchronizacją storage sprawdź jego katalog w ustawieniach Label Studio.
Historyczny wpis może wskazywać stare repo. Ustaw nowy `data/raw/images/label_studio`.
Nie importuj ponownie plików `import_*.json` do skopiowanego projektu, bo powstaną duplikaty.
Uruchomienie aplikacji i jej migracje bazy nie były częścią przenoszenia.

## Co trafia do Gita

Kod, konfiguracje, dokumentacja, zdjęcia źródłowe, nagrania, przygotowany zbiór,
eksporty anotacji, podglądy, wagi bazowe i checkpointy obecnego treningu są wersjonowane.
Repo zawiera też pełne wyniki bieżącego modelu i podsumowanie PDF.
Pliki cache, konfiguracja z absolutnymi ścieżkami, środowiska, baza Label Studio
i stare archiwum pozostają lokalne i ignorowane. Kopię bazy oraz archiwum zachowaj osobno.
Manifest migracji opisuje wszystkie skopiowane pliki, także te pozostawione poza Gitem.
