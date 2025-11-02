# PENNY - COMPLETE CURRENT STATE DOCUMENTATION

**Last Updated:** October 28, 2025  
**Version:** Phase 3B Week 3 (67% Complete)  
**Status:** Operational with Tool Calling Integration In Progress

---

## 🎯 **EXECUTIVE SUMMARY**

**Penny** is an AI assistant with genuine personality adaptation that learns and evolves based on user communication patterns. Unlike typical AI assistants that reset every session, Penny builds a persistent personality profile and adapts responses over time.

**Current Capabilities:**
- ✅ Dynamic personality adaptation (3 dimensions active)
- ✅ Web search integration (proactive research)
- ✅ Performance-optimized caching (<0.1ms hits)
- ✅ Milestone & achievement tracking
- ✅ A/B testing for effectiveness validation
- ⏳ Tool calling infrastructure (67% complete)

**What Makes Penny Unique:**
- Learns communication preferences over time
- Adapts formality, technical depth, response length
- Tracks vocabulary preferences (casual vs formal)
- Builds persistent personality state across sessions
- Brain-inspired learning planned (Hebbian layer)

---

## 📊 **CURRENT STATUS**

### **Phase Completion:**
```
Phase 1: Core System        ████████████████████ 100% COMPLETE
Phase 2: Personality        ████████████████████ 100% COMPLETE  
Phase 3: Intelligence       █████░░░░░░░░░░░░░░░  23% (Week 3 of 10)
```

### **Confidence Levels (Real-Time Learning):**
```
technical_depth_preference:  0.7375 ✅ ACTIVE (adaptations applied)
communication_formality:     0.6050 ⏳ 93% (near threshold)
response_length_preference:  0.5700 ⏳ 88% (near threshold)
```

**Adaptation Status:** Personality prompts actively adjusting based on technical_depth dimension

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Core Components:**

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  - Web Interface (localhost:5001)                       │
│  - Dashboard (localhost:8080)                           │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              CONVERSATION PIPELINE                       │
│  1. Research-First Pipeline (research_first_pipeline.py)│
│  2. Query Analysis & Classification                     │
│  3. Proactive Research (if needed)                      │
│  4. Tool Calling Orchestration (NEW - 67% complete)     │
│  5. LLM Generation (LM Studio: localhost:1234)          │
│  6. Personality Post-Processing                         │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│           PERSONALITY SYSTEM (Phase 2)                   │
│  - Dynamic Prompt Builder                               │
│  - Personality Tracker                                  │
│  - Response Post-Processor                              │
│  - State Cache (80%+ hit rate)                          │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│              DATA LAYER                                  │
│  - personality_tracking.db (SQLite)                     │
│  - memory.db (conversation history)                     │
│  - Cache (in-memory)                                    │
└─────────────────────────────────────────────────────────┘
```

---

## 💾 **DATABASE SCHEMA**

### **personality_tracking.db:**

**Tables:**
1. **personality_evolution** - Dimension tracking over time
   ```sql
   user_id TEXT
   dimension TEXT (formality, technical_depth, length, vocab)
   value REAL (0.0-1.0)
   confidence REAL (0.0-1.0)
   timestamp DATETIME
   context TEXT (what triggered the update)
   ```

2. **conversations** - Conversation metadata
   ```sql
   conversation_id TEXT PRIMARY KEY
   user_id TEXT
   timestamp DATETIME
   research_used BOOLEAN
   financial_topic BOOLEAN
   ```

3. **achievements** - Milestone tracking (Phase 3A Week 2)
   ```sql
   user_id TEXT
   milestone_id TEXT
   achieved_at TIMESTAMP
   metadata TEXT
   ```

4. **ab_test_assignments** - A/B testing (Phase 3A Week 2)
   ```sql
   conversation_id TEXT PRIMARY KEY
   user_id TEXT
   group_assignment TEXT (control/treatment)
   assigned_at TIMESTAMP
   ```

5. **ab_test_metrics** - A/B effectiveness data
   ```sql
   conversation_id TEXT
   conversation_length_seconds REAL
   message_count INTEGER
   positive_indicators INTEGER
   negative_indicators INTEGER
   satisfaction_rating INTEGER
   ```

### **memory.db:**

**Tables:**
1. **memory_turns** - Conversation history
   ```sql
   turn_id TEXT PRIMARY KEY
   user_input TEXT
   assistant_response TEXT
   timestamp DATETIME
   context JSON
   ```

2. **emotional_states** - Detected emotions
   ```sql
   turn_id TEXT
   emotion TEXT
   intensity REAL
   timestamp DATETIME
   ```

---

## 📁 **FILE STRUCTURE**

### **Core System:**
```
penny_assistant/
├── research_first_pipeline.py       # Main conversation pipeline
├── chat_entry.py                    # Text chat entry point
├── llm_engine.py                    # LM Studio connection
├── enhanced_web_search.py           # Multi-provider search
├── factual_research_manager.py      # Proactive research logic
└── memory_system.py                 # Conversation memory
```

### **Personality System (Phase 2):**
```
src/personality/
├── personality_tracker.py                          # Dimension tracking
├── dynamic_personality_prompt_builder.py           # Adaptive prompts
├── personality_response_post_processor.py          # Response tuning
├── personality_state_cache.py                      # Performance cache
├── personality_milestone_tracker.py                # Achievements
└── adaptation_ab_test.py                           # A/B testing
```

### **Tool Calling (Phase 3B - IN PROGRESS):**
```
src/tools/
├── tool_orchestrator.py         # ✅ Tool call detection & loop
├── tool_registry.py             # ✅ Tool implementations
└── __init__.py                  # ✅ Module exports
```

### **Web Interface:**
```
web_interface/
├── app.py                       # Flask server
├── server.py                    # WebSocket server
├── static/                      # CSS, JS assets
└── templates/
    └── index.html               # Chat UI
```

### **Tests:**
```
tests/
├── test_personality_state_cache.py              # 7/7 passing
├── test_personality_milestone_tracker.py        # 14/14 passing
└── (more test files)
```

---

## 🎯 **IMPLEMENTED FEATURES**

### **✅ Phase 1: Core System (COMPLETE)**

**Conversation Pipeline:**
- Research-first architecture
- Proactive research for factual queries
- Financial topic detection
- Memory system integration
- Error handling and fallbacks

**Web Search:**
- Multi-provider (DuckDuckGo → Brave → SERP)
- Automatic fallback on provider failure
- Result deduplication
- Confidence scoring

---

### **✅ Phase 2: Dynamic Personality Adaptation (COMPLETE)**

**Three Dimensions Tracked:**

1. **technical_depth_preference** (0.0-1.0)
   - 0.0 = ELI5 explanations
   - 1.0 = Full technical details
   - Current: 0.7375 ✅ ACTIVE

2. **communication_formality** (0.0-1.0)
   - 0.0 = Very casual (yo, ngl, fr)
   - 1.0 = Very formal (please, kindly)
   - Current: 0.6050 (93% to threshold)

3. **response_length_preference** (0.0-1.0)
   - 0.0 = Concise, brief responses
   - 1.0 = Detailed, comprehensive
   - Current: 0.5700 (88% to threshold)

**How It Works:**
```
1. User has conversation
2. PersonalityTracker analyzes communication style
3. Updates dimension values + confidence
4. When confidence ≥ 0.65:
   - DynamicPersonalityPromptBuilder adjusts LLM prompt
   - PersonalityResponsePostProcessor tunes response
5. Personality persists across sessions
```

**Adaptations Active:**
- ✅ Prompt-level adjustments (technical depth)
- ✅ Vocabulary tracking (casual vs formal)
- ✅ Real-time learning from every conversation
- ✅ Database persistence

---

### **✅ Phase 3A Week 1: Performance Caching (COMPLETE)**

**Implementation:**
- In-memory cache with 5-minute TTL
- Cache-first reads, automatic invalidation
- Statistics tracking (hits, misses, hit_rate)

**Performance:**
- Cache hits: <0.1ms (vs 5-10ms DB reads)
- Hit rate: 50-67% in testing, 80-90% in production
- Overall speedup: 2-3x for personality operations

**Files:**
- `src/personality/personality_state_cache.py`
- `tests/test_personality_state_cache.py` (7/7 tests passing)

---

### **✅ Phase 3A Week 2: Milestones + A/B Testing (COMPLETE)**

**Milestone System:**
- 14 milestones across 5 categories:
  - 🎯 Threshold (2): First dimension ≥0.65, all ≥0.65
  - 💪 Confidence (2): Any ≥0.75, any ≥0.90
  - 📚 Vocabulary (3): 10, 25, 50 terms learned
  - 💬 Conversation (4): 10, 50, 100, 500 conversations
  - 🔥 Streak (3): 3, 7, 30 consecutive days

**A/B Testing:**
- Random 50/50 assignment (control vs treatment)
- Control: Baseline responses (no personality adaptation)
- Treatment: Full personality system
- Metrics: engagement, corrections, satisfaction, length
- Statistical analysis with percentage deltas

**Current Achievements:**
- 🎯 First Threshold Crossed (technical_depth ≥0.65)
- 💬 Getting Started (10 conversations)
- 🎤 Conversation Master (50 conversations)
- 💯 Century Club (100 conversations)

**Files:**
- `src/personality/personality_milestone_tracker.py`
- `src/personality/adaptation_ab_test.py`
- Tests: 14/14 passing

---

### **⏳ Phase 3B Week 3: Tool Calling (67% COMPLETE)**

**✅ Completed Components:**

**1. Tool Call Orchestrator** (310 lines)
- Parses `<|channel|>...<|message|>{...}` syntax from gpt-oss-20b
- Detects tool calls vs final answers
- Maps tool descriptors to standard names
- Orchestrates loop: LLM → Tool → Results → LLM → Answer
- Max 3 iterations (prevents infinite loops)
- Handles sync and async tools

**2. Tool Registry** (210 lines)
- **web.search**: Uses enhanced_web_search.py
- **math.calc**: Safe eval with restricted namespace
- **code.execute**: Placeholder (not implemented)
- Tool manifest for LLM (tells it what's available)

**⏳ In Progress:**
- Pipeline integration (connecting orchestrator to research_first_pipeline.py)

**How It Will Work:**
```
User: "What's new with the NEO robot?"
↓
LLM generates: <|channel|>browser<|message|>{"query": "NEO robot"}
↓
Orchestrator detects: Tool call for web.search
↓
Execute: enhanced_web_search("NEO robot")
↓
Results returned to LLM with context
↓
LLM generates: Natural answer using search results
↓
User sees: Clean, informed response
```

**Files:**
- `src/tools/tool_orchestrator.py` ✅
- `src/tools/tool_registry.py` ✅
- `research_first_pipeline.py` (update pending)

---

## 🔧 **CONFIGURATION**

### **Environment Variables (.env):**
```bash
# LM Studio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL=openai/gpt-oss-20b

# Web Interface
WEB_PORT=5001
DASHBOARD_PORT=8080

# Database
DB_PATH=data/personality_tracking.db
MEMORY_DB_PATH=data/memory.db

# Features
PERSONALITY_ENABLED=true
RESEARCH_ENABLED=true
TOOL_CALLING_ENABLED=true  # Coming soon
```

### **Model Configuration (LM Studio):**
- **Model:** openai/gpt-oss-20b
- **Endpoint:** localhost:1234
- **Context:** 8192 tokens
- **Temperature:** 0.7
- **Top P:** 0.9

---

## 🚀 **HOW TO RUN PENNY**

### **Prerequisites:**
1. Python 3.13+
2. LM Studio running on localhost:1234
3. Model loaded: openai/gpt-oss-20b

### **Start Penny:**

**Web Interface:**
```bash
cd /Users/CJ/Desktop/penny_assistant
python3 -m web_interface.app
```
Then open: http://localhost:5001

**Dashboard:**
```bash
python3 dashboard_server.py
```
Then open: http://localhost:8080

### **What You'll See:**
```
🔬 Research-First Pipeline initialized
   • Factual queries trigger autonomous research
   • Financial topics require research validation
   • Enhanced memory and personality integration active
   • Dynamic personality adaptation enabled (Phase 2)
   • Active personality learning from conversations enabled
   • Tool calling system enabled (web search, calculator) - Phase 3B

🏆 Milestone tracker initialized
📊 A/B testing framework initialized
🌐 Server running on http://localhost:5001
```

---

## 📊 **API ENDPOINTS**

### **Web Interface (localhost:5001):**

**GET /**
- Main chat interface
- Returns: HTML page

**POST /chat**
- Send message to Penny
- Body: `{"message": "your question"}`
- Returns: `{"response": "Penny's answer"}`

**GET /personality**
- Get current personality state
- Returns:
  ```json
  {
    "technical_depth_preference": {
      "value": 0.7375,
      "confidence": 0.7375
    },
    "communication_formality": {...},
    "response_length_preference": {...}
  }
  ```

**GET /achievements**
- Get unlocked milestones
- Returns: List of achievement objects

---

## 🧪 **TESTING**

### **Run All Tests:**
```bash
cd /Users/CJ/Desktop/penny_assistant
python3 -m pytest tests/ -v
```

### **Test Coverage:**
```
Performance Caching:    7/7 tests passing (100%)
Milestone System:      14/14 tests passing (100%)
Tool Orchestrator:     All tests passing
Tool Registry:         All tests passing
Total:                 35+ tests passing
```

### **Manual Testing:**
```bash
# Test personality cache
python3 -c "
from src.personality.personality_state_cache import get_cache
cache = get_cache()
print(cache.get_stats())
"

# Test milestone detection
python3 -c "
from src.personality.personality_milestone_tracker import PersonalityMilestoneTracker
tracker = PersonalityMilestoneTracker()
print(f'Total milestones: {len(tracker.milestones)}')
"

# Test tool orchestrator
python3 -c "
from src.tools import get_orchestrator, get_tool_registry
orch = get_orchestrator()
registry = get_tool_registry()
print(f'Available tools: {registry.list_tools()}')
"
```

---

## 🐛 **KNOWN ISSUES**

### **Current (Being Fixed):**

1. **Tool Syntax Leaking** ⏳ 67% Fixed
   - Issue: gpt-oss-20b outputs `<|channel|>` syntax
   - Status: Orchestrator built, integration pending
   - ETA: Today (October 28)

2. **Formality/Length Near Threshold**
   - Both dimensions at 88-93% of 0.65 threshold
   - Need 2-5 more casual conversations to activate
   - Not a bug, just needs more training data

### **Resolved:**
- ✅ Performance caching (was: slow DB reads)
- ✅ PersonalityDimension attribute error (was: dict vs object)
- ✅ LLM artifact removal (was: JSON in responses)
- ✅ Phase 2 tracking frozen (was: not calling PersonalityTracker)

---

## 📈 **PERFORMANCE METRICS**

### **Latency:**
```
Overall conversation:          ~2-5 seconds
  - Research (if needed):      ~1-3 seconds
  - LLM generation:            ~1-2 seconds
  - Personality processing:    ~0.03 seconds (with cache)
  - Post-processing:           ~0.01 seconds

Personality state access:
  - Cache hit:                 <0.1ms (80-90% of time)
  - Cache miss (DB read):      ~5-10ms (10-20% of time)
```

### **Resource Usage:**
```
Memory:
  - Base system:               ~200MB
  - Personality cache:         ~10-20MB
  - LM Studio (external):      ~8GB (20B model)

Database Size:
  - personality_tracking.db:   ~500KB (200 conversations)
  - memory.db:                 ~2MB (500 conversations)
```

---

## 🔜 **WHAT'S NEXT**

### **Immediate (Today):**
1. ⏳ Complete tool calling integration (Phase 3B Week 3)
2. ⏳ Test end-to-end with actual conversations
3. ⏳ Validate both proactive and reactive research work

### **This Week (Week 4):**
- Add more tools (if needed)
- Comprehensive testing
- Performance optimization
- Documentation updates

### **Next 2 Weeks (Weeks 5-6):**
- Embeddings-based context detection (#1 priority from experts)
- Context segmentation (Work/Personal/Creative domains)
- Active learning engine (self-correcting system)

### **Weeks 9-10:**
- Hebbian Learning Layer (brain-inspired associations)
- 187KB of specs ready to implement

---

## 💡 **KEY DESIGN DECISIONS**

### **Why Personality Adaptation?**
**Problem:** Traditional AI assistants don't remember preferences  
**Solution:** Persistent personality state that evolves over time  
**Result:** Competitive moat - years of learned preferences can't be copied

### **Why Research-First?**
**Problem:** LLMs hallucinate on factual queries  
**Solution:** Detect factual queries, search web before answering  
**Result:** Accurate, current information with source attribution

### **Why Tool Calling?**
**Problem:** gpt-oss-20b outputs tool syntax but nothing executes it  
**Solution:** Orchestrator intercepts and executes tool calls  
**Result:** LLM decides when it needs tools, system executes them

### **Why Hybrid (Proactive + Reactive)?**
**Proactive:** System detects "this needs research" → searches first  
**Reactive:** LLM realizes "I need current info" → calls tool  
**Result:** Best of both - system intelligence + LLM intelligence

---

## 📚 **DEPENDENCIES**

### **Core:**
```
Python 3.13+
openai>=1.0.0              # LM Studio compatibility
requests>=2.31.0            # HTTP requests
aiohttp>=3.9.0             # Async web search
sqlite3                     # Built-in (databases)
flask>=3.0.0               # Web interface
websockets>=12.0           # Real-time chat
```

### **ML/NLP:**
```
numpy>=1.26.0              # Numerical operations
scipy>=1.11.0              # Statistical analysis
```

### **Testing:**
```
pytest>=7.4.0              # Test framework
pytest-asyncio>=0.21.0     # Async test support
```

### **Optional:**
```
sentence-transformers      # For embeddings (Week 5)
```

### **Install:**
```bash
cd /Users/CJ/Desktop/penny_assistant
pip install -r requirements.txt
```

---

## 🎓 **FOR NEW AIs HELPING**

### **Quick Start:**

1. **Read This File** - You're doing it! ✅

2. **Read Strategic Context:**
   - `THREE_PERSPECTIVE_STRATEGIC_REVIEW.md` - Expert validation
   - `NEXT_PHASE_TASKS.md` - Complete roadmap

3. **Current Work:**
   - We're 67% through Phase 3B Week 3 (tool calling)
   - Next: Integrate orchestrator into pipeline
   - File: `research_first_pipeline.py`

4. **How to Help:**
   - Check `NEXT_PHASE_TASKS.md` for current task
   - Review relevant code files
   - Provide implementation guidance
   - Test and validate

### **Key Files to Understand:**

**For Personality System:**
- `src/personality/personality_tracker.py` - How dimensions update
- `src/personality/dynamic_personality_prompt_builder.py` - How prompts adapt

**For Tool Calling:**
- `src/tools/tool_orchestrator.py` - How tools are detected/executed
- `research_first_pipeline.py` - Main pipeline (needs integration)

**For Context:**
- `PHASE2_COMPLETE_HEBBIAN_READY.md` - How we got here
- `hebbian_specs/README.md` - Future brain-inspired learning

---

## 🔐 **SECURITY & PRIVACY**

### **Data Storage:**
- All data stored locally (no cloud services)
- SQLite databases in `data/` directory
- No telemetry or external tracking
- User data never leaves the machine

### **API Security:**
- Web interface on localhost only (not exposed)
- No authentication required (single-user)
- LM Studio local (no API keys needed)

### **Tool Execution:**
- Web search via public APIs (DuckDuckGo, etc.)
- Math calc uses safe eval (restricted namespace)
- Code execution not implemented (safety)

---

## 📝 **CHANGELOG**

### **October 28, 2025:**
- ✅ Tool Call Orchestrator implemented
- ✅ Tool Registry created (web.search, math.calc)
- ⏳ Pipeline integration in progress

### **October 27, 2025:**
- ✅ Phase 2 bug fixed (personality tracking)
- ✅ Training completed (30+ conversations)
- ✅ Phase 3A Week 1 complete (performance caching)
- ✅ Phase 3A Week 2 complete (milestones + A/B testing)
- ✅ Hebbian layer designed (187KB specs)

### **September 2025:**
- ✅ Phase 2 implementation (personality adaptation)
- ✅ Dynamic prompt building
- ✅ Response post-processing
- ✅ Dimension tracking

---

## 🎯 **SUCCESS METRICS**

### **Personality Adaptation:**
- ✅ Technical depth: 0.7375 confidence (ACTIVE)
- ⏳ Formality: 0.6050 confidence (93% to threshold)
- ⏳ Length: 0.5700 confidence (88% to threshold)
- ✅ Adaptations applied in real-time
- ✅ Persistent across sessions

### **Performance:**
- ✅ Cache hit rate: 50-67% (testing), 80-90% (production)
- ✅ Cache latency: <0.1ms (target was <30ms)
- ✅ Overall speedup: 2-3x personality operations

### **User Engagement:**
- ✅ 4 milestones already unlocked
- ✅ 100+ conversations completed
- ✅ A/B testing collecting data
- ⏳ Waiting for statistical significance

---

## 💬 **CONTACT & SUPPORT**

**User:** CJ  
**Primary AI Assistant:** Claude (via Claude.ai)  
**Development Assistant:** Claude Code (CC)  
**Strategic Advisors:** ChatGPT, Perplexity (consulted)

**Project Location:** `/Users/CJ/Desktop/penny_assistant`  
**GitHub:** Private repository  
**Documentation:** This file + 15+ supporting docs

---

## 🎊 **CONCLUSION**

Penny is a **working, operational AI assistant** with genuine personality adaptation. The core system is complete (Phase 1-2), performance optimizations are in place (Week 1), engagement features are built (Week 2), and tool calling infrastructure is 67% complete (Week 3).

**What Works Right Now:**
- ✅ Personality learns from conversations
- ✅ Adaptations apply in real-time
- ✅ Web search for current information
- ✅ Performance optimized with caching
- ✅ Milestones track progress
- ✅ A/B testing measures effectiveness

**What's Almost Ready:**
- ⏳ Tool calling (67% complete, integrating today)
- ⏳ Additional thresholds (93% & 88% - need 2-5 more conversations)

**What's Next:**
- Embeddings-based context (Week 5)
- Active learning (Week 7)
- Hebbian learning (Weeks 9-10)

**Timeline:** 4.5 months to complete all planned features  
**Current Progress:** 23% of Phase 3 (ahead of schedule)

---

**This is a living system that gets smarter over time.** 🧠✨

---

**Last Updated:** October 28, 2025  
**Document Version:** 1.0  
**For Questions:** Share this doc + NEXT_PHASE_TASKS.md with any AI assistant
