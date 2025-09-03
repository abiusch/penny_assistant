# PennyGPT Next Phase - Task Breakdown for ChatGPT Agent Mode

## 🎉 CURRENT STATUS: FULLY FUNCTIONAL VOICE ASSISTANT ✅
**Last Updated: September 2, 2025**

### **MAJOR BREAKTHROUGH COMPLETED TODAY**
✅ **Real-time voice assistant is now 100% operational** - Full conversation pipeline working end-to-end

### **Key Fixes Applied Today:**
- ✅ **STT Integration**: Fixed to use `transcribe_audio()` directly with numpy arrays
- ✅ **Health Monitor Error**: Fixed with null object pattern for safe fallback
- ✅ **Missing Time Import**: Added to `memory_enhanced_pipeline.py`
- ✅ **TTS Speech Rate**: Optimized to 150 WPM (0.75 config value) for natural conversation
- ✅ **Memory System**: 14 conversations tracked, 5 user preferences learned
- ✅ **Performance Logging**: Complete system with CSV logs, real-time metrics, and session reports

### **Current Performance:**
- STT: ~750ms | LLM: ~1000ms | TTS: 150 WPM | End-to-End: 2-3 seconds

---

## Project Context
Voice assistant with working pipeline: Audio → Whisper → Ollama → gTTS → Speaker
Repository: https://github.com/abiusch/penny_assistant
Working script: `penny_with_tts.py` (run with `PYTHONPATH=src python penny_with_tts.py`)

## 🎯 UPDATED PRIORITIES (Post Voice Assistant Completion)

### **🎯 Priority 1: Performance & Reliability Monitoring** - ⏸️ IN PROGRESS
**Goal**: Add logging and monitoring for optimization

#### Task 1.1: Add Performance Logging - ✅ COMPLETE
- [x] Create `performance_logger.py` with CSV output
- [x] Log per-stage timings: VAD/STT/LLM/TTS + cache hit rates
- [x] Add to `real_time_voice_loop.py` conversation flow
- [x] Generate simple performance reports
- [x] Real-time performance display during conversations
- [x] Session summaries with averages and cache hit rates

#### Task 1.2: Wake-word Hardening
- [ ] Add debounce window to prevent false triggers
- [ ] Implement confidence threshold for wake word detection
- [ ] Unit tests for wake word edge cases and near-matches
- [ ] Test noise resilience

#### Task 1.3: TTS Resilience Testing
- [ ] Test backend failure scenarios (Google TTS down, etc.)
- [ ] Verify barge-in behavior unchanged
- [ ] Add graceful fallback logging
- [ ] Benchmark cold-start vs warmed phrase performance

### **🎯 Priority 2: Pipeline Unification** - ⚠️ PARTIALLY COMPLETE
**Goal**: Use the existing `PipelineLoop` class instead of separate scripts

#### Task 2.1: Create Unified Entry Point
- [x] Real-time voice loop working (`real_time_voice_loop.py`)
- [ ] Create unified `main.py` that uses PipelineLoop 
- [ ] Add command-line arguments for different modes
- [ ] Support both continuous and single-interaction modes

#### Task 2.2: Config & Preset Profiles
- [ ] Document speaking_rate/WPM mapping in config
- [ ] Add preset profiles: quiet room / noisy / accuracy-first
- [ ] Create environment-specific optimizations

### **🎯 Priority 3: Production Packaging** - ⏸️ NOT STARTED
**Goal**: Prepare for real-world deployment

#### Task 3.1: macOS Integration
- [ ] Create `docs/MACOS_SETUP.md` with permissions setup
- [ ] Document Terminal accessibility permissions
- [ ] Add troubleshooting section for audio permissions

#### Task 3.2: Deployment Preparation  
- [ ] Outline menu-bar app/daemon architecture
- [ ] Process model for background operation
- [ ] Graceful start/stop mechanisms

---

## 🏆 COMPLETED PRIORITIES

### **✅ Priority 1: Wake Word Detection** - COMPLETE
- [x] Continuous listening mode working
- [x] Wake word variations implemented ("hey penny", "penny", "ok penny")
- [x] Timeout behavior functional
- [x] Command extraction working properly

### **✅ Priority 2: Conversation Memory** - COMPLETE
- [x] Memory manager operational (14 conversations stored)
- [x] Context integration with LLM working
- [x] User preference learning active (5 preferences)
- [x] Memory persistence and retrieval

### **✅ Priority 3: Response Optimization** - COMPLETE
- [x] Voice-optimized responses implemented
- [x] Natural conversation flow achieved  
- [x] Speech rate properly configured (150 WPM)
- [x] Personality integration working

### **✅ Priority 4: Health Monitoring** - COMPLETE
- [x] Health monitor integration fixed
- [x] Null object pattern for safe fallback
- [x] No more AttributeError crashes on startup
- [x] Graceful degradation when health monitor unavailable

## Testing Requirements
For each implemented feature:
1. Add unit tests in `tests/` directory
2. Ensure existing 11 tests still pass
3. Test full conversation flow end-to-end
4. Document any new dependencies in `requirements.txt`

## File Structure to Maintain
```
src/
├── core/
│   ├── wake_word.py (NEW)
│   ├── memory.py (NEW)
│   ├── prompts.py (NEW)
│   └── pipeline.py (UPDATE)
├── adapters/
│   └── llm/local_ollama_adapter.py (UPDATE)
tests/
├── test_wake_word.py (NEW)
├── test_memory.py (NEW)
docs/
└── MACOS_SETUP.md (NEW)
main.py (NEW)
```

## Success Criteria
- [ ] Can activate Penny with wake word
- [ ] Maintains conversation context
- [ ] Responses are concise (under 3 sentences)
- [ ] All tests pass
- [ ] Code committed to GitHub

## Commands for Testing
```bash
# Environment setup
source .venv/bin/activate

# Run tests
PYTHONPATH=src pytest -q tests --ignore=whisper --tb=short

# Test wake word version
PYTHONPATH=src python penny_wake_word.py

# Test unified pipeline
PYTHONPATH=src python main.py
```

## Notes for Implementation
- Keep audio device setting at 1 (MacBook Pro Microphone)
- Silence threshold is 0.005 in `stt_engine.py`
- Use subprocess.run() for any system calls
- Maintain PYTHONPATH=src pattern for imports
- Python 3.13 works but shows warnings, 3.11 is preferred
