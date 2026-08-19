## Dane:
- **Organizacja**: foldery/nazwy plików z metadanymi (lokalizacja, godzina, warunki pogodowe) - przyda się później do analizy błędów per warunek.
- **Adnotacja**: bounding box na sygnalizatorze pieszym + etykieta stanu (czerwony/zielony/brak/nieczytelny).
- **Auto-adnotacja jako start**: użycie modelu wytrenowanego na DTLD/ImVisible do wstępnego oznaczenia zdjęć, potem tylko poprawa błędów ręcznie - dużo szybsze niż adnotacja od zera.
- **Augmentacja**: jasność/kontrast (słońce, zmierzch), rozmycie ruchu, przycięcia - symuluje warunki, których nie było podczas fotografowania/nagrywania.

#### Pomysły na pozyskanie danych:
- **Google Street View / Maps Platform** - nie można. Warunki użytkowania Google Maps Platform wprost zakazują używania treści (w tym Street View) do trenowania modeli ML/AI. Ryzyko prawne, więc odpada jako źródło danych treningowych.
- **Mapillary** - można używać do ML/badań na licencji CC BY-SA, ma API i pokrycie w Polsce. Ograniczenie: to statyczne zdjęcia z przypadkowego momentu, więc nie da state sygnalizacji (czerwony/zielony) w sposób kontrolowany. Dodatkowo zdjęć sygnalizatorów pieszych jest drastycznie mało i ciężko je znaleźć. 
- **Własna kolekcja** - docelowe pozyskanie danych. Ograniczenie: czas.

---
## Podział danych:

**Podział train/val/test** (x/y/z do ustalenia) - **WAŻNE** zdjęcia z tego samego skrzyżowania/sesji nie mogą trafić równocześnie do train i test (data leakage, zawyży wynik).

---
## Trenowanie:

### Modele trenowane w podobnych tematach:
- DTLD = **DriveU Traffic Light Dataset**, publiczny zbiór danych do wykrywania sygnalizacji świetlnej, stworzony przez Uniwersytet w Ulm (Niemcy).
	Co zawiera: 232 039 oznaczonych sygnalizatorów na zdjęciach z 11 niemieckich miast, z tagami: kolor (czerwony/żółty/zielony), orientacja, liczba lampek, poziom zakrycia, anomalie wizualne.
- ImVisible = **PTL (Pedestrian Traffic Light) Dataset** + lekka sieć CNN **LytNet**, projekt stworzony specjalnie do rozpoznawania sygnalizacji dla pieszych i przejść dla pieszych, na potrzeby osób niewidomych.
	Co zawiera: zdjęcia skrzyżowań z różnych warunków (pogoda, kąt, typ skrzyżowania), oznaczone: obecność/pozycja sygnalizatora pieszego + orientacja przejścia dla pieszych (zebry) względem kamery.

Powyższe modele można wykorzystać w formie pretreningu i douczyć je na naszej własnej kolekcji zdjęć.

### Wybór modelu bazowego:
- lekki **YOLO** (np. YOLOv8n/YOLO11n) - pod kątem działania w czasie rzeczywistym na małym urządzeniu.

### Walidacja:
- Nacisk na **false positive** - fałszywe "wolno przejść" jest niedopuszczalne, więc miarą sukcesu nie jest tylko accuracy, ale recall na klasie "czerwony/stop" i osobne śledzenie false positive rate dla "zielony/go".
