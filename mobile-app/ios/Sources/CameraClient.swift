import Foundation
import AVFoundation
import UIKit

/// Zakłada standardowy szkic Arduino "CameraWebServer":
///   zdjęcie:  http://IP/capture   (port 80)
///   strumień: http://IP:81/stream (MJPEG)
struct CameraClient {
    let host: String

    private var base: String {
        var h = host.trimmingCharacters(in: .whitespacesAndNewlines)
        for p in ["http://", "https://"] where h.hasPrefix(p) { h.removeFirst(p.count) }
        while h.hasSuffix("/") { h.removeLast() }
        return h
    }
    private var hostOnly: String { String(base.split(separator: ":").first ?? "") }

    var captureURL: URL? { URL(string: "http://\(base)/capture") }
    var streamURL: URL? { URL(string: "http://\(hostOnly):81/stream") }

    func captureJPEG() async throws -> Data {
        guard let url = captureURL else { throw AppError("Nieprawidłowy adres kamery") }
        var req = URLRequest(url: url)
        req.timeoutInterval = 10
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard (resp as? HTTPURLResponse)?.statusCode == 200,
              data.count > 1000, data[0] == 0xFF, data[1] == 0xD8
        else { throw AppError("Kamera nie zwróciła zdjęcia (sprawdź adres IP)") }
        return data
    }
}

/// Nagrywa strumień MJPEG z ESP32-CAM do pliku MP4.
enum MJPEGRecorder {
    static func record(camera: CameraClient, seconds: Double, to url: URL) async throws {
        guard let streamURL = camera.streamURL else { throw AppError("Nieprawidłowy adres kamery") }
        var req = URLRequest(url: streamURL)
        req.timeoutInterval = 15
        let (bytes, resp) = try await URLSession.shared.bytes(for: req)
        guard (resp as? HTTPURLResponse)?.statusCode == 200 else {
            throw AppError("Nie można otworzyć strumienia (czy inne urządzenie go nie ogląda?)")
        }

        try? FileManager.default.removeItem(at: url)
        var writer: AVAssetWriter?
        var input: AVAssetWriterInput?
        var adaptor: AVAssetWriterInputPixelBufferAdaptor?

        let start = Date()
        var lastT = -1.0
        var frames = 0
        var buf = [UInt8]()
        buf.reserveCapacity(120_000)
        var inFrame = false
        var prev: UInt8 = 0

        for try await b in bytes {
            if inFrame {
                buf.append(b)
                if prev == 0xFF && b == 0xD9 {            // koniec klatki JPEG
                    inFrame = false
                    let t = Date().timeIntervalSince(start)
                    if let cg = UIImage(data: Data(buf))?.cgImage {
                        if writer == nil {
                            let w = try AVAssetWriter(outputURL: url, fileType: .mp4)
                            let inp = AVAssetWriterInput(mediaType: .video, outputSettings: [
                                AVVideoCodecKey: AVVideoCodecType.h264,
                                AVVideoWidthKey: cg.width,
                                AVVideoHeightKey: cg.height,
                            ])
                            inp.expectsMediaDataInRealTime = true
                            let ad = AVAssetWriterInputPixelBufferAdaptor(
                                assetWriterInput: inp,
                                sourcePixelBufferAttributes: [
                                    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA,
                                    kCVPixelBufferWidthKey as String: cg.width,
                                    kCVPixelBufferHeightKey as String: cg.height,
                                ])
                            w.add(inp)
                            w.startWriting()
                            w.startSession(atSourceTime: .zero)
                            writer = w; input = inp; adaptor = ad
                        }
                        if let inp = input, let ad = adaptor, let pool = ad.pixelBufferPool,
                           inp.isReadyForMoreMediaData, t > lastT,
                           let pb = makeBuffer(cg, pool: pool) {
                            ad.append(pb, withPresentationTime: CMTime(seconds: t, preferredTimescale: 600))
                            lastT = t
                            frames += 1
                        }
                    }
                    buf.removeAll(keepingCapacity: true)
                    if t >= seconds { break }
                }
            } else if prev == 0xFF && b == 0xD8 {          // początek klatki JPEG
                inFrame = true
                buf = [0xFF, 0xD8]
            }
            prev = b
        }

        guard let w = writer, let inp = input, frames > 0 else {
            throw AppError("Nie odebrano żadnych klatek ze strumienia")
        }
        inp.markAsFinished()
        await w.finishWriting()
        if w.status != .completed { throw AppError("Nie udało się zapisać filmu") }
    }

    private static func makeBuffer(_ cg: CGImage, pool: CVPixelBufferPool) -> CVPixelBuffer? {
        var pb: CVPixelBuffer?
        CVPixelBufferPoolCreatePixelBuffer(nil, pool, &pb)
        guard let pb else { return nil }
        CVPixelBufferLockBaseAddress(pb, [])
        defer { CVPixelBufferUnlockBaseAddress(pb, []) }
        guard let ctx = CGContext(
            data: CVPixelBufferGetBaseAddress(pb),
            width: CVPixelBufferGetWidth(pb),
            height: CVPixelBufferGetHeight(pb),
            bitsPerComponent: 8,
            bytesPerRow: CVPixelBufferGetBytesPerRow(pb),
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue
        ) else { return nil }
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: CVPixelBufferGetWidth(pb), height: CVPixelBufferGetHeight(pb)))
        return pb
    }
}
