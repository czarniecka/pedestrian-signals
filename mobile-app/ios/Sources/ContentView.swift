import SwiftUI

struct ContentView: View {
    @StateObject private var model = AppModel()
    @AppStorage("host") private var host = ""
    @AppStorage("folder") private var folder = "ESP32-CAM"
    @AppStorage("autoMode") private var autoMode = false
    @AppStorage("videoSec") private var videoSec = 10
    @AppStorage("interval") private var interval = 60

    var body: some View {
        NavigationStack {
            Form {
                Section("Kamera ESP32-CAM") {
                    TextField("Adres IP, np. 192.168.1.50", text: $host)
                        .keyboardType(.numbersAndPunctuation)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }

                Section("Dysk Google") {
                    GoogleRow(auth: model.auth) { Task { await model.signIn() } }
                    TextField("Folder na Dysku", text: $folder)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }

                Section("Tryb") {
                    Picker("Tryb", selection: $autoMode) {
                        Text("Ręczny").tag(false)
                        Text("Automatyczny").tag(true)
                    }
                    .pickerStyle(.segmented)
                    Text(autoMode
                         ? "Każde zdjęcie i film od razu trafia na Dysk. Zdjęcia można robić cyklicznie."
                         : "Najpierw podgląd na liście, na Dysk wysyłasz przyciskiem przy pliku.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Stepper("Długość filmu: \(videoSec) s", value: $videoSec, in: 3...120)
                    if autoMode {
                        Stepper("Zdjęcie co \(interval) s", value: $interval, in: 5...3600, step: 5)
                    }
                }

                Section {
                    Button { Task { await model.photo(host: host, autoUpload: autoMode, folder: folder) } } label: {
                        Label("Zrób zdjęcie", systemImage: "camera")
                    }
                    .disabled(model.busy || host.isEmpty)

                    Button { Task { await model.video(host: host, seconds: videoSec, autoUpload: autoMode, folder: folder) } } label: {
                        Label("Nagraj film", systemImage: "video")
                    }
                    .disabled(model.busy || host.isEmpty)

                    if autoMode {
                        if model.autoRunning {
                            Button(role: .destructive) { model.stopAuto() } label: {
                                Label("Zatrzymaj cykliczne zdjęcia", systemImage: "stop.circle")
                            }
                        } else {
                            Button { model.startAuto(host: host, interval: interval, folder: folder) } label: {
                                Label("Start: zdjęcia co \(interval) s", systemImage: "play.circle")
                            }
                            .disabled(host.isEmpty || !model.auth.isSignedIn)
                        }
                    }
                } footer: {
                    Text(model.status)
                }

                if !model.items.isEmpty {
                    Section("Pliki") {
                        ForEach(model.items) { item in
                            ItemRow(item: item) {
                                Task { await model.uploadItem(item.id, folder: folder) }
                            }
                        }
                    }
                }
            }
            .navigationTitle("ESP Cam Drive")
        }
    }
}

private struct GoogleRow: View {
    @ObservedObject var auth: GoogleAuth
    let signIn: () -> Void

    var body: some View {
        if auth.isSignedIn {
            HStack {
                Label("Zalogowano", systemImage: "checkmark.circle.fill").foregroundStyle(.green)
                Spacer()
                Button("Wyloguj") { auth.signOut() }
            }
        } else {
            Button(action: signIn) { Label("Zaloguj się do Google", systemImage: "person.crop.circle") }
        }
    }
}

private struct ItemRow: View {
    let item: Item
    let onUpload: () -> Void

    var body: some View {
        HStack(spacing: 12) {
            Group {
                if let t = item.thumb {
                    Image(uiImage: t).resizable().scaledToFill()
                } else {
                    Image(systemName: item.isVideo ? "video.fill" : "photo").foregroundStyle(.secondary)
                }
            }
            .frame(width: 56, height: 56)
            .background(Color.secondary.opacity(0.15))
            .clipShape(RoundedRectangle(cornerRadius: 8))

            Text(item.url.lastPathComponent).font(.footnote)
            Spacer()
            if item.uploaded {
                Image(systemName: "checkmark.icloud.fill").foregroundStyle(.green)
            } else {
                Button(action: onUpload) { Image(systemName: "icloud.and.arrow.up") }
                    .buttonStyle(.borderless)
            }
        }
    }
}
