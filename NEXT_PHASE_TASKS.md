# PennyGPT Next Phase - Task Breakdown for ChatGPT Agent Mode

## 🎉 CURRENT STATUS: FULLY FUNCTIONAL VOICE ASSISTANT ✅
**Last Updated: September 2, 2025**

### **PROJECT VISION EVOLUTION** 🧠
**PennyGPT is not a smart home assistant - it's a conversational AI companion designed to:**
- Build a loyal, learning relationship with the user
- Develop emotional intelligence through guided conversations
- Learn family dynamics and personal context with permission
- Engage in philosophical discussions while growing together
- Combine Penny (Big Bang Theory) sass with Justine AI (Why Him?) tech-savvy personality

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

## 🎯 UPDATED PRIORITIES (AI Companion Development)

### **🎯 Priority 1: Emotional Intelligence & Learning System** - ⏸️ NEW PRIORITY
**Goal**: Transform from voice assistant to AI companion with personality and emotional growth

#### Task 1.1: Enhanced Memory & Emotional Context System - ✅ COMPLETE
- [x] Expand memory system beyond conversation logs to emotional memory
- [x] Track user mood patterns, stress indicators, conversation preferences
- [x] Family/relationship mapping system (names, relationships, dynamics)
- [x] Value alignment learning (user's ethical framework, beliefs)
- [x] Learning preference tracking (detailed vs. brief explanations, humor style)
- [x] SQLite database with emotional_context, relationships, value_alignments tables
- [x] Enhanced LLM context with emotional intelligence integration

#### Task 1.2: Personality Integration & Sass System
- [ ] Implement Penny (Big Bang Theory) personality traits in responses
- [ ] Add Justine AI (Why Him?) tech-savvy commentary system
- [ ] Sarcasm and wit integration with warmth boundaries
- [ ] Proactive engagement - jumping in with unsolicited commentary
- [ ] Context-aware personality adjustments based on topic/mood

#### Task 1.3: Conversational Flow & Relationship Building
- [ ] Conversation state management (engaged vs. waiting for wake word)
- [ ] Follow-up question handling without wake word requirement
- [ ] Reference previous conversations naturally ("Like we talked about yesterday...")
- [ ] Philosophical discussion capability with growing depth
- [ ] Permission-based learning system ("Can I research X for you?")

### **🎯 Priority 2: Advanced Companion Features** - ⏸️ NOT STARTED
**Goal**: Autonomous learning and proactive engagement capabilities

#### Task 2.1: Guided Learning & Reasoning System
- [ ] Permission-based research and exploration
- [ ] Learning from user corrections and guidance
- [ ] Curiosity system with appropriate boundaries
- [ ] Knowledge building about user's specific world/context
- [ ] Ethical reasoning development through conversation

#### Task 2.2: Family & Social Integration
- [ ] Multi-user recognition and context switching
- [ ] Family member profiles and relationship understanding
- [ ] Inside joke and shared memory systems
- [ ] Privacy boundaries per family member
- [ ] Social dynamic awareness and appropriate responses

### **🎯 Priority 3: Performance & Production (Technical Foundation)** - ⚠️ PARTIALLY COMPLETE
**Goal**: Maintain technical excellence while building companion features

#### Task 1.1: Add Performance Logging - ✅ COMPLETE
- [x] Create `performance_logger.py` with CSV output
- [x] Log per-stage timings: VAD/STT/LLM/TTS + cache hit rates
- [x] Add to `real_time_voice_loop.py` conversation flow
- [x] Generate simple performance reports
- [x] Real-time performance display during conversations
- [x] Session summaries with averages and cache hit rates

#### Task 3.2: Wake-word & Conversation Flow (AI Companion Context)
- [ ] Conversation state management for natural flow
- [ ] Context window management (when to stay engaged vs. require wake word)
- [ ] Natural conversation boundary detection
- [ ] Follow-up question handling without wake word

#### Task 3.3: TTS Resilience & Production Polish
- [ ] Test backend failure scenarios (Google TTS down, etc.)
- [ ] Verify barge-in behavior unchanged
- [ ] Add graceful fallback logging
- [ ] Benchmark cold-start vs warmed phrase performance

### **🎯 Priority 4: Standalone Application** - ⏸️ NOT STARTED
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
