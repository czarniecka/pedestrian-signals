import Foundation

enum Config {
    /// Wklej tutaj Client ID z Google Cloud Console (typ klienta: iOS).
    static let googleClientID = "WKLEJ_TUTAJ_CLIENT_ID.apps.googleusercontent.com"

    static let scope = "https://www.googleapis.com/auth/drive.file"

    /// Schemat przekierowania Google dla klientów iOS = odwrócony Client ID.
    static var redirectScheme: String {
        googleClientID.split(separator: ".").reversed().joined(separator: ".")
    }
    static var redirectURI: String { "\(redirectScheme):/oauth2redirect" }
}

struct AppError: LocalizedError {
    let message: String
    init(_ message: String) { self.message = message }
    var errorDescription: String? { message }
}
