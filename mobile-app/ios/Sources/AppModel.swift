import Foundation
import UIKit

struct Item: Identifiable {
    let id = UUID()
    let url: URL
    let isVideo: Bool
    var uploaded = false
    var thumb: UIImage?
}

@MainActor
final class AppModel: ObservableObject {
    @Published var items: [Item] = []
    @Published var status = "Wpisz adres IP kamery i zaloguj się do Google"
    @Published var busy = false
    @Published var autoRunning = false

    let auth = GoogleAuth()
    private lazy var drive = DriveUploader(auth: auth)
    private var autoTask: Task<Void, Never>?
    private let keeper = BackgroundKeeper()

    // MARK: Google

    func signIn() async {
        do { try await auth.signIn(); status = "Zalogowano do Google" }
        catch { status = "Logowanie: \(error.localizedDescription)" }
    }

    // MARK: Zdjęcie / film

    func photo(host: String, autoUpload: Bool, folder: String) async {
        guard !busy else { return }
        busy = true
        defer { busy = false }
        status = "Pobieram zdjęcie…"
        do {
            let data = try await CameraClient(host: host).captureJPEG()
            let url = Self.newFileURL(prefix: "IMG", ext: "jpg")
            try data.write(to: url)
            let thumb = UIImage(data: data)?.preparingThumbnail(of: CGSize(width: 120, height: 120))
            let item = Item(url: url, isVideo: false, thumb: thumb)
            items.insert(item, at: 0)
            status = "Zdjęcie zapisane"
            if autoUpload { await uploadItem(item.id, folder: folder) }
        } catch {
            status = "Błąd: \(error.localizedDescription)"
        }
    }

    func video(host: String, seconds: Int, autoUpload: Bool, folder: String) async {
        guard !busy else { return }
        busy = true
        defer { busy = false }
        status = "Nagrywam \(seconds) s…"
        do {
            let url = Self.newFileURL(prefix: "VID", ext: "mp4")
            try await MJPEGRecorder.record(camera: CameraClient(host: host), seconds: Double(seconds), to: url)
            let item = Item(url: url, isVideo: true)
            items.insert(item, at: 0)
            status = "Film zapisany"
            if autoUpload { await uploadItem(item.id, folder: folder) }
        } catch {
            status = "Błąd: \(error.localizedDescription)"
        }
    }

    // MARK: Wysyłka

    func uploadItem(_ id: UUID, folder: String) async {
        guard let i = items.firstIndex(where: { $0.id == id }) else { return }
        let item = items[i]
        status = "Wysyłam \(item.url.lastPathComponent)…"
        do {
            try await drive.upload(fileURL: item.url,
                                   mime: item.isVideo ? "video/mp4" : "image/jpeg",
                                   folderName: folder)
            if let j = items.firstIndex(where: { $0.id == id }) { items[j].uploaded = true }
            status = "Wysłano na Dysk: \(item.url.lastPathComponent)"
        } catch {
            status = "Błąd wysyłki: \(error.localizedDescription)"
        }
    }

    // MARK: Tryb automatyczny (zdjęcia co N sekund)

    func startAuto(host: String, interval: Int, folder: String) {
        guard autoTask == nil else { return }
        autoRunning = true
        keeper.start()   // lokalizacja w tle utrzymuje aplikację przy życiu po zgaszeniu ekranu
        if keeper.isDenied {
            status = "Włącz lokalizację dla aplikacji w Ustawieniach, inaczej cykl zatrzyma się po zgaszeniu ekranu"
        }
        autoTask = Task { [weak self] in
            while !Task.isCancelled {
                await self?.photo(host: host, autoUpload: true, folder: folder)
                try? await Task.sleep(nanoseconds: UInt64(interval) * 1_000_000_000)
            }
        }
    }

    func stopAuto() {
        autoTask?.cancel()
        autoTask = nil
        autoRunning = false
        keeper.stop()
        status = "Zatrzymano"
    }

    // MARK: Pliki

    private static func newFileURL(prefix: String, ext: String) -> URL {
        let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("ESPCam", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        let f = DateFormatter()
        f.dateFormat = "yyyyMMdd_HHmmss"
        return dir.appendingPathComponent("\(prefix)_\(f.string(from: Date())).\(ext)")
    }
}
