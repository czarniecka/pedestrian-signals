import Foundation

/// Wysyłanie plików do Dysku Google (REST API v3, zakres drive.file).
final class DriveUploader {
    private let auth: GoogleAuth
    private var folderCache: [String: String] = [:]

    init(auth: GoogleAuth) { self.auth = auth }

    func upload(fileURL: URL, mime: String, folderName: String) async throws {
        let folderID = try await folder(named: folderName)
        let token = try await auth.validAccessToken()

        // Multipart zapisujemy do pliku tymczasowego, żeby nie trzymać filmu w pamięci.
        let boundary = UUID().uuidString
        // Plik zostaje, dopóki sesja w tle nie skończy wysyłki (usuwa go BackgroundUploader).
        let tmp = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("upload-\(UUID().uuidString)")
        FileManager.default.createFile(atPath: tmp.path, contents: nil)

        let meta = try JSONSerialization.data(withJSONObject: [
            "name": fileURL.lastPathComponent,
            "parents": [folderID],
        ])
        let out = try FileHandle(forWritingTo: tmp)
        try out.write(contentsOf: Data("--\(boundary)\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".utf8))
        try out.write(contentsOf: meta)
        try out.write(contentsOf: Data("\r\n--\(boundary)\r\nContent-Type: \(mime)\r\n\r\n".utf8))
        let src = try FileHandle(forReadingFrom: fileURL)
        while let chunk = try src.read(upToCount: 1 << 20), !chunk.isEmpty {
            try out.write(contentsOf: chunk)
        }
        try out.write(contentsOf: Data("\r\n--\(boundary)--".utf8))
        try out.close()
        try src.close()

        var req = URLRequest(url: URL(string: "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart")!)
        req.httpMethod = "POST"
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        req.setValue("multipart/related; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        try await BackgroundUploader.shared.upload(request: req, fromFile: tmp)
    }

    private func folder(named name: String) async throws -> String {
        if let id = folderCache[name] { return id }
        let token = try await auth.validAccessToken()

        let escaped = name.replacingOccurrences(of: "\\", with: "\\\\").replacingOccurrences(of: "'", with: "\\'")
        var c = URLComponents(string: "https://www.googleapis.com/drive/v3/files")!
        c.queryItems = [
            .init(name: "q", value: "name='\(escaped)' and mimeType='application/vnd.google-apps.folder' and trashed=false"),
            .init(name: "fields", value: "files(id)"),
        ]
        var req = URLRequest(url: c.url!)
        req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        let (data, resp) = try await URLSession.shared.data(for: req)
        try check(resp, data)

        struct List: Decodable { struct F: Decodable { let id: String }; let files: [F] }
        if let id = try JSONDecoder().decode(List.self, from: data).files.first?.id {
            folderCache[name] = id
            return id
        }

        var create = URLRequest(url: URL(string: "https://www.googleapis.com/drive/v3/files?fields=id")!)
        create.httpMethod = "POST"
        create.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        create.setValue("application/json", forHTTPHeaderField: "Content-Type")
        create.httpBody = try JSONSerialization.data(withJSONObject: [
            "name": name, "mimeType": "application/vnd.google-apps.folder",
        ])
        let (d2, r2) = try await URLSession.shared.data(for: create)
        try check(r2, d2)
        struct Created: Decodable { let id: String }
        let id = try JSONDecoder().decode(Created.self, from: d2).id
        folderCache[name] = id
        return id
    }

    private func check(_ resp: URLResponse, _ data: Data) throws {
        let code = (resp as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(code) else {
            let body = String(data: data, encoding: .utf8) ?? ""
            throw AppError("Dysk Google (\(code)): \(body.prefix(200))")
        }
    }
}
