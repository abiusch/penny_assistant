# Changelog

All notable changes to Penny Assistant are documented here.

## [Unreleased] - Week 6.9 (Personality Polish)

### In Progress
- UI Week 6 indicators (Joy %, Memories, Context turns)
- Waveform visualization for Penny's avatar
- Voice input button functionality  
- Semantic memory persistence across server restarts

---

## [0.7.0] - 2025-12-08 - Week 6 Complete

### Added
- **Context Manager**: Rolling 10-turn conversation window with metadata tracking
- **Emotion Detector**: Keyword-based emotion detection (6 emotions: joy, sadness, anger, fear, surprise, neutral)
- **Semantic Memory**: Vector-based similarity search using sentence-transformers + FAISS
  - all-MiniLM-L6-v2 model (384-dimensional embeddings)
  - Top-k similarity search for relevant past conversations
  - Automatic conversation indexing
- **Justine-Style Personality**: Baked into core system prompt
  - Casual, enthusiastic language
  - Celebrates wins with real energy ("Hell yeah!", "YESS!")
  - Bold and confident without corporate hedging
  - Calls out impatience directly
  - Proactive with unsolicited advice

### Fixed
- **HuggingFace Cache Permissions**: Set HF_HOME to local project cache before imports
- **Research Classification False Positives**: Added conversational expression filtering
- **Em Dash Grammar Issues**: Updated emoji filter to preserve em/en dashes
- **Word Smashing**: Prevented token concatenation from missing punctuation

### Changed
- Week 6 systems integrated as **baseline features** (outside A/B test)
- Triple save architecture: Base Memory → Context Manager → Semantic Memory
- Enhanced metadata with emotion, sentiment, and context tracking
- Prompt building now includes conversation context and semantic results

### Performance
- Total Week 6 overhead: ~100-150ms per request
- Emotion detection: <1ms
- Context retrieval: <5ms
- Semantic search: 50-100ms

### Testing
- Added `diagnostics_week6.py` - 15/18 tests passing
- Unit tests for Context Manager, Emotion Detector, Semantic Memory
- Integration tests for full pipeline

---

## [0.6.5] - 2025-11-30 - UI Redesign

### Changed
- Redesigned web interface to light, modern, gender-neutral theme
- Replaced dark purple gradient with light gray/white
- Replaced heart icons with lightning bolt
- Updated color palette to indigo/blue accents
- Maintained React + Tailwind architecture

### Added
- Quick action cards (placeholder functionality)
- Personality metrics display
- Debug panel toggle
- Responsive design improvements

---

## [0.6.0] - 2025-11-20 - Phase 3B Week 3

### Added
- **Tool Calling Infrastructure**
  - Tool orchestrator with max 3 iterations
  - Tool registry with safety wrappers
  - Three safe tools: web.search, math.calc, code.execute
- Tool manifest in LLM prompts
- Tool usage analytics

---

## [0.5.5] - 2025-11-15 - Phase 3A Week 2

### Added
- **Milestone & Achievement System**
  - Personality milestones tracking
  - Achievement notifications
  - Progress metrics

### Changed
- A/B testing framework initialization
- Metrics recording for experiments

---

## [0.5.0] - 2025-11-10 - Phase 2 Complete

### Added
- **Dynamic Personality Adaptation**
  - Personality prompt builder
  - Response post-processor
  - Active personality learning from conversations
- **Personality Tracker**
  - Communication formality tracking
  - Technical depth preference
  - Humor style preference
  - Response length preference
- A/B testing framework (control vs treatment groups)

### Changed
- Split personality enhancements into experimental group
- Baseline personality for control group
- Incremental confidence updates for dimensions

---

## [0.4.0] - 2025-11-01 - Research-First Pipeline

### Added
- **ResearchFirstPipeline**: Production pipeline ensuring factual queries trigger research
- **Research Manager**: Autonomous web research via Brave Search API
- Research classification heuristics
- Financial topic detection with disclaimers

### Changed
- Replaced EdgeModalInterface with ResearchFirstPipeline as production system
- Integrated enhanced memory and personality systems
- Added research context to prompts

### Fixed
- Research triggering logic
- Hallucination prevention for factual queries

---

## [0.3.0] - 2025-10-20 - Enhanced Memory

### Added
- **Enhanced Memory System**
  - Emotional tagging of conversations
  - Sentiment analysis
  - Context-aware retrieval
- **Personality Integration**
  - Adaptive communication styles
  - User preference tracking
- SQLite-based memory persistence

---

## [0.2.0] - 2025-10-10 - Base Memory & Personality

### Added
- **MemoryManager**: Core conversation storage
- **Personality System**:
  - Dry, sarcastic baseline personality
  - Output sanitization filters
  - Forbidden phrase removal
  - Emoji policy enforcement
- Configuration via `personality/config.json`

---

## [0.1.0] - 2025-10-01 - Initial Release

### Added
- Basic LLM integration (OpenAI-compatible API)
- Web interface (Flask + React)
- Text-based chat functionality
- Configuration system
- Health monitoring
- System diagnostics

---

## Version Numbering

- **Major (0.x.0)**: Phase completions, major architecture changes
- **Minor (0.x.X)**: New features, week completions
- **Patch (0.x.x)**: Bug fixes, minor improvements

**Current Phase**: Phase 3 - Advanced Features (Weeks 6-10)
**Current Week**: Week 6.9 - Personality Polish
**Progress**: 67% (6.5-7 of 10 weeks)

---

**Latest**: v0.7.0 - Week 6 Context & Emotion Systems Complete
