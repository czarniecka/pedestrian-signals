import Foundation
import UIKit

/// Wysyłka plików przez sesję w tle: iOS dokończy upload nawet po zawieszeniu aplikacji.
final class BackgroundUploader: NSObject, URLSessionDataDelegate {
    static let shared = BackgroundUploader()
    static var completionHandler: (() -> Void)?

    private let lock = NSLock()
    private var pending: [Int: (cont: CheckedContinuation<Void, Error>, tmp: URL)] = [:]
    private var bodies: [Int: Data] = [:]

    private lazy var session: URLSession = {
        let c = URLSessionConfiguration.background(withIdentifier: "com.ola.espcamdrive.upload")
        c.sessionSendsLaunchEvents = true
        c.isDiscretionary = false
        c.waitsForConnectivity = true
        return URLSession(configuration: c, delegate: self, delegateQueue: nil)
    }()

    /// Wywołaj przy starcie, żeby odtworzyć sesję po wybudzeniu aplikacji przez system.
    func reconnect() { _ = session }

    func upload(request: URLRequest, fromFile tmp: URL) async throws {
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Void, Error>) in
            let task = session.uploadTask(with: request, fromFile: tmp)
            lock.withLock { pending[task.taskIdentifier] = (cont, tmp) }
            task.resume()
        }
    }

    func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
        lock.withLock { bodies[dataTask.taskIdentifier, default: Data()].append(data) }
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        let (p, body) = lock.withLock {
            (pending.removeValue(forKey: task.taskIdentifier), bodies.removeValue(forKey: task.taskIdentifier))
        }

        if let tmp = p?.tmp { try? FileManager.default.removeItem(at: tmp) }
        guard let cont = p?.cont else { return }   // aplikacja została wznowiona po zabiciu: upload i tak się wykonał

        if let error { cont.resume(throwing: error); return }
        let code = (task.response as? HTTPURLResponse)?.statusCode ?? 0
        if (200..<300).contains(code) {
            cont.resume()
        } else {
            let text = String(data: body ?? Data(), encoding: .utf8) ?? ""
            cont.resume(throwing: AppError("Dysk Google (\(code)): \(text.prefix(200))"))
        }
    }

    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        DispatchQueue.main.async {
            Self.completionHandler?()
            Self.completionHandler = nil
        }
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        BackgroundUploader.shared.reconnect()   // odbiera wyniki uploadów rozpoczętych w poprzednim uruchomieniu
        return true
    }

    func application(_ application: UIApplication, handleEventsForBackgroundURLSession identifier: String,
                     completionHandler: @escaping () -> Void) {
        BackgroundUploader.completionHandler = completionHandler
        BackgroundUploader.shared.reconnect()
    }
}
