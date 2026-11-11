# ESP Cam Drive (iOS)

Aplikacja pobiera zdjęcia i filmy z ESP32-CAM przez WiFi i wysyła je na Dysk Google.
Tryb ręczny (podgląd, potem "wyślij") i automatyczny (zdjęcia co N sekund + natychmiastowa wysyłka).

> Kod nie był kompilowany w tym środowisku. Przy pierwszym buildzie mogą wyskoczyć drobne błędy, wklej je do Claude.

## 1. Kamera ESP32-CAM (najprościej)

1. Arduino IDE → Plik → Przykłady → ESP32 → Camera → **CameraWebServer**.
2. Odkomentuj model `CAMERA_MODEL_AI_THINKER`, wpisz SSID i hasło swojego WiFi (tej samej sieci co iPhone).
3. Wgraj szkic. W Serial Monitorze zobaczysz adres IP (np. `192.168.1.50`). Najlepiej ustaw w routerze stały adres dla kamery.
4. Aplikacja używa `http://IP/capture` (zdjęcie) i `http://IP:81/stream` (film). Strumień obsługuje jednego klienta naraz, więc zamknij podgląd w przeglądarce.

## 2. Google Cloud (jednorazowo, ok. 5 min)

1. https://console.cloud.google.com → nowy projekt.
2. **APIs & Services → Library** → włącz **Google Drive API**.
3. **OAuth consent screen**: typ *Internal* (jeśli masz konto Workspace w firmie) albo *External* i dodaj siebie jako Test user. Zakres: `.../auth/drive.file`.
4. **Credentials → Create credentials → OAuth client ID → iOS**, Bundle ID: `com.ola.espcamdrive` (lub Twój własny, taki sam jak w `project.yml`).
5. Skopiuj **Client ID** do `Sources/Config.swift` (`googleClientID`).

Uwaga: dla *External* w trybie Testing logowanie wygasa po 7 dniach. Aplikacja poprosi wtedy o ponowne zalogowanie.
Aplikacja widzi tylko pliki, które sama utworzyła (zakres `drive.file`), i zapisuje je w folderze o nazwie z ustawień (domyślnie `ESP32-CAM`).

## 3. Instalacja na iPhonie kablem (Mac)

VS Code sam nie podpisze aplikacji iOS, potrzebna jest zainstalowana aplikacja Xcode (darmowa, z App Store). Samo klikanie odbywa się potem w Xcode.

```bash
brew install xcodegen
cd ESPCamDrive
xcodegen          # tworzy ESPCamDrive.xcodeproj
open ESPCamDrive.xcodeproj
```

W Xcode:
1. Target **ESPCamDrive → Signing & Capabilities** → wybierz swój Team (zwykłe Apple ID wystarczy) i ewentualnie zmień Bundle Identifier.
2. Podłącz iPhone'a kablem, odblokuj, zaufaj komputerowi. Na iPhonie włącz **Ustawienia → Prywatność i ochrona → Tryb dewelopera** (po restarcie).
3. Wybierz iPhone'a jako cel i naciśnij **Run (▶)**.
4. Przy pierwszym uruchomieniu: **Ustawienia → Ogólne → VPN i zarządzanie urządzeniem** → zaufaj swojemu profilowi.
5. Przy pierwszym starcie zezwól na dostęp do sieci lokalnej.

Darmowe konto Apple: aplikacja wygasa po 7 dniach, wystarczy ponownie nacisnąć Run. Konto Developer (99 USD/rok) wydłuża to do roku.

## Użycie

1. Wpisz IP kamery, kliknij **Zaloguj się do Google**.
2. Wybierz tryb. Ręczny: *Zrób zdjęcie* / *Nagraj film*, potem ikona chmury przy pliku.
   Automatyczny: wszystko leci od razu na Dysk, a *Start* robi zdjęcia co N sekund.
3. **Praca w tle:** po naciśnięciu *Start* aplikacja poprosi o dostęp do lokalizacji. Wybierz **"Podczas używania aplikacji"** (lub "Zawsze"). Lokalizacja służy tylko do utrzymania aplikacji przy życiu po zgaszeniu ekranu, pozycja nie jest nigdzie zapisywana ani wysyłana. Na pasku statusu pojawi się niebieski wskaźnik. Dzięki temu zdjęcia co N sekund lecą też przy zablokowanym telefonie, a wysyłka na Dysk jest realizowana przez sesję w tle, którą iOS kończy sam.
   - Nie zamykaj aplikacji w przełączniku (przesunięciem w górę), bo to zatrzymuje pętlę.
   - Wyłącz *Tryb niskiego zużycia energii* i zostaw telefon na ładowarce, bo bateria schodzi szybciej.
   - To rozwiązanie tylko do własnej instalacji (App Store by je odrzucił).
   - Gdy iOS mimo wszystko zabije aplikację, rozpoczęte uploady się dokończą, ale cykl zdjęć trzeba uruchomić ponownie.

## Struktura

- `Sources/CameraClient.swift`: pobieranie zdjęcia i nagrywanie MJPEG do MP4
- `Sources/GoogleAuth.swift`: logowanie OAuth + PKCE, token w Keychain
- `Sources/DriveUploader.swift`: folder i upload przez Drive API v3
- `Sources/AppModel.swift`, `ContentView.swift`: logika i interfejs
