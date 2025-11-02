# NEXT_PHASE_TASKS - EDGE AI HYBRID ROADMAP

**Last Updated:** October 28, 2025 - EDGE AI STRATEGIC PIVOT  
**Major Decision:** Edge-First Hybrid Architecture  
**Audit:** Claude + ChatGPT + Perplexity (88% consensus)  
**Edge AI Analysis:** ChatGPT Edge AI Blueprint

---

## 🧠 **STRATEGIC PIVOT: EDGE AI INTEGRATION**

### **Why Edge AI Changes Everything:**

**Solves Critical Audit Issues:**
- ✅ Voice latency (3-5s → <1s) - **Week 8 becomes validation, not implementation**
- ✅ Modal fragmentation - **Unified edge pipeline for chat AND voice**
- ✅ Privacy concerns - **90% runs on-device**
- ✅ API costs - **70-90% reduction**
- ✅ Agentic scalability - **Local = cheap proactive behaviors**

**Enhances Competitive Moat:**
- ✨ Personality responds instantly (<500ms) - feels ALIVE
- ✨ Truly offline-capable
- ✨ Privacy-first by architecture
- ✨ Scales without cost explosion

**Your Hardware:** M4 Pro 48GB RAM = Perfect for this

---

## 📊 **EDGE AI COMPONENT DISTRIBUTION**

| Component | Location | Technology | Latency |
|-----------|----------|------------|---------|
| Wake Word | **Edge** | pvporcupine | <50ms |
| STT | **Edge** | Whisper.cpp large-v3 | ~200ms |
| Personality | **Edge** | Local JSON + VectorDB | <10ms |
| TTS | **Edge** | Coqui XTTS + personality prosody | ~300ms |
| LLM Fast | **Edge** | Ollama LLaMA 3.1 8B | ~400ms |
| LLM Smart | **Edge** | Ollama LLaMA 3.1 70B-Q4 | ~1.5s |
| LLM Complex | **Cloud** | GPT-5 / Claude 3.5 | ~3s |
| Research | **Cloud** | Tool Orchestrator | ~1-2s |
| Memory | **Edge** | SQLite + JSON | <5ms |

**Result:**
- **Edge-only:** 500-800ms total (vs current 3-5s)
- **Hybrid:** 2-3s with research (vs current 5-8s)
- **Expected distribution:** 80% edge, 20% cloud

---

## 📋 **EDGE AI REVISED ROADMAP**

```
BEFORE EDGE:                 WITH EDGE AI:
├── Week 3: Tool Calling     ├── Week 3: Tool Calling ⏳
├── Week 4: Critical Fixes   ├── Week 4: Critical Fixes + Edge Setup 🚨
│                            │   └── +Ollama +Whisper.cpp +benchmarks
├── Week 4.5: Arch           ├── Week 4.5: Edge Infrastructure 🔴
│                            │   └── Model mgr, hybrid routing, local TTS
├── Week 5: Embeddings       ├── Week 5: Edge Embeddings ⭐
│                            │   └── sentence-transformers LOCAL
├── Week 6: Context          ├── Week 6: Edge Context + Emotion
├── Week 7: Agentic          ├── Week 7: Edge Agentic Pipeline 🎯
│                            │   └── Local fast, cloud deep
├── Week 8: Voice Optimize   ├── Week 8: Edge Voice Polish ✅
│                            │   └── DONE via edge, just validate
└── Week 9-10: Hebbian       └── Week 9-10: Hebbian 🧠
```

**Time Impact:** +10-14 hours total (Week 4 +2hrs, Week 4.5 +8-12hrs)  
**Timeline:** Still 5-6 months  
**Value:** MASSIVE improvement in latency, privacy, cost

---

## 🚨 **WEEK 4: CRITICAL FIXES + EDGE SETUP** (17-25 hours)

### **ORIGINAL FIXES (15-21 hours):**

**FIX 1: Unify Chat/Voice via Edge Interface** (6-8 hours) 🚨🚨🚨

```python
# NEW: src/core/edge_modal_interface.py

class EdgeModalInterface(ABC):
    """Unified edge-first base for all modalities"""
    
    def __init__(self):
        # SHARED personality
        self.personality = PersonalityTracker()
        self.milestone_tracker = PersonalityMilestoneTracker()
        self.ab_tester = AdaptationABTest()
        
        # Edge AI stack
        self.edge_llm_fast = None  # LLaMA 8B
        self.edge_llm_smart = None  # LLaMA 70B
        self.hybrid_router = HybridLLMRouter()
        self.edge_stt = None  # Whisper.cpp
        self.edge_tts = None  # Coqui XTTS
    
    def setup_edge_models(self):
        """Initialize edge stack"""
        self.edge_llm_fast = load_ollama("llama3.1:8b")
        self.edge_llm_smart = load_ollama("llama3.1:70b-q4")
        self.edge_stt = load_whisper("large-v3")
        self.edge_tts = load_coqui_xtts()

class VoiceInterface(EdgeModalInterface):
    def process_input(self, audio: bytes) -> bytes:
        # Edge STT
        text = self.edge_stt.transcribe(audio)  # ~200ms
        
        # Shared personality
        adapted_prompt = self._apply_personality(text)
        
        # Route: edge 80%, cloud 20%
        response_text = self._route_to_llm(adapted_prompt)
        
        # Edge TTS with personality prosody
        personality_state = self.personality.get_personality_state()
        prosody = self._map_personality_to_voice(personality_state)
        response_audio = self.edge_tts.synthesize(response_text, **prosody)
        
        # Update personality
        self._update_personality(text, response_text)
        
        return response_audio  # Total: ~500-800ms!
```

**Files:**
- NEW: `src/core/edge_modal_interface.py` (~300 lines)
- NEW: `src/edge/model_loader.py` (~150 lines)
- NEW: `src/edge/hybrid_router.py` (~250 lines)
- UPDATE: `voice_entry.py`, `research_first_pipeline.py`
- NEW: `tests/integration/test_edge_modal.py` (~200 lines)

**Success:** Both modalities <1s response time, shared personality

---

**FIX 2: Integration Tests + Edge Tests** (4-6 hours) 🚨

*Add edge-specific tests:*

```python
def test_edge_voice_latency():
    """Voice <1s for simple queries"""
    voice = VoiceInterface()
    voice.setup_edge_models()
    
    audio = load_test_audio("hey_penny.wav")
    start = time.time()
    response = voice.process_input(audio)
    latency = time.time() - start
    
    assert latency < 1.0, f"Latency {latency}s > 1s target"

def test_hybrid_routing_distribution():
    """Verify 80% edge, 20% cloud"""
    router = HybridLLMRouter()
    
    test_queries = load_test_queries(100)
    routes = [router.route(q) for q in test_queries]
    
    edge_count = sum(1 for r in routes if r.target.startswith("edge"))
    assert 75 <= edge_count <= 85, "Should be ~80% edge"
```

**Target:** 20+ tests (15 original + 5 edge-specific)

---

**FIX 3: Concurrent Access** (3-4 hours) 🚨  
**FIX 4: Tool Safety** (2-3 hours) 🔴

*No changes - same as audit plan*

---

### **NEW: EDGE AI FOUNDATION** (2-4 hours) 🧠

**Install edge stack:**

```bash
# 1. Install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b      # ~5GB
ollama pull llama3.1:70b-q4  # ~40GB

# 2. Build Whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp && make
bash ./models/download-ggml-model.sh large-v3

# 3. Install Coqui TTS
pip install TTS

# 4. Benchmark
python scripts/benchmark_edge_models.py
```

**Expected benchmarks:**
- LLaMA 8B: ~400ms
- LLaMA 70B: ~1.5s
- Whisper: ~200ms
- TTS: ~300ms

**Files:**
- NEW: `scripts/install_edge_stack.sh`
- NEW: `scripts/benchmark_edge_models.py`
- NEW: `docs/EDGE_AI_SETUP.md`

---

## 🔴 **WEEK 4.5: EDGE INFRASTRUCTURE** (22-30 hours)

### **INFRASTRUCTURE 1: Model Manager** (5-6 hours) 🔴

```python
# NEW: src/edge/model_manager.py

class EdgeModelManager:
    """Manage edge models - updates, optimization"""
    
    def check_updates(self) -> Dict[str, str]:
        """Check for new models"""
        available = fetch_model_registry()
        updates = {}
        for model, remote_ver in available.items():
            local_ver = get_local_version(model)
            if remote_ver > local_ver:
                updates[model] = remote_ver
        return updates
    
    def suggest_upgrade(self):
        """Penny suggests upgrades conversationally"""
        updates = self.check_updates()
        if updates:
            return f"Yo CJ, found {len(updates)} model upgrades. Want 'em?"
```

**Features:**
- Auto-check updates
- Download & quantize
- Optimize for M4 Pro
- Conversational upgrade prompts

---

### **INFRASTRUCTURE 2: Hybrid Router** (6-8 hours) 🔴

```python
# NEW: src/edge/hybrid_router.py

class HybridLLMRouter:
    """Route queries: edge fast, edge smart, or cloud"""
    
    def route(self, prompt: str, ctx: ConversationContext) -> RoutingDecision:
        complexity = self.analyze_complexity(prompt, ctx)
        
        if complexity < 0.3:  # Greetings, simple
            return RoutingDecision(
                target="edge_fast",  # LLaMA 8B
                estimated_latency_ms=400
            )
        elif complexity < 0.7:  # Moderate
            return RoutingDecision(
                target="edge_smart",  # LLaMA 70B
                estimated_latency_ms=1500
            )
        else:  # Complex coding, research
            return RoutingDecision(
                target="cloud",  # GPT-5
                estimated_latency_ms=3000
            )
    
    def analyze_complexity(self, prompt: str, ctx) -> float:
        score = 0.0
        
        # Length
        if len(prompt.split()) > 100: score += 0.3
        elif len(prompt.split()) < 10: score -= 0.2
        
        # Keywords
        if any(w in prompt.lower() for w in ["code", "script"]): score += 0.4
        if any(w in prompt.lower() for w in ["hey", "hi"]): score -= 0.3
        
        # Context
        if ctx.requires_research: score += 0.2
        
        return max(0.0, min(1.0, score))
```

**Expected:** 60% fast edge, 20% smart edge, 20% cloud

---

### **INFRASTRUCTURE 3: Local TTS** (5-6 hours) 🔴

```python
# NEW: src/edge/local_tts.py

class LocalTTS:
    """Edge TTS with personality prosody"""
    
    def synthesize(self, text: str, personality_state: PersonalityState) -> bytes:
        # Map personality to voice params
        prosody = self._personality_to_prosody(personality_state)
        
        # Generate with Coqui XTTS
        audio = self.model.tts(text=text, **prosody)
        return audio
    
    def _personality_to_prosody(self, state) -> dict:
        prosody = {}
        
        # Technical → confident, clear
        if state['technical_depth'] > 0.7:
            prosody['emotion'] = 'confident'
            prosody['speed'] = 0.95
        
        # Casual → relaxed, faster  
        if state['formality'] < 0.4:
            prosody['emotion'] = 'casual'
            prosody['speed'] = 1.1
        
        # Sarcasm → tone shift
        if state.get('sarcasm', 0.5) > 0.6:
            prosody['emotion'] = 'sarcastic'
        
        return prosody
```

---

### **INFRASTRUCTURE 4: Edge Telemetry** (6-8 hours) ⚠️

```python
# UPDATE: src/core/telemetry.py

class EdgeMetrics:
    edge_fast_calls: int = 0
    edge_smart_calls: int = 0
    cloud_calls: int = 0
    
    edge_fast_latency_ms: List[float]
    edge_smart_latency_ms: List[float]
    cloud_latency_ms: List[float]
    
    def get_cost_savings(self) -> Dict:
        """Calculate vs cloud-only"""
        total = sum([self.edge_fast_calls, self.edge_smart_calls, self.cloud_calls])
        
        # Cloud-only cost: $0.01/call
        cloud_only = total * 0.01
        
        # Actual: edge ~$0.0001, cloud $0.01
        actual = (
            self.edge_fast_calls * 0.0001 +
            self.edge_smart_calls * 0.0003 +
            self.cloud_calls * 0.01
        )
        
        savings = cloud_only - actual
        return {
            'savings': savings,
            'savings_percent': round(savings / cloud_only * 100, 1)
        }
```

**Dashboard shows:**
- Routing distribution pie chart
- Latency comparison
- Cost savings (expect 70-90%)

---

## ⭐ **WEEK 5: EDGE EMBEDDINGS** (28-35 hours)

**Run embeddings locally:**

```python
# NEW: src/research/edge_semantic_classifier.py

from sentence_transformers import SentenceTransformer

class EdgeSemanticClassifier:
    """LOCAL semantic classification"""
    
    def __init__(self):
        # Runs on CPU efficiently (~90MB)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Training examples
        self.research_examples = [
            "What's the latest news on X?",
            "Current price of Y?",
            # ... 50+ examples
        ]
        
        # Compute once, cache
        self.research_embeddings = self.model.encode(self.research_examples)
    
    def requires_research(self, query: str) -> float:
        """Fast edge computation"""
        query_embedding = self.model.encode(query)
        similarities = cosine_similarity(query_embedding, self.research_embeddings)
        return float(similarities.max())
```

**Benefits:**
- Privacy (never sends query to cloud for classification)
- Speed (< 50ms vs API call)
- Cost (free vs paid embedding API)
- Accuracy (+15-25% from audit)

---

## 📋 **WEEK 6-10: UNCHANGED** 

**Week 6:** Context + Emotion (edge-based storage)  
**Week 7:** Edge Agentic Pipeline (local = cheap proactive behaviors)  
**Week 8:** Edge Voice Polish (DONE, just validate <1s target)  
**Week 9-10:** Hebbian (no changes)

---

## 📊 **REVISED TIMELINE WITH EDGE AI**

```
Phase 2: ████████████████████ 100% ✅

Week 3:   █████████████░░░░░░░  67% Tool Calling ⏳
Week 4:   ░░░░░░░░░░░░░░░░░░░░   0% Fixes + Edge Setup 🚨
Week 4.5: ░░░░░░░░░░░░░░░░░░░░   0% Edge Infrastructure 🔴
Week 5:   ░░░░░░░░░░░░░░░░░░░░   0% Edge Embeddings ⭐
Week 6:   ░░░░░░░░░░░░░░░░░░░░   0% Context + Emotion
Week 7:   ░░░░░░░░░░░░░░░░░░░░   0% Edge Agentic 🎯
Week 8:   ░░░░░░░░░░░░░░░░░░░░   0% Voice Polish ✅
Week 9-10:░░░░░░░░░░░░░░░░░░░░   0% Hebbian 🧠

Total: ~110-140 hours (+10-14hrs for edge)
Timeline: Still 5-6 months
Value: MASSIVE latency/privacy/cost improvements
```

---

## 🎯 **SUCCESS METRICS WITH EDGE AI**

**Performance:**
- ✅ Voice response <1s (edge-only)
- ✅ Chat response <500ms (simple queries, edge)
- ✅ 80% queries run edge-only
- ✅ Personality updates in real-time

**Privacy:**
- ✅ 90% of processing on-device
- ✅ No personality data sent to cloud
- ✅ Offline mode functional

**Cost:**
- ✅ 70-90% reduction in API costs
- ✅ Agentic behaviors affordable
- ✅ Scalable without cost explosion

**User Experience:**
- ✅ Personality feels INSTANT
- ✅ Responses feel "alive", not "computed"
- ✅ No lag between user and Penny

---

## 💡 **WHY EDGE AI IS NOT OVER-ENGINEERING**

**It Solves Audit Issues:**
1. Voice latency (Week 8 solved early)
2. Modal fragmentation (natural unified architecture)
3. Cost concerns (enables agentic scaling)
4. Privacy story (even stronger)

**It Enhances Strengths:**
1. Personality moat → feels instant/alive
2. Privacy-first → by architecture
3. Innovation → ahead of curve

**It Fits Your Hardware:**
- M4 Pro 48GB perfect for this
- Can run full stack simultaneously
- Industry moving this direction (Apple Intelligence, Gemini Nano)

**Expert Validation:**
- ChatGPT provided detailed blueprint
- Hybrid approach validated
- Technical feasibility confirmed

---

## 📚 **EDGE AI DOCUMENTATION**

**New Docs to Create:**
1. `docs/EDGE_AI_SETUP.md` - Installation guide
2. `docs/EDGE_AI_ARCHITECTURE.md` - System design
3. `docs/HYBRID_ROUTING_GUIDE.md` - Routing logic
4. `scripts/install_edge_stack.sh` - Automated setup
5. `scripts/benchmark_edge_models.py` - Performance tests

---

## 🚀 **IMMEDIATE ACTIONS**

**TODAY:**
1. ✅ Finish Week 3 tool calling

**THIS WEEK (Week 4):**
2. 🚨 Unify via EdgeModalInterface
3. 🚨 Integration tests + edge tests
4. 🚨 Concurrent access
5. 🔴 Tool safety
6. 🧠 Install edge stack (Ollama, Whisper, TTS)

**NEXT WEEK (Week 4.5):**
7. 🔴 Model manager
8. 🔴 Hybrid router
9. 🔴 Local TTS
10. ⚠️ Edge telemetry

---

## 🎊 **THE BOTTOM LINE**

**Edge AI transforms Penny from "good" to "revolutionary":**

- ✨ **Latency:** 3-5s → <1s (5x faster)
- ✨ **Privacy:** 50% local → 90% local
- ✨ **Cost:** $X/month → $0.1-0.3X/month (70-90% savings)
- ✨ **Experience:** "Computed" → "Alive"
- ✨ **Scalability:** Limited → Unlimited (agentic behaviors affordable)

**This is the right move. Let's do it.** 🚀✨💜

---

**Last Updated:** October 28, 2025  
**Next Review:** After Week 4 complete  
**Status:** EDGE AI INTEGRATION APPROVED → READY TO BUILD

**LET'S MAKE PENNY TRULY ALIVE!** 🧠⚡💜
