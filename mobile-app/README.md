# mobile-app

Aplikacja mobilna **ESP Cam Drive**: pobiera zdjęcia i filmy z kamery ESP32-CAM przez WiFi i wysyła je na Dysk Google. Służy do zbierania danych do projektu.

- `ios/`: kod aplikacji iOS (SwiftUI) wraz z `project.yml` dla XcodeGen.
- Pełna instrukcja (konfiguracja kamery, Google Cloud, instalacja, użycie): [ios/README.md](ios/README.md).

## Build w GitHub Actions

Workflow `.github/workflows/build-ios.yml` buduje niepodpisany plik `.ipa` na runnerze macOS.

- Uruchamia się automatycznie po pushu na branch `feature/mobile-app`, jeśli zmieniły się pliki w `mobile-app/`.
- Można go też odpalić ręcznie (`workflow_dispatch`), gdy plik workflow jest na domyślnym branchu repozytorium.
- Wynik: artefakt `ESPCamDrive-ipa` na stronie przebiegu w zakładce **Actions**.

Plik `.ipa` jest niepodpisany, więc przed instalacją na iPhonie trzeba go podpisać (np. własnym Apple ID).
