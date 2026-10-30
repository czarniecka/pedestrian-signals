# Anotacja w Label Studio

Wklej `configs/label_studio.xml` w Settings → Labeling Interface → Code.
Konfiguracja oczekuje pola danych `image`. Importuj JPG z `data/raw/images/`.
Import przez Upload Files wykonuj partiami po około 20 zdjęć. Oryginały mają razem
około 723 MiB, a domyślna konfiguracja ogranicza pojedynczy import do 100 plików
i odczyt treści żądania do 250 MiB. Przy przekroczeniu limitów aplikacja może
pokazywać nieczytelny błąd RawPostDataException.
Alternatywa: lokalny storage wskazujący katalog ze zdjęciami, zamiast uploadu.
Plik `data/exports/label_studio/import_raw_images.json` zawiera 169 odwołań lokalnych;
przed jego użyciem trzeba dodać Local Files source storage dla tego katalogu
w tym samym projekcie (wymagane również do uprawnień wyświetlania zdjęć).

| ID | Klasa | Zasada |
|---|---|---|
| 0 | crosswalk | Jedna ramka wokół widocznego obszaru jednego przejścia: wszystkie białe pasy wraz z przestrzenią między nimi. |
| 1 | traffic_light_red | Sygnalizator dla pieszych z jednoznacznie widocznym czerwonym sygnałem. |
| 2 | traffic_light_green | Sygnalizator dla pieszych z jednoznacznie widocznym zielonym sygnałem. |
| 3 | traffic_light_off | Czytelny sygnalizator dla pieszych skierowany ku kamerze, bez widocznego zapalonego sygnału. Opis obrazu, nie dowód awarii urządzenia. |
| 4 | traffic_light_unknown | Rozpoznawalny sygnalizator dla pieszych, ale stan nieczytelny: odległość, rozmycie, zasłonięcie, prześwietlenie. |

## Zasady

- Obejmuj całą głowicę sygnalizatora z czerwonym i zielonym polem, bez słupa.
  Nie obrysowuj wyłącznie świecącego piktogramu. Zachowaj tę samą geometrię dla wszystkich stanów.
- Oznacz wszystkie rozpoznawalne sygnalizatory dla pieszych, również dotyczące innych
  przejść. Powiązanie światła z właściwym przejściem będzie osobnym zadaniem.
- Nie oznaczaj świateł dla samochodów, rowerów ani tramwajów. Gdy rodzaj obiektu
  jest nieczytelny, nie zgaduj; odłóż zdjęcie do przeglądu przed treningiem.
- Ramka obiektu uciętego kadrem obejmuje tylko jego widoczną część.
- Nie dodawaj klasy żółtej dla standardowych dwukolorowych sygnalizatorów pieszych.
- Oznacz wszystkie czytelne przejścia. Nie oznaczaj znaków drogowych jako przejść.
- Zdjęcie rzeczywiście bez obiektów zatwierdź z pustą anotacją. Nie myl z pominiętym zdjęciem.
- Nie obracaj ramek: zwykła detekcja YOLO korzysta z ramek równoległych do osi obrazu.

## Eksport

1. Zapisz YOLO i dodatkowo JSON w `data/exports/label_studio/`.
2. Sprawdź mapowanie eksportu (np. classes.txt) względem `configs/classes.yaml`.
   Atrybuty category ustalają ID, ale należy sprawdzić również gotowy eksport.
3. Wiersz YOLO: `class_id x_center y_center width height`, współrzędne 0–1.
   Nazwa etykiety musi odpowiadać nazwie zdjęcia.
4. Całe serie skrzyżowania/sesji przypisz do jednego podzbioru; nie dziel losowo podobnych klatek.
5. Augmentuj tylko trening. Walidacja pozostaje na rzeczywistych zdjęciach.

Źródła: https://labelstud.io/templates/image_bbox oraz https://labelstud.io/guide/export
