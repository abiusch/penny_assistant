# PennyGPT Next Phase - Task Breakdown for ChatGPT Agent Mode

## Project Context
Voice assistant with working pipeline: Audio → Whisper → Ollama → gTTS → Speaker
Repository: https://github.com/abiusch/penny_assistant
Working script: `penny_with_tts.py` (run with `PYTHONPATH=src python penny_with_tts.py`)

## Priority 1: Wake Word Detection
**Goal**: Implement "Hey Penny" or "Penny" wake word to trigger listening

### Task 1.1: Create Wake Word Detector
- [ ] Create `src/core/wake_word.py`
- [ ] Implement simple keyword detection in transcribed text
- [ ] Check for variations: "hey penny", "penny", "ok penny"
- [ ] Return boolean for wake word detected

### Task 1.2: Add Continuous Listening Mode
- [ ] Create `penny_wake_word.py` based on `penny_with_tts.py`
- [ ] Implement continuous audio monitoring loop
- [ ] Only process commands after wake word detected
- [ ] Add timeout after wake word (e.g., 5 seconds to give command)

### Task 1.3: Test Wake Word
- [ ] Create `tests/test_wake_word.py`
- [ ] Test detection of various wake word formats
- [ ] Test rejection of non-wake-word audio
- [ ] Verify timeout behavior

## Priority 2: Conversation Memory
**Goal**: Maintain context between interactions

### Task 2.1: Create Memory Manager
- [ ] Create `src/core/memory.py`
- [ ] Implement conversation history storage (in-memory for now)
- [ ] Store last N exchanges (user input + assistant response)
- [ ] Add method to format history for LLM context

### Task 2.2: Integrate Memory with LLM
- [ ] Modify `src/adapters/llm/local_ollama_adapter.py`
- [ ] Include conversation history in prompts
- [ ] Add system prompt for context awareness
- [ ] Test context retention across multiple interactions

### Task 2.3: Add Memory Persistence (Optional)
- [ ] Save conversation history to JSON file
- [ ] Load previous session on startup
- [ ] Add command to clear memory ("forget everything")

## Priority 3: Response Optimization
**Goal**: Make responses appropriate for voice interaction

### Task 3.1: Add System Prompts
- [ ] Create `src/core/prompts.py`
- [ ] Define voice-optimized system prompt (keep responses under 2 sentences)
- [ ] Add personality traits from `penny_config.json`
- [ ] Include current date/time context

### Task 3.2: Implement Prompt Templates
- [ ] Modify LLM adapters to use system prompts
- [ ] Add prompt template for different modes (casual, informative, joke)
- [ ] Test response length and appropriateness

## Priority 4: Pipeline Unification
**Goal**: Use the existing `PipelineLoop` class instead of separate scripts

### Task 4.1: Fix PipelineLoop Integration
- [ ] Update `src/core/pipeline.py` to use correct device settings
- [ ] Ensure TTS is properly connected in pipeline
- [ ] Add wake word support to pipeline states

### Task 4.2: Create Unified Entry Point
- [ ] Create `main.py` that uses PipelineLoop
- [ ] Add command-line arguments for different modes
- [ ] Support both continuous and single-interaction modes

## Priority 5: Keyboard Shortcuts (macOS)
**Goal**: Enable spacebar triggering without Enter key

### Task 5.1: Document macOS Setup
- [ ] Create `docs/MACOS_SETUP.md`
- [ ] Document Terminal accessibility permissions
- [ ] Include screenshots of System Settings steps
- [ ] Add troubleshooting section

### Task 5.2: Implement Keyboard Handler
- [ ] Update `penny.py` with proper keyboard monitoring
- [ ] Add fallback for when permissions denied
- [ ] Test with both spacebar and Enter key options

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
