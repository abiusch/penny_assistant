// Swift file for the menu bar app
import SwiftUI
import Foundation
import AppKit

@main
struct PennyMenuBarApp: App {
    @StateObject private var pennyService = PennyService()
    
    var body: some Scene {
        MenuBarExtra("Penny", systemImage: "mic.circle") {
            MenuBarView()
                .environmentObject(pennyService)
        }
    }
}

struct MenuBarView: View {
    @EnvironmentObject var pennyService: PennyService
    @State private var showingSettings = false
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Status Section
            HStack {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                Text(statusText)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Spacer()
            }
            .padding(.horizontal, 12)
            .padding(.top, 8)
            
            Divider()
            
            // Push-to-Talk Toggle
            Button(action: {
                pennyService.togglePTT()
            }) {
                HStack {
                    Image(systemName: pennyService.isPTTActive ? "mic.fill" : "mic.slash")
                    Text(pennyService.isPTTActive ? "Stop PTT" : "Start PTT")
                    Spacer()
                }
            }
            .keyboardShortcut("s", modifiers: [.command, .shift])
            
            // Test Speak
            Button(action: {
                pennyService.testSpeak()
            }) {
                HStack {
                    Image(systemName: "speaker.wave.2")
                    Text("Test Speech")
                    Spacer()
                }
            }
            .keyboardShortcut("t", modifiers: [.command, .shift])
            
            // Settings
            Button(action: {
                showingSettings = true
            }) {
                HStack {
                    Image(systemName: "gear")
                    Text("Settings")
                    Spacer()
                }
            }
            
            Divider()
            
            // Health Status
            HStack {
                Text("Health:")
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(pennyService.healthStatus)
                    .font(.caption)
                    .foregroundColor(pennyService.isHealthy ? .green : .red)
                Spacer()
                Button("Refresh") {
                    pennyService.checkHealth()
                }
                .font(.caption)
            }
            .padding(.horizontal, 12)
            
            Divider()
            
            // Quit
            Button("Quit Penny") {
                NSApplication.shared.terminate(nil)
            }
            .keyboardShortcut("q", modifiers: [.command])
        }
        .frame(width: 250)
        .onAppear {
            pennyService.startHealthMonitoring()
        }
        .sheet(isPresented: $showingSettings) {
            SettingsView()
                .environmentObject(pennyService)
        }
    }
    
    private var statusColor: Color {
        switch pennyService.currentStatus {
        case .idle: return .gray
        case .listening: return .blue
        case .speaking: return .green
        case .error: return .red
        }
    }
    
    private var statusText: String {
        switch pennyService.currentStatus {
        case .idle: return "Idle"
        case .listening: return "Listening..."
        case .speaking: return "Speaking..."
        case .error: return "Error"
        }
    }
}

struct SettingsView: View {
    @EnvironmentObject var pennyService: PennyService
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Penny Settings")
                .font(.title2)
                .fontWeight(.bold)
            
            Divider()
            
            // Server Configuration
            GroupBox("Server Configuration") {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text("Server URL:")
                        TextField("http://127.0.0.1:8080", text: $pennyService.serverURL)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    HStack {
                        Button("Test Connection") {
                            pennyService.checkHealth()
                        }
                        Spacer()
                        Text(pennyService.healthStatus)
                            .foregroundColor(pennyService.isHealthy ? .green : .red)
                    }
                }
                .padding(8)
            }
            
            // Audio Settings
            GroupBox("Audio Settings") {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Input Device: System Default")
                        .foregroundColor(.secondary)
                    Text("Output Device: System Default")
                        .foregroundColor(.secondary)
                    Text("Note: Device selection managed by daemon")
                        .font(.caption)
                        .foregroundColor(.secondary)
                }
                .padding(8)
            }
            
            Spacer()
            
            HStack {
                Button("Cancel") {
                    dismiss()
                }
                Spacer()
                Button("Save") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding()
        .frame(width: 400, height: 300)
    }
}

// MARK: - Service Layer

class PennyService: ObservableObject {
    @Published var isPTTActive = false
    @Published var currentStatus: PennyStatus = .idle
    @Published var healthStatus = "Unknown"
    @Published var isHealthy = false
    @Published var serverURL = "http://127.0.0.1:8080"
    
    private var healthTimer: Timer?
    
    enum PennyStatus {
        case idle, listening, speaking, error
    }
    
    func startHealthMonitoring() {
        checkHealth()
        healthTimer = Timer.scheduledTimer(withTimeInterval: 10.0, repeats: true) { _ in
            self.checkHealth()
        }
    }
    
    func checkHealth() {
        guard let url = URL(string: "\(serverURL)/health") else {
            updateHealthStatus(false, "Invalid URL")
            return
        }
        
        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                if let error = error {
                    self.updateHealthStatus(false, "Connection failed: \(error.localizedDescription)")
                    return
                }
                
                guard let httpResponse = response as? HTTPURLResponse,
                      httpResponse.statusCode == 200,
                      let data = data else {
                    self.updateHealthStatus(false, "Server error")
                    return
                }
                
                do {
                    let healthData = try JSONDecoder().decode(HealthResponse.self, from: data)
                    let uptimeText = String(format: "%.1fs", healthData.uptime_s)
                    self.updateHealthStatus(healthData.ok, "OK - Uptime: \(uptimeText)")
                    self.isPTTActive = healthData.ptt_active
                } catch {
                    self.updateHealthStatus(false, "Parse error")
                }
            }
        }.resume()
    }
    
    private func updateHealthStatus(_ healthy: Bool, _ status: String) {
        isHealthy = healthy
        healthStatus = status
        currentStatus = healthy ? .idle : .error
    }
    
    func togglePTT() {
        let endpoint = isPTTActive ? "/ptt/stop" : "/ptt/start"
        guard let url = URL(string: "\(serverURL)\(endpoint)") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                if error == nil, let httpResponse = response as? HTTPURLResponse,
                   httpResponse.statusCode == 200 {
                    self.isPTTActive.toggle()
                    self.currentStatus = self.isPTTActive ? .listening : .idle
                }
            }
        }.resume()
    }
    
    func testSpeak() {
        guard let url = URL(string: "\(serverURL)/speak") else { return }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = ["text": "Hello! This is a test from your menu bar app."]
        request.httpBody = try? JSONEncoder().encode(body)
        
        currentStatus = .speaking
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                // Simulate speaking duration
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
                    self.currentStatus = .idle
                }
            }
        }.resume()
    }
    
    deinit {
        healthTimer?.invalidate()
    }
}

// MARK: - Data Models

struct HealthResponse: Codable {
    let ok: Bool
    let uptime_s: Double
    let ptt_active: Bool
}
