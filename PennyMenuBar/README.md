# PennyMenuBar - SwiftUI Menu Bar App

A native macOS menu bar application for controlling your PennyGPT voice assistant via HTTP API.

## 🎯 Features

### Core Functionality
- **Menu Bar Integration**: Lives in your macOS menu bar with status indicator
- **Push-to-Talk Control**: Toggle PTT mode on/off via menu or keyboard shortcuts
- **Health Monitoring**: Real-time connection status to your PennyGPT daemon
- **Test Speech**: Quick test of TTS functionality
- **Settings Panel**: Configure server URL and view connection status

### Visual Status Indicators
- 🔴 **Red**: Connection error or daemon offline
- 🔵 **Blue**: Listening (PTT active)
- 🟢 **Green**: Speaking (TTS active)
- ⚫ **Gray**: Idle (ready)

### Keyboard Shortcuts
- **⌘⇧S**: Toggle Push-to-Talk
- **⌘⇧T**: Test Speech
- **⌘Q**: Quit application

## 🛠️ Setup & Build

### Prerequisites
- macOS 13.0+ (for SwiftUI MenuBarExtra)
- Xcode 15.0+
- Your PennyGPT FastAPI daemon running on `http://127.0.0.1:8080`

### Quick Build
```bash
cd PennyMenuBar
chmod +x build.sh
./build.sh
```

### Manual Xcode Build
1. Open `PennyMenuBar.xcworkspace` in Xcode
2. Select PennyMenuBar scheme
3. Build and Run (⌘R)

## 🔧 Configuration

### Default Settings
- **Server URL**: `http://127.0.0.1:8080`
- **Health Check Interval**: 10 seconds
- **Bundle ID**: `com.penny.menubar`

### Customization
Edit `PennyMenuBarApp.swift` to modify:
- Server URL default
- Health check frequency
- Menu shortcuts
- Status indicators

## 📡 API Integration

The app integrates with your FastAPI daemon endpoints:

### Health Check
```
GET /health
Response: {"ok": true, "uptime_s": 45.2, "ptt_active": false}
```

### PTT Control
```
POST /ptt/start   # Enable push-to-talk
POST /ptt/stop    # Disable push-to-talk
```

### Test Speech
```
POST /speak
Body: {"text": "Hello! This is a test from your menu bar app."}
```

## 🎯 Usage Workflow

1. **Start Your Daemon**: Ensure PennyGPT FastAPI server is running
2. **Launch Menu Bar App**: Double-click built app or use Xcode
3. **Check Status**: Green dot in menu bar = healthy connection
4. **Control PTT**: Click menu icon → "Start PTT" or use ⌘⇧S
5. **Test Speech**: Use "Test Speech" button or ⌘⇧T
6. **Monitor Health**: Status updates every 10 seconds automatically

## 🚀 Integration with PennyGPT

This menu bar app is designed to work with your production-ready PennyGPT system:

- **FastAPI Daemon**: Uses your existing HTTP endpoints
- **Personality System**: Leverages your 4-tone personality presets
- **Safety Guardrails**: Benefits from your sensitive topic detection
- **Production Ready**: Built on your 22/22 passing test foundation

## 🔍 Troubleshooting

### Connection Issues
- Verify daemon is running: `curl http://127.0.0.1:8080/health`
- Check firewall settings
- Ensure port 8080 is available

### Build Issues
- Update Xcode to latest version
- Verify deployment target (macOS 13.0+)
- Check code signing settings

### Permission Issues
- Menu bar apps require no special permissions
- Network requests use standard macOS networking

## 🎉 Next Steps

With this menu bar app, you now have:
✅ **Daily dogfooding capability** - Use PennyGPT throughout your day
✅ **Visual feedback** - Always know system status at a glance  
✅ **Quick controls** - PTT and speech testing via menu/shortcuts
✅ **Production integration** - Built on your proven FastAPI foundation

Ready to enhance with ChatGPT's remaining roadmap items:
- First-run checks ("penny doctor")
- TTS latency polish with caching
- Calendar integration improvements
- CI/docs cleanup

The foundation is solid and the daily workflow is unlocked! 🚀
