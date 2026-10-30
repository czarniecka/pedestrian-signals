# Nowe zdjęcia test_2 — 2026-10-15

Uruchomiono niezmieniony model `manual_scene_split_v1_batch4/weights/best.pt`
na czterech PNG z `data/dataset/images/test_2`. GPU, imgsz=960, confidence=0.25,
domyślne NMS. Bez treningu, zmiany wag, augmentacji testowej ani dołączania tych
zdjęć do zbioru treningowego. Nie użyto etykiet ani nie policzono mAP/recall.

Zdjęcia pokazują tę samą nową lokalizację z niewielkimi zmianami kadru oraz stanu
sygnalizacji. To cztery skorelowane ujęcia, a nie cztery niezależne sceny.

| Zdjęcie | Predykcje powyżej progu | Ocena wizualna |
|---|---|---|
| img.png | traffic_light_red 0.358 | Ramka wskazuje mały czerwony sygnalizator pieszy w tle. Przejścia i zielony sygnalizator po prawej pominięte. |
| img_1.png | crosswalk 0.383 | Ramka jest zdecydowanie za duża: obejmuje torowisko i znaczną część chodnika. Widoczny mały zielony sygnalizator w tle pominięty. |
| img_2.png | crosswalk 0.761 | Podobnie błędna, bardzo duża ramka nawierzchni mimo wysokiego confidence. Sygnalizator pieszy pominięty. |
| img_3.png | crosswalk 0.685; traffic_light_red 0.417 | Błędna duża ramka nawierzchni; ramka czerwonego światła wskazuje trzykomorowy sygnalizator dla pojazdów, nie pieszych. Mały sygnalizator pieszy w tle pominięty. |

To jakościowa ocena widocznych wyników, a nie pomiar względem ground truth.
Confidence nie oznacza prawdopodobieństwa poprawnej i bezpiecznej decyzji.

## Wniosek

Wynik na tej lokalizacji jest znacznie słabszy niż sugerowała walidacja z poprzedniego
eksperymentu. Szczególnie widoczne są błędy lokalizacji przejścia oraz odróżniania
sygnalizatorów pieszych od samochodowych. Małe światła na tle drzew bywają pomijane.
Nie należy traktować wcześniejszego wysokiego mAP zielonych świateł na 10 obiektach
z jednej lokalizacji jako potwierdzenia generalizacji.

Przy zbieraniu kolejnej partii danych warto uwzględnić nawierzchnie bez przejścia,
torowiska i chodniki z wzorami oraz sygnalizatory samochodowe jako trudne tło.
Trzeba też ujednolicić zakres ramek świateł i sprawdzić, czy w dotychczasowych
anotacjach nie trafiły do nich sygnalizatory dla pojazdów. To kierunki dalszej
weryfikacji, nie stwierdzenie, że znaleziono już konkretny błędny label.

Test_2 pozostaje poza treningiem. Jeśli te zdjęcia zostaną kiedyś użyte do uczenia,
cała lokalizacja musi trafić do jednego podzbioru i potrzebny będzie nowy test na
kolejnej lokalizacji. Po obejrzeniu wyników ten zestaw służy już do analizy błędów,
a nie do niezależnego potwierdzania skuteczności przyszłych zmian.

## Pliki

- `runs/inference/test_2_2026-10-15/predictions.jpg` — zestawienie czterech wyników.
- `runs/inference/test_2_2026-10-15/predictions_images/` — osobne wizualizacje w pełnej rozdzielczości.
- `runs/inference/test_2_2026-10-15/predictions.json` — wszystkie ramki, confidence i hashe źródeł oraz wag.

Polecenie odtwarzające:

```powershell
python scripts/inspect_baseline.py --weights runs/train/manual_scene_split_v1_batch4/weights/best.pt --source data/dataset/images/test_2 --limit 4 --output runs/inference/test_2_2026-10-15/predictions.jpg
```
