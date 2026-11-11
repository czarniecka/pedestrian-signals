import CoreLocation

/// Utrzymuje aplikację przy życiu po zgaszeniu ekranu, odbierając lokalizację w tle
/// (iOS nie zawiesza wtedy procesu, więc pętla zdjęć dalej działa).
/// Uwaga: to rozwiązanie tylko do własnej instalacji, App Store by je odrzucił.
final class BackgroundKeeper: NSObject, CLLocationManagerDelegate {
    private let lm = CLLocationManager()
    private var wanted = false

    override init() {
        super.init()
        lm.delegate = self
        lm.desiredAccuracy = kCLLocationAccuracyThreeKilometers   // najmniejsze zużycie baterii
        lm.distanceFilter = 1000
        lm.pausesLocationUpdatesAutomatically = false
        lm.allowsBackgroundLocationUpdates = true
        lm.showsBackgroundLocationIndicator = true
    }

    var isDenied: Bool {
        lm.authorizationStatus == .denied || lm.authorizationStatus == .restricted
    }

    func start() {
        wanted = true
        switch lm.authorizationStatus {
        case .notDetermined: lm.requestWhenInUseAuthorization()
        case .authorizedAlways, .authorizedWhenInUse: lm.startUpdatingLocation()
        default: break
        }
    }

    func stop() {
        wanted = false
        lm.stopUpdatingLocation()
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        guard wanted else { return }
        if manager.authorizationStatus == .authorizedAlways || manager.authorizationStatus == .authorizedWhenInUse {
            manager.startUpdatingLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {}
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {}
}
