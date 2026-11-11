import Foundation
import AuthenticationServices
import CryptoKit
import UIKit

enum Keychain {
    static func set(_ key: String, _ value: String?) {
        let q: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                kSecAttrAccount as String: key]
        SecItemDelete(q as CFDictionary)
        guard let value else { return }
        var a = q
        a[kSecValueData as String] = Data(value.utf8)
        SecItemAdd(a as CFDictionary, nil)
    }

    static func get(_ key: String) -> String? {
        let q: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                kSecAttrAccount as String: key,
                                kSecReturnData as String: true,
                                kSecMatchLimit as String: kSecMatchLimitOne]
        var out: AnyObject?
        guard SecItemCopyMatching(q as CFDictionary, &out) == errSecSuccess,
              let d = out as? Data else { return nil }
        return String(data: d, encoding: .utf8)
    }
}

extension Data {
    var base64URL: String {
        base64EncodedString()
            .replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_")
            .replacingOccurrences(of: "=", with: "")
    }
}

private struct TokenResponse: Decodable {
    let access_token: String
    let expires_in: Int
    let refresh_token: String?
}

/// Logowanie do Google (OAuth 2.0 + PKCE), bez żadnych zewnętrznych bibliotek.
final class GoogleAuth: NSObject, ObservableObject, ASWebAuthenticationPresentationContextProviding {
    @Published var isSignedIn = false

    private var session: ASWebAuthenticationSession?
    private var accessToken: String?
    private var expiry = Date.distantPast

    override init() {
        super.init()
        isSignedIn = Keychain.get("refresh") != nil
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        UIApplication.shared.connectedScenes
            .compactMap { ($0 as? UIWindowScene)?.keyWindow }
            .first ?? ASPresentationAnchor()
    }

    @MainActor
    func signIn() async throws {
        if Config.googleClientID.contains("WKLEJ_TUTAJ") {
            throw AppError("Wpisz Client ID z Google Cloud w Sources/Config.swift")
        }
        let verifier = Self.randomString(64)
        let challenge = Data(SHA256.hash(data: Data(verifier.utf8))).base64URL

        var c = URLComponents(string: "https://accounts.google.com/o/oauth2/v2/auth")!
        c.queryItems = [
            .init(name: "client_id", value: Config.googleClientID),
            .init(name: "redirect_uri", value: Config.redirectURI),
            .init(name: "response_type", value: "code"),
            .init(name: "scope", value: Config.scope),
            .init(name: "code_challenge", value: challenge),
            .init(name: "code_challenge_method", value: "S256"),
            .init(name: "access_type", value: "offline"),
            .init(name: "prompt", value: "consent"),
        ]

        let callback: URL = try await withCheckedThrowingContinuation { cont in
            let s = ASWebAuthenticationSession(url: c.url!, callbackURLScheme: Config.redirectScheme) { url, err in
                if let url { cont.resume(returning: url) }
                else { cont.resume(throwing: err ?? AppError("Logowanie przerwane")) }
            }
            s.presentationContextProvider = self
            self.session = s
            s.start()
        }

        guard let code = URLComponents(url: callback, resolvingAgainstBaseURL: false)?
            .queryItems?.first(where: { $0.name == "code" })?.value
        else { throw AppError("Google nie zwróciło kodu logowania") }

        let r = try await tokenRequest([
            "client_id": Config.googleClientID,
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": Config.redirectURI,
            "grant_type": "authorization_code",
        ])
        accessToken = r.access_token
        expiry = Date().addingTimeInterval(Double(r.expires_in))
        guard let rt = r.refresh_token else { throw AppError("Brak refresh tokenu od Google") }
        Keychain.set("refresh", rt)
        isSignedIn = true
    }

    func signOut() {
        Keychain.set("refresh", nil)
        accessToken = nil
        DispatchQueue.main.async { self.isSignedIn = false }
    }

    func validAccessToken() async throws -> String {
        if let t = accessToken, expiry > Date().addingTimeInterval(60) { return t }
        guard let rt = Keychain.get("refresh") else { throw AppError("Zaloguj się do Google") }
        do {
            let r = try await tokenRequest([
                "client_id": Config.googleClientID,
                "refresh_token": rt,
                "grant_type": "refresh_token",
            ])
            accessToken = r.access_token
            expiry = Date().addingTimeInterval(Double(r.expires_in))
            return r.access_token
        } catch {
            signOut()
            throw AppError("Sesja Google wygasła, zaloguj się ponownie")
        }
    }

    private func tokenRequest(_ params: [String: String]) async throws -> TokenResponse {
        var req = URLRequest(url: URL(string: "https://oauth2.googleapis.com/token")!)
        req.httpMethod = "POST"
        req.setValue("application/x-www-form-urlencoded", forHTTPHeaderField: "Content-Type")
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-._~"))
        req.httpBody = params
            .map { "\($0.key)=\($0.value.addingPercentEncoding(withAllowedCharacters: allowed) ?? "")" }
            .joined(separator: "&")
            .data(using: .utf8)
        let (data, resp) = try await URLSession.shared.data(for: req)
        guard (resp as? HTTPURLResponse)?.statusCode == 200 else {
            throw AppError("Google: " + String((String(data: data, encoding: .utf8) ?? "").prefix(200)))
        }
        return try JSONDecoder().decode(TokenResponse.self, from: data)
    }

    private static func randomString(_ n: Int) -> String {
        var b = [UInt8](repeating: 0, count: n)
        _ = SecRandomCopyBytes(kSecRandomDefault, n, &b)
        return Data(b).base64URL
    }
}
