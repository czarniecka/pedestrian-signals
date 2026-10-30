# Pierwszy model po ręcznej anotacji — 2026-10-14

Wytrenowano YOLOv8n z wag COCO na RTX 4060. Najlepszy checkpoint pochodzi z epoki 47. Trening zakończył się po 72 epokach przez early stopping; czas samego treningu wyniósł około 22.1 minut.

## Dane i ochrona podziału

Z lokalnej bazy Label Studio PNW odczytano w trybie read-only 152 zatwierdzone zadania z ramkami (357 obiektów). Pozostałe 17 zadań nie miało zatwierdzonych anotacji i zostało pominięte zgodnie z zakresem użytkownika. Nie zmieniono anotacji w aplikacji ani oryginalnych zdjęć.

- Train: 115 zdjęć, 281 obiektów. Val: 37 zdjęć, 76 obiektów.
- Cała sesja żółtego przejścia z 2026-08-16 i UUID-owy widok tej lokalizacji są w val.
- Serie z centrum miasta pozostają razem w train, także między kamerami i datami.
- Zweryfikowano rozłączność grup, nazw, SHA-256 oryginałów i hashy zdekodowanych przetworzonych obrazów. Minimalna odległość dHash między train i val wynosi 15/64; ten dodatkowy test nie zastępuje przeglądu scen.
- Podział oparto na wizualnym przeglądzie i nazwach plików, bez metadanych GPS. Zapisano go w data/dataset/split_manifest.json.
- Nie zastosowano losowego podziału klatek ani augmentacji walidacji.

## Preprocessing i trening

RGB; zmniejszenie najdłuższego boku do maksymalnie 1920 px bez powiększania, zachowanie proporcji, JPEG95. Nie kadrowano zdjęć ani nie zmieniano orientacji. Weryfikacja wymiarów anotacji i EXIF przeszła dla wszystkich zdjęć. Pięć ramek minimalnie wychodzących poza obraz przycięto do jego granic; zmiany zapisano w preparation_report.json.

Wejście modelu: 960 px; batch 4; seed 42; AdamW; maksymalnie 80 epok, patience 25, workers 0. Większy batch 8 na starcie był zbyt wolny przy współdzieleniu GPU z grą, więc rozpoczęto właściwy eksperyment z batch 4.

Augmentacje generowane podczas treningu razem z ramkami: obrót ±5°, translacja 5%, skala 0.8–1.2, umiarkowana jasność i nasycenie (HSV S/V 0.2). Wyłączono zmianę odcienia, odbicia, mosaic, mixup i opcjonalne transformacje Albumentations, w tym grayscale.

Środowisko: Python 3.13.7, PyTorch 2.9.0+cu128, Ultralytics 8.4.143.

## Wynik najlepszych wag na walidacji

Łącznie: mAP50 **0.810**, mAP50–95 **0.516**. Nie są to procenty poprawnych decyzji o przejściu przez jezdnię.

| Klasa | Obiekty val | Precision | Recall | mAP50 | mAP50–95 |
|---|---:|---:|---:|---:|---:|
| Przejście | 37 | 0.861 | 0.568 | 0.613 | 0.392 |
| Czerwone światło piesze | 27 | 0.842 | 0.815 | 0.887 | 0.507 |
| Zielone światło piesze | 10 | 0.869 | 1.000 | 0.995 | 0.645 |
| Brak zapalonego sygnału | 2 | 0.344 | 0.500 | 0.745 | 0.522 |

Precision/Recall są raportowane według sposobu wyboru progu przez Ultralytics; nie należy interpretować ich jako wyniku dokładnie przy confidence=0.25 użytym do podglądu.

## Wnioski i ograniczenia

Rozpoznawanie świateł jest obiecujące jako wstępny eksperyment. Dla czerwonych sygnałów recall wynosi około 0.815; zielone mają recall 1.0 na zaledwie 10 obiektach. Wynik ten nie potwierdza niezawodności ani braku fałszywych wskazań zielonego.

Przejścia są słabszym elementem: recall około 0.568, mAP50 około 0.613. Walidacja obejmuje między innymi żółte, tymczasowe oznakowanie, którego nie ma w serii treningowej; jest to rzeczywisty test zmiany wyglądu sceny.

Wyłączone/nieświecące sygnalizatory mają tylko 10 obiektów train i 2 val. Wnioski dla tej klasy są bardzo niestabilne. Klasa traffic_light_unknown nie ma żadnych przykładów, pozostaje nieprzetestowana i nie należy uznawać jej za wytrenowaną.

Walidacja obejmuje głównie jedną odłożoną lokalizację, a wiele jej klatek jest skorelowanych. Użyto jej również do wyboru checkpointu; nie ma osobnego, nietkniętego testu końcowego. Nie porównuj tych liczb bezpośrednio ze starym eksperymentem 24/6, bo zmieniły się dane, klasy i podział.

Zgodnie z prośbą użyto tylko zdjęć z obiektami. Fałszywe alarmy na pustych scenach nie były oceniane. Dalszy krok: nowe lokalizacje, materiał z ESP-CAM, przykłady trudnych/nieczytelnych świateł oraz osobny test również na zdjęciach negatywnych.

## Pliki

- Wagi: runs/train/manual_scene_split_v1_batch4/weights/best.pt
- Dokładne metryki: runs/train/manual_scene_split_v1_batch4/experiment_summary.json
- Podgląd predykcji (confidence 0.25): runs/train/manual_scene_split_v1_batch4/validation_predictions.jpg
- Przebieg treningu i macierz pomyłek: results.png oraz confusion_matrix.png w katalogu eksperymentu.
- Kopia anotacji: data/exports/label_studio/annotated_tasks_snapshot.json
- Audyt danych: data/dataset/preparation_report.json oraz split_manifest.json
