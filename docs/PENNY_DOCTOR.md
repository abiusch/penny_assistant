# Penny Doctor - System Health Checker

The **Penny Doctor** is a comprehensive diagnostic tool that validates your entire PennyGPT system setup, preventing those frustrating troubleshooting sessions.

## 🎯 What It Checks

### 🐍 Python Environment
- Python version (3.9+ required, 3.11+ recommended)
- Virtual environment activation
- PYTHONPATH configuration

### 📦 Dependencies
- Required Python packages (FastAPI, PyAudio, OpenAI, etc.)
- Import availability
- Version compatibility

### 🔊 Audio System
- Microphone access and permissions
- Speaker/headphone output
- Audio device enumeration
- Basic playback test

### 🧠 LLM Services
- LM Studio connection (localhost:1234)
- Ollama connection (localhost:11434)
- Model availability

### 🗣️ Text-to-Speech
- Google TTS (gTTS) library
- Internet connectivity for TTS
- Speech synthesis functionality

### 🤖 PennyGPT Components
- Core file structure
- Configuration files
- Module importability
- FastAPI server validation

### 🌐 Daemon Service
- FastAPI daemon running status
- Health endpoint response
- PTT control endpoints
- Speech endpoint functionality

### 🔐 macOS Permissions
- Microphone access permissions
- Audio device accessibility
- System security settings

## 🚀 Usage

### Quick Health Check
```bash
# Simple run
./scripts/doctor.sh

# Or directly
python3 penny_doctor.py

# Or as module
python3 -m core.doctor
```

### With PYTHONPATH (Recommended)
```bash
cd /Users/CJ/Desktop/penny_assistant
PYTHONPATH=src python3 penny_doctor.py
```

## 📊 Output Examples

### ✅ Healthy System
```
🏥 Penny Doctor - PennyGPT System Health Check
==================================================

🐍 Python Environment Checks
------------------------------
✅ Python Version
   Found Python 3.11.5

✅ Virtual Environment
   Active virtual environment detected

✅ PYTHONPATH Configuration
   PYTHONPATH: src

📦 Dependency Checks
--------------------
✅ Package: fastapi
   FastAPI web framework

✅ Package: uvicorn
   ASGI server

[... more checks ...]

📋 Health Check Summary
=======================
🎉 All checks passed! Your PennyGPT system is ready to use.
📊 Results: 15/15 checks passed

🚀 Next Steps:
• Your system is ready! Try: PYTHONPATH=src python server.py
• Then test with: curl http://127.0.0.1:8080/health
```

### ❌ Issues Found
```
🏥 Penny Doctor - PennyGPT System Health Check
==================================================

🐍 Python Environment Checks
------------------------------
❌ Python Version
   Found Python 3.8.10
   🔧 Fix: Install Python 3.9+ (recommended: 3.11 or 3.13)

❌ Virtual Environment
   No virtual environment detected
   🔧 Fix: Activate with: source .venv/bin/activate

[... more checks ...]

📋 Health Check Summary
=======================
❌ 3 issues found. System may not work properly.
📊 Results: 12/15 checks passed

🔧 Quick Fixes:
-------------
• Python Version: Install Python 3.9+ (recommended: 3.11 or 3.13)
• Virtual Environment: Activate with: source .venv/bin/activate
• FastAPI Daemon: Start with: cd /path/to/penny_assistant && PYTHONPATH=src python server.py

🚀 Next Steps:
• Fix the issues above and run 'penny doctor' again
• For help, check: docs/TROUBLESHOOTING.md
```

## 🔧 Common Issues & Fixes

### Python Environment Issues
```bash
# Wrong Python version
pyenv install 3.11.5
pyenv global 3.11.5

# No virtual environment
python3 -m venv .venv
source .venv/bin/activate
```

### Missing Dependencies
```bash
# Install all requirements
pip install -r requirements.txt

# Install specific package
pip install fastapi uvicorn pyaudio
```

### Audio Permission Issues (macOS)
1. Go to **System Preferences > Security & Privacy**
2. Click **Privacy** tab
3. Select **Microphone** from left panel
4. Enable access for **Terminal** or your Python app

### FastAPI Daemon Not Running
```bash
# Start the daemon
cd /Users/CJ/Desktop/penny_assistant
PYTHONPATH=src python server.py

# Test it's working
curl http://127.0.0.1:8080/health
```

### LLM Service Issues
```bash
# For LM Studio
# Download and start LM Studio, load a model

# For Ollama
brew install ollama
ollama serve
ollama pull llama2
```

## 🧪 Testing the Doctor

Run the doctor's own tests:
```bash
# Test the doctor itself
PYTHONPATH=src pytest tests/test_penny_doctor.py -v

# Run all tests including doctor
PYTHONPATH=src pytest tests/ -v
```

## 📝 Exit Codes

- **0**: All checks passed, system ready
- **>0**: Number of issues found

Perfect for CI/CD pipelines:
```bash
./scripts/doctor.sh && echo "System healthy!" || echo "Issues found!"
```

## 🎯 Integration with Setup

The doctor integrates with your complete PennyGPT system:
- **Validates your FastAPI daemon** and all endpoints
- **Checks your personality system** and safety guardrails
- **Tests your SwiftUI menu bar app** readiness
- **Verifies production-ready components** (22/22 tests)

## 🔄 Workflow Integration

### During Development
```bash
# Before starting work
./scripts/doctor.sh

# After making changes
./scripts/doctor.sh && git commit
```

### First-Time Setup
```bash
# Clone repository
git clone https://github.com/abiusch/penny_assistant.git
cd penny_assistant

# Run doctor to identify setup needs
./scripts/doctor.sh

# Fix issues and re-run until healthy
./scripts/doctor.sh

# Start using PennyGPT
PYTHONPATH=src python server.py
```

### Production Deployment
```bash
# Pre-deployment health check
./scripts/doctor.sh || exit 1

# Deploy with confidence
docker build -t pennygpt .
```

## 🎉 ChatGPT Roadmap Achievement

**Priority #4 Complete**: First-run checks ("penny doctor")

This completes another major milestone in ChatGPT's roadmap:
1. ✅ **Minimal personality layer** (4 tones + safety)
2. ✅ **Daemon shim endpoints** (FastAPI production-ready) 
3. ✅ **SwiftUI menu-bar shell** (native macOS integration)
4. ✅ **First-run checks** (comprehensive penny doctor)

**Next up**: TTS perceived latency polish and calendar improvements!

The doctor ensures **no more head-scratching sessions** - every component is validated before you start working. 🚀
