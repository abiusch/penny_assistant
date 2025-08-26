# Development Assistant Brief - PennyGPT Current State

## Current Working State (December 2024)
**The voice assistant is now fully functional:**
- ✅ Records audio from MacBook microphone (device 1)
- ✅ Transcribes speech using Whisper (base model)
- ✅ Gets intelligent responses from Ollama/llama3
- ✅ All 11 tests passing
- ✅ Full conversation loop working

## Recent Fixes Applied

### 1. Package Structure Consolidation
- Migrated from duplicate `core/` + `src/core/` to single `src/` layout
- Fixed all imports to use `from core...` with `PYTHONPATH=src`
- Created `pyproject.toml` for proper package installation
- Removed duplicate directories that were causing import ambiguity

### 2. Audio Pipeline Fixes
- Fixed microphone device selection (was defaulting to iPhone, now MacBook Pro)
- Lowered silence threshold from 0.01 to 0.005 (was rejecting normal speech as silence)
- Added audio device configuration to `penny_config.json`
- Verified Whisper transcription working with real audio

### 3. LLM Integration
- Fixed `LocalLLM` adapter to actually call Ollama via subprocess (was just echoing)
- Installed Ollama and pulled llama3 model
- Added `generate()` method to GPTOSS adapter for interface compatibility
- LLM router now correctly selects between local/cloud modes

## Project Structure
- **Repo layout:** Everything under `src/` (clean single-tree structure)
- **Config:** `penny_config.json` at repo root with audio device settings
- **Python:** Currently 3.13 (works with warnings), 3.11 recommended for audio stability
- **Platform:** macOS development environment
- **Dependencies:** All in `requirements.txt`, Ollama installed separately

## Working Commands
```bash
# Activate environment
source .venv/bin/activate

# Run tests (all passing)
PYTHONPATH=src pytest -q tests --ignore=whisper --tb=short

# Run voice assistant
PYTHONPATH=src python penny_simple_fixed.py

# Debug audio issues
PYTHONPATH=src python debug_audio.py
```

## File Map (Key Components)
```
src/
├── core/
│   ├── pipeline.py         # Main execution flow
│   ├── llm_router.py       # LLM selection logic
│   ├── personality.py      # Tone/style application
│   └── intent_router.py    # Intent classification
├── adapters/
│   ├── llm/
│   │   ├── local_ollama_adapter.py  # Fixed to call Ollama
│   │   └── factory.py              # LLM factory pattern
│   ├── stt/
│   │   └── whisper_adapter.py      # Whisper transcription
│   └── tts/
│       └── google_tts_adapter.py   # Google TTS (not yet connected)
```

## Known Issues & Next Steps

### Current Issues
- Python 3.13 compatibility warnings (but everything works)
- macOS accessibility permissions needed for keyboard monitoring in main `penny.py`
- TTS not yet integrated in pipeline (gTTS installed but not connected)

### Recommended Next Steps
1. **Commit working code** - Everything is functional, save this state
2. **Consider Python 3.11** - Would eliminate audio library warnings
3. **Add TTS integration** - Connect google_tts_adapter to pipeline
4. **Fix macOS accessibility** - For spacebar triggering in main app

## Testing & Verification
```bash
# Quick health check
python -c "from src.core.pipeline import run_once; print(run_once())"

# Test Ollama connection
ollama run llama3 "test"

# Test audio recording
python -c "import sounddevice as sd; print(sd.query_devices())"
```

## Security & Best Practices
- ✅ Using `subprocess.run()` instead of `os.system()`
- ✅ Temp file cleanup in Whisper adapter
- ✅ Resource management with try/finally blocks
- ✅ No shell injection vulnerabilities
- ✅ Proper error handling in adapters

## Development Notes
- Always use `PYTHONPATH=src` when running scripts
- The silence threshold (0.005) may need tuning for different environments
- Ollama must be running for LLM responses to work
- Device 1 is hardcoded as MacBook microphone - adjust if needed

---
*This brief represents the current working state after resolving ~20 critical issues including import errors, package structure problems, and audio pipeline failures. The system is now functional end-to-end.*
