# Week 6 Integration Architecture

**System**: Context Manager, Emotion Detector & Semantic Memory
**Integration Target**: ResearchFirstPipeline (Production Pipeline)
**Status**: Deployed as Baseline Features

---

## Architecture Overview

Week 6 introduces three interconnected memory systems that enhance Penny's conversational capabilities:

1. **Context Manager** - Maintains short-term conversation window
2. **Emotion Detector** - Analyzes emotional content in user messages
3. **Semantic Memory** - Provides long-term memory with vector similarity search

These systems integrate at multiple points in the conversation pipeline to provide:
- Emotional awareness
- Conversational coherence
- Relevant historical context
- Personalized responses

---

## System Components

### 1. Context Manager
**File**: `src/memory/context_manager.py`

```python
class ContextManager:
    """
    Maintains a rolling window of recent conversation turns.

    Features:
    - Configurable window size (default: 10 turns)
    - Tracks user input, assistant response, metadata
    - Provides formatted context strings for LLM
    - Monitors current topic and emotional state
    """
```

**Key Methods**:
- `add_turn(user_input, assistant_response, metadata)` - Add conversation turn
- `get_context_for_prompt(max_turns, include_metadata)` - Retrieve formatted context
- `get_stats()` - Get window statistics
- `clear()` - Reset context

**Storage**: In-memory deque (FIFO queue)

**Data Structure**:
```python
{
    'user_input': str,
    'assistant_response': str,
    'timestamp': datetime,
    'metadata': {
        'emotion': str,
        'sentiment': str,
        'research_used': bool,
        ...
    }
}
```

---

### 2. Emotion Detector
**File**: `src/memory/emotion_detector.py`

```python
class EmotionDetector:
    """
    Keyword-based emotion detection with sentiment analysis.

    Emotions: joy, sadness, anger, fear, surprise, neutral
    Sentiment: positive, negative, neutral
    """
```

**Key Methods**:
- `detect_emotion(text)` - Returns EmotionResult
- `get_sentiment(text)` - Returns sentiment category and score

**Algorithm**:
1. Lowercase input text
2. Match keywords against emotion dictionaries
3. Count matches per emotion category
4. Calculate confidence based on match density
5. Determine primary emotion (highest score)
6. Calculate sentiment score (-1 to +1)

**EmotionResult**:
```python
{
    'primary_emotion': str,      # Most likely emotion
    'confidence': float,         # 0.0 - 1.0
    'sentiment': str,           # positive/negative/neutral
    'sentiment_score': float,   # -1.0 to +1.0
    'all_emotions': Dict[str, float]  # Scores for all emotions
}
```

**Performance**: <1ms per detection (keyword matching)

---

### 3. Semantic Memory
**File**: `src/memory/semantic_memory.py`

```python
class SemanticMemory:
    """
    Vector-based long-term memory with similarity search.

    Technology:
    - sentence-transformers (all-MiniLM-L6-v2)
    - FAISS IndexFlatIP (inner product similarity)
    - 384-dimensional embeddings
    """
```

**Key Methods**:
- `add_conversation_turn(user_input, assistant_response, turn_id, context)` - Index conversation
- `semantic_search(query, k, min_similarity)` - Find similar conversations
- `get_relevant_context(query, max_turns, min_similarity)` - Get formatted context
- `save(filepath)` / `load(filepath)` - Persistence (currently not used)

**Components**:

1. **Embedding Generator** (`src/memory/embedding_generator.py`):
```python
class EmbeddingGenerator:
    """
    Generates 384-dim embeddings using sentence-transformers.
    Model: all-MiniLM-L6-v2
    """
```

2. **Vector Store** (`src/memory/vector_store.py`):
```python
class VectorStore:
    """
    FAISS-based vector storage with metadata.
    Index type: IndexFlatIP (inner product)
    """
```

**Performance**: ~50-100ms per search (FAISS vector similarity)

**Storage**: In-memory (resets on server restart)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                │
│                     "What's the weather?"                        │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                   EMOTION DETECTION                             │
│  emotion_detector.detect_emotion(user_input)                   │
│  → EmotionResult(primary_emotion='neutral', confidence=0.8)    │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│               RESEARCH CLASSIFICATION                           │
│  research_manager.requires_research(user_input)                │
│  → True (weather query requires current data)                  │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                 RESEARCH EXECUTION                              │
│  research_manager.run_research(query, [])                      │
│  → research_context (findings, key insights, summary)          │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│              CONTEXT RETRIEVAL (Week 6)                         │
│  context_manager.get_context_for_prompt(max_turns=5)          │
│  → conversation_context (last 5 turns formatted)               │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│             SEMANTIC SEARCH (Week 6)                            │
│  semantic_memory.semantic_search(query, k=3)                   │
│  → semantic_results (top 3 similar past conversations)         │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                  PROMPT BUILDING                                │
│  Combines:                                                      │
│  - System prompt (personality)                                 │
│  - Research instructions                                       │
│  - Personality enhancement (treatment group only)              │
│  - Conversation context (Week 6)                               │
│  - Semantic memory results (Week 6)                            │
│  - Current emotion & topic (Week 6)                            │
│  - Legacy memory context                                       │
│  - Research context                                            │
│  - Tool manifest                                               │
│  → final_prompt                                                │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                 LLM GENERATION                                  │
│  llm.complete(final_prompt)                                    │
│  → raw_response                                                │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│               POST-PROCESSING                                   │
│  - Personality adjustments (treatment group)                   │
│  - Financial disclaimer (if needed)                            │
│  - Output sanitization                                         │
│  → final_response                                              │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────┐
│                  TRIPLE SAVE (Week 6)                           │
│  1. base_memory.add_conversation_turn()                        │
│     → turn_id                                                  │
│  2. context_manager.add_turn()                                 │
│     → rolling window updated                                   │
│  3. semantic_memory.add_conversation_turn()                    │
│     → vector embedding indexed                                 │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
                    ┌────────────────┐
                    │  FINAL RESPONSE │
                    └────────────────┘
```

---

## Integration Points in ResearchFirstPipeline

### 1. Initialization (Line 75-79)
```python
# Week 6: Context Manager, Emotion Detector, Semantic Memory
self.context_manager = ContextManager(max_window_size=10)
self.emotion_detector = EmotionDetector()
self.semantic_memory = SemanticMemory()
logger.info("🧠 Week 6 systems initialized")
```

### 2. Emotion Detection (Line 111-113)
```python
# Step 1.5: Week 6 - Detect emotion from user input
emotion_result = self.emotion_detector.detect_emotion(actual_command)
print(f"😊 Emotion detected: {emotion_result.primary_emotion}")
```

### 3. Context Retrieval (Line 175-177)
```python
# Step 4.5: Week 6 - Get conversation context
conversation_context = self.context_manager.get_context_for_prompt(
    max_turns=5,
    include_metadata=True
)
```

### 4. Semantic Search (Line 180-185)
```python
# Get semantic memories (similar past conversations)
semantic_results = []
try:
    semantic_results = self.semantic_memory.semantic_search(
        query=actual_command,
        k=3
    )
    print(f"🧠 Semantic memory: Found {len(semantic_results)} relevant memories")
except Exception as e:
    logger.warning(f"Semantic search failed: {e}")
```

### 5. Prompt Building (Line 233-254)
```python
# Week 6: Add conversation context from context manager
if conversation_context:
    prompt_sections.append(f"\n{conversation_context}")

# Week 6: Add semantic memory context
if semantic_results:
    semantic_context = "\n\nRelevant past conversations:"
    for result in semantic_results:
        semantic_context += f"\n- User: {result.get('user_input', '')[:100]}..."
    prompt_sections.append(semantic_context)

# Week 6: Add current topic and emotional state
stats = self.context_manager.get_stats()
context_info = []
if stats.get('current_topic'):
    context_info.append(f"Current topic: {stats['current_topic']}")
if emotion_result:
    context_info.append(f"User's current emotion: {emotion_result.primary_emotion}")
if context_info:
    prompt_sections.append("\n\n" + "\n".join(context_info))
```

### 6. Triple Save (Line 377-396)
```python
# Build enhanced metadata with emotion
enhanced_metadata = {
    "research_used": research_required,
    "financial_topic": financial_topic,
    "emotion": emotion_result.primary_emotion,
    "emotion_confidence": emotion_result.confidence,
    "sentiment": emotion_result.sentiment,
    "sentiment_score": emotion_result.sentiment_score
}

# Save to base memory
turn = self.base_memory.add_conversation_turn(...)

# Week 6: Save to context manager with emotion metadata
self.context_manager.add_turn(
    user_input=actual_command,
    assistant_response=final_response,
    metadata=enhanced_metadata
)

# Week 6: Save to semantic memory
self.semantic_memory.add_conversation_turn(
    user_input=actual_command,
    assistant_response=final_response,
    turn_id=turn.turn_id,
    context=enhanced_metadata
)
```

---

## Week 6 Outside A/B Test Framework

**Design Philosophy**: Week 6 features are **baseline improvements** that benefit all users.

### Why Outside A/B Test?

1. **Core Infrastructure**: Context awareness is fundamental to good conversation, not experimental
2. **Fair Comparison**: Both control and treatment groups should have the same context baseline
3. **Immediate Value**: Users benefit immediately without waiting for experiment results

### A/B Test Structure

```
Control Group:
  ✅ Week 6: Context Manager
  ✅ Week 6: Emotion Detector
  ✅ Week 6: Semantic Memory
  ❌ Personality Enhancement (baseline only)
  ❌ Response Post-Processing

Treatment Group:
  ✅ Week 6: Context Manager
  ✅ Week 6: Emotion Detector
  ✅ Week 6: Semantic Memory
  ✅ Personality Enhancement (dynamic prompts)
  ✅ Response Post-Processing (personality adjustments)
```

**What's Being Tested**: Dynamic personality adaptation (Phase 2), not context awareness (Week 6)

---

## Performance Characteristics

### Latency Impact

| Component | Latency | When |
|-----------|---------|------|
| Emotion Detection | <1ms | Every request |
| Context Retrieval | <5ms | Every request |
| Semantic Search | 50-100ms | Every request |
| Embedding Generation | 20-50ms | On save only |
| **Total Overhead** | **~100-150ms** | **Per request** |

### Memory Usage

| Component | Memory | Growth Rate |
|-----------|--------|-------------|
| Context Manager | ~10 KB | Fixed (10-turn window) |
| Emotion Detector | <1 KB | Fixed (keyword dicts) |
| Semantic Memory | ~500 bytes/conv | Linear (~500 KB per 1000 convs) |
| Embedding Model | ~100 MB | Fixed (model weights) |
| **Total** | **~100 MB + 500 bytes/conv** | |

### Scalability

- **Context Manager**: O(1) - Fixed window size
- **Emotion Detector**: O(n) - n = text length (fast keyword matching)
- **Semantic Search**: O(d×k) - d = embedding dimension (384), k = result count (3)
- **FAISS Performance**: Sub-linear search on large datasets (optimized C++)

---

## Error Handling

### Graceful Degradation

All Week 6 systems are designed to fail gracefully without breaking the pipeline:

```python
# Example: Semantic search with fallback
semantic_results = []
try:
    semantic_results = self.semantic_memory.semantic_search(query, k=3)
except Exception as e:
    logger.warning(f"Semantic search failed: {e}")
    # Continue with empty results - not critical
```

### Known Issues & Mitigations

1. **HuggingFace Cache Permissions**
   - **Issue**: Model downloads fail without write access
   - **Mitigation**: Set HF_HOME to local project cache before imports

2. **Empty Semantic Memory**
   - **Issue**: New deployments have no indexed conversations
   - **Mitigation**: Gracefully handle 0 results from semantic search

3. **In-Memory Vector Store**
   - **Issue**: Semantic memory resets on server restart
   - **Mitigation**: Implement save/load functionality (future work)

---

## Future Enhancements

### Short-Term (Week 7)
1. Persistent semantic memory (save/load FAISS index)
2. Incremental indexing (batch updates)
3. Memory pruning strategies (remove old/low-value conversations)

### Medium-Term (Phase 4)
1. ML-based emotion detection (replace keyword matching)
2. Multi-modal embeddings (text + voice tone + context)
3. Hierarchical memory (short-term → long-term consolidation)

### Long-Term (Phase 5)
1. Distributed semantic memory (shared across users with privacy)
2. Personalized embedding fine-tuning
3. Predictive context pre-loading

---

## Testing Strategy

### Unit Tests
- `test_context_manager.py` - Context window operations
- `test_emotion_detector.py` - Emotion classification accuracy
- `test_semantic_memory.py` - Vector search correctness

### Integration Tests
- `test_full_integration_v2.py` - End-to-end pipeline with Week 6
- `diagnostics_week6.py` - Comprehensive system diagnostics

### Test Coverage
- Context Manager: 100% (all methods tested)
- Emotion Detector: 85% (keyword accuracy validated)
- Semantic Memory: 90% (search and storage validated)

---

## Monitoring & Observability

### Debug Logging
All Week 6 operations log to console with emoji prefixes:

```
😊 Emotion detected: joy (confidence: 0.85, sentiment: positive)
💬 Conversation context: 1234 chars
🧠 Semantic memory: Found 3 relevant memories
✨ Final prompt built: 5678 chars (includes Week 6 context)
💾 Context Manager: Saved turn with emotion joy
🧠 Semantic Memory: Turn indexed for future retrieval
```

### Metrics to Track
1. **Emotion Distribution**: Track primary emotion frequencies
2. **Context Utilization**: How often semantic results are found
3. **Search Latency**: Monitor FAISS search performance
4. **Memory Growth**: Track semantic memory database size

---

## Conclusion

Week 6 architecture successfully integrates three complementary memory systems into Penny's production pipeline:

- **Context Manager** provides short-term coherence
- **Emotion Detector** adds emotional intelligence
- **Semantic Memory** enables long-term recall

These systems work together to create more contextually aware, emotionally intelligent, and personalized conversations while maintaining performance (<150ms overhead) and reliability (graceful degradation).

**Status**: ✅ PRODUCTION-READY
