# WEEK 8 INTEGRATION GUIDE

**Purpose:** Step-by-step guide to integrate emotional continuity into ResearchFirstPipeline  
**Estimated Time:** 3-4 hours  
**Date:** December 28, 2025

---

## 🎯 INTEGRATION OVERVIEW

Week 8 adds emotional continuity to Penny by:
1. Detecting significant emotions in user messages
2. Tracking emotional threads across sessions
3. Suggesting natural check-ins about past emotions
4. Managing user consent and preferences
5. Creating personality snapshots for rollback
6. Applying gradual forgetting over time

---

## 📋 STEP 1: UPDATE IMPORTS

**File:** `research_first_pipeline.py`

```python
# Add Week 8 imports
from src.memory.emotion_detector_v2 import EmotionDetectorV2
from src.memory.emotional_continuity import EmotionalContinuity
from src.personality.personality_snapshots import PersonalitySnapshotManager
from src.memory.forgetting_mechanism import ForgettingMechanism
from src.memory.consent_manager import ConsentManager
```

---

## 📋 STEP 2: INITIALIZE WEEK 8 SYSTEMS

**File:** `research_first_pipeline.py` → `__init__` method

```python
def __init__(self):
    super().__init__()
    
    # ... existing initialization ...
    
    # Week 8: Consent Manager (check user preferences)
    self.consent_manager = ConsentManager()
    
    # Week 8: Upgrade emotion detection to v2
    self.emotion_detector = EmotionDetectorV2()
    
    # Week 8: Emotional continuity tracker
    self.emotional_continuity = EmotionalContinuity(
        semantic_memory=self.semantic_memory,
        emotion_detector=self.emotion_detector,
        window_days=self.consent_manager.get_memory_window(),
        intensity_threshold=self.consent_manager.get_intensity_threshold(),
        enabled=self.consent_manager.is_tracking_enabled()
    )
    
    # Week 8: Personality snapshots (every 50 conversations)
    self.personality_snapshots = PersonalitySnapshotManager(
        storage_path="data/personality_snapshots",
        snapshot_interval=50
    )
    
    # Week 8: Forgetting mechanism (30-day decay)
    self.forgetting_mechanism = ForgettingMechanism(decay_days=30)
    
    logger.info("🧠 Week 8 Emotional Continuity initialized")
```

---

## 📋 STEP 3: UPDATE THINK() METHOD

**File:** `research_first_pipeline.py` → `think()` method

### **3.1: Track Emotion (Before LLM Call)**

```python
def think(self, user_text: str) -> str:
    \"\"\"Process input with emotional continuity\"\"\"
    
    # Generate unique turn ID
    turn_id = f"turn_{int(time.time() * 1000)}"
    
    # Week 8: Track emotion if significant
    emotional_thread = None
    if self.consent_manager.is_tracking_enabled():
        emotional_thread = self.emotional_continuity.track_emotion(
            user_input=user_text,
            turn_id=turn_id
        )
        
        if emotional_thread:
            logger.info(
                f"📌 Tracked emotion: {emotional_thread.emotion} "
                f"(intensity={emotional_thread.intensity:.2f})"
            )
    
    # ... existing code ...
```

### **3.2: Check for Emotional Context (Before LLM Call)**

```python
    # Week 8: Check if we should reference previous emotional context
    check_in_thread = None
    emotional_context = ""
    
    if self.consent_manager.is_checkins_enabled():
        check_in_thread = self.emotional_continuity.should_check_in()
        
        if check_in_thread:
            emotional_context = self.emotional_continuity.generate_check_in_prompt(
                check_in_thread
            )
            logger.info(f"💭 Suggesting emotional check-in: {check_in_thread.emotion}")
```

### **3.3: Build Enhanced System Prompt**

```python
    # Build system prompt with emotional context
    base_system_prompt = self.personality_builder.build_prompt(...)
    
    if emotional_context:
        # Add emotional context to system prompt
        system_prompt = f\"{base_system_prompt}\
\
{emotional_context}\"
    else:
        system_prompt = base_system_prompt
```

### **3.4: Call LLM (Existing)**

```python
    # ... existing LLM call logic ...
    response = self.llm.generate(messages, system_prompt=system_prompt)
```

### **3.5: Mark Follow-Up (After LLM Call)**

```python
    # Week 8: Mark thread as followed up if we referenced it
    if check_in_thread and self._response_references_emotion(response, check_in_thread):
        self.emotional_continuity.mark_followed_up(check_in_thread, turn_id)
        logger.info(f"✅ Marked emotional follow-up for {check_in_thread.turn_id}")
```

### **3.6: Snapshot Check (After Conversation)**

```python
    # Week 8: Check if snapshot needed
    conversation_count = len(self.semantic_memory.get_all_turns())
    
    if self.personality_snapshots.should_snapshot(conversation_count):
        # Get current personality state
        personality_state = self.personality_tracker.get_personality_state()
        
        # Get current emotional threads
        emotional_threads = [
            t.to_dict() for t in self.emotional_continuity.threads
        ]
        
        # Create snapshot
        snapshot = self.personality_snapshots.create_snapshot(
            personality_state=personality_state,
            emotional_threads=emotional_threads,
            conversation_count=conversation_count
        )
        
        logger.info(f"📸 Created personality snapshot v{snapshot.version}")
```

### **3.7: Apply Forgetting (Periodic)**

```python
    # Week 8: Apply forgetting mechanism (every N conversations)
    if conversation_count % 10 == 0:  # Every 10 conversations
        self.emotional_continuity.threads = self.forgetting_mechanism.apply_decay(
            self.emotional_continuity.threads
        )
```

---

## 📋 STEP 4: ADD HELPER METHODS

**File:** `research_first_pipeline.py`

```python
def _response_references_emotion(self, response: str, thread) -> bool:
    \"\"\"
    Check if Penny's response references the emotional thread.
    
    Simple heuristic: Does response mention the emotion or context?
    \"\"\"
    response_lower = response.lower()
    
    # Check for emotion mention
    if thread.emotion.lower() in response_lower:
        return True
    
    # Check for context keywords
    context_words = thread.context.lower().split()[:5]  # First 5 words
    for word in context_words:
        if len(word) > 4 and word in response_lower:  # Only meaningful words
            return True
    
    return False
```

---

## 📋 STEP 5: ADD CONSENT DIALOG (FIRST RUN)

**File:** `research_first_pipeline.py` or web interface

```python
def _check_emotional_consent(self):
    \"\"\"Check if user has granted consent for emotional tracking\"\"\"
    
    if not self.consent_manager.is_tracking_enabled():
        # Show consent dialog to user
        consent_text = \"\"\"
        Penny can remember how you feel about things across conversations.
        
        This means:
        - Penny tracks significant emotions (stress, excitement, sadness)
        - Penny can check in naturally about past emotional moments
        - Your emotional data is encrypted and under your control
        
        You can:
        - Disable tracking anytime
        - Manually forget specific moments
        - Rollback personality changes
        
        Enable emotional tracking?
        \"\"\"
        
        # Get user response (implementation depends on interface)
        user_response = self._prompt_user(consent_text)
        
        if user_response.lower() in ['yes', 'y', 'enable', 'sure']:
            self.consent_manager.grant_consent(
                emotional_tracking=True,
                proactive_checkins=True
            )
            logger.info("✅ User granted emotional tracking consent")
            return True
        else:
            logger.info("❌ User declined emotional tracking")
            return False
    
    return True  # Already has consent
```

Call this in `think()` before tracking:

```python
def think(self, user_text: str) -> str:
    # Check consent on first emotional trigger
    if not self.consent_manager.is_tracking_enabled():
        if self.emotion_detector.is_significant_emotion(user_text):
            self._check_emotional_consent()
    
    # ... rest of think() logic ...
```

---

## 📋 STEP 6: ADD MANAGEMENT COMMANDS

**File:** New `src/cli/emotional_management.py` or integrate into existing CLI

```python
def cmd_show_emotional_threads(self):
    \"\"\"Show current emotional threads\"\"\"
    threads = self.emotional_continuity.get_recent_threads()
    
    print(f\"\
Recent Emotional Threads ({len(threads)}):\")
    for thread in threads:
        days_ago = (datetime.now() - thread.timestamp).days
        print(f\"  [{thread.emotion}] {thread.context[:50]}... \")
        print(f\"    Intensity: {thread.intensity:.2f} | {days_ago} days ago\")

def cmd_forget_thread(self, turn_id: str):
    \"\"\"Manually forget a specific thread\"\"\"
    self.emotional_continuity.threads = self.forgetting_mechanism.forget_thread(
        self.emotional_continuity.threads,
        turn_id
    )
    print(f\"Forgot emotional thread {turn_id}\")

def cmd_rollback_personality(self, version: int):
    \"\"\"Rollback personality to previous version\"\"\"
    snapshot = self.personality_snapshots.rollback_to_version(version)
    
    if snapshot:
        # Restore personality state
        self.personality_tracker.restore_state(snapshot.personality_state)
        
        # Restore emotional threads
        self.emotional_continuity.threads = [
            EmotionalThread.from_dict(t) for t in snapshot.emotional_threads
        ]
        
        print(f\"Rolled back to personality v{version}\")
    else:
        print(f\"Snapshot v{version} not found\")

def cmd_show_consent_status(self):
    \"\"\"Show current consent and preferences\"\"\"
    prefs = self.consent_manager.get_preferences()
    
    print(\"Emotional Tracking Status:\")
    print(f\"  Tracking enabled: {prefs['emotional_tracking_enabled']}\")
    print(f\"  Check-ins enabled: {prefs['proactive_checkins_enabled']}\")
    print(f\"  Intensity threshold: {prefs['intensity_threshold']}\")
    print(f\"  Memory window: {prefs['memory_window_days']} days\")
```

---

## 📋 STEP 7: UPDATE WEB INTERFACE (OPTIONAL)

**File:** `run_penny_http.py` or similar

Add endpoints for:

```python
@app.get(\"/api/emotional_threads\")
def get_emotional_threads():
    \"\"\"Get current emotional threads\"\"\"
    threads = pipeline.emotional_continuity.get_recent_threads()
    return {
        'threads': [t.to_dict() for t in threads],
        'stats': pipeline.emotional_continuity.get_stats()
    }

@app.post(\"/api/consent\")
def update_consent(request: ConsentRequest):
    \"\"\"Update emotional tracking consent\"\"\"
    if request.tracking_enabled:
        pipeline.consent_manager.grant_consent(
            emotional_tracking=True,
            proactive_checkins=request.checkins_enabled
        )
    else:
        pipeline.consent_manager.revoke_consent()
    
    return {'status': 'updated'}

@app.get(\"/api/personality_versions\")
def get_personality_versions():
    \"\"\"Get personality snapshot history\"\"\"
    return pipeline.personality_snapshots.list_versions()

@app.post(\"/api/personality_rollback\")
def rollback_personality(request: RollbackRequest):
    \"\"\"Rollback to previous personality version\"\"\"
    snapshot = pipeline.personality_snapshots.rollback_to_version(request.version)
    
    if snapshot:
        # ... restore logic ...
        return {'status': 'rolled_back', 'version': request.version}
    else:
        return {'status': 'error', 'message': 'Version not found'}
```

---

## 📋 STEP 8: TESTING

### **8.1: Unit Tests (Already Done)**
```bash
pytest tests/test_emotion_detector_v2.py -v
pytest tests/test_emotional_continuity.py -v
```

### **8.2: Integration Test**

```python
# Test file: tests/test_week8_integration.py

def test_full_week8_workflow():
    \"\"\"Test complete Week 8 workflow\"\"\"
    pipeline = ResearchFirstPipeline()
    
    # 1. Grant consent
    pipeline.consent_manager.grant_consent(emotional_tracking=True)
    
    # 2. Process emotional input
    response1 = pipeline.think(\"I'm so stressed about work layoffs\")
    
    # Should track emotion
    assert len(pipeline.emotional_continuity.threads) > 0
    thread = pipeline.emotional_continuity.threads[0]
    assert thread.emotion in ['fear', 'sadness', 'stress']
    
    # 3. Next conversation should suggest check-in
    check_in = pipeline.emotional_continuity.should_check_in()
    assert check_in is not None
    
    # 4. Process next input with check-in
    response2 = pipeline.think(\"Hey Penny\")
    
    # Should reference previous stress
    assert 'stress' in response2.lower() or 'work' in response2.lower()
```

### **8.3: Real-World Test**

```bash
# Start Penny
python main.py

# Test sequence:
User: "I'm really worried about my job interview tomorrow"
Penny: [Should track emotion, intensity ~0.85]

User: "Tell me about Python"
Penny: [Normal response, no emotional reference]

User: "Hey Penny"
Penny: [Should check in] "Hey! How are you feeling about that interview? 
                         You seemed worried yesterday."
```

---

## ✅ VERIFICATION CHECKLIST

- [ ] Week 8 imports added
- [ ] Systems initialized in `__init__`
- [ ] Emotion tracking in `think()`
- [ ] Check-in logic added
- [ ] System prompt enhanced with emotional context
- [ ] Follow-up marking implemented
- [ ] Snapshot creation added
- [ ] Forgetting mechanism integrated
- [ ] Consent dialog shown on first use
- [ ] Management commands available
- [ ] Unit tests passing (100%)
- [ ] Integration test passing
- [ ] Real-world test validates natural check-ins

---

## 🎯 EXPECTED RESULTS

After integration, you should see:

1. **Logs:**
```
🧠 Week 8 Emotional Continuity initialized
📌 Tracked emotion: stress (intensity=0.87)
💭 Suggesting emotional check-in: stress
✅ Marked emotional follow-up for turn_12345
📸 Created personality snapshot v3
```

2. **Behavior:**
- Penny remembers significant emotional moments
- Natural check-ins days later
- Appropriate emotional references
- No intrusive over-tracking

3. **Performance:**
- <100ms overhead for emotion detection
- <10ms for emotional context check
- No noticeable latency

---

## 🚨 TROUBLESHOOTING

### **Issue: Emotion detection too slow**
```python
# Solution: Check model loading
detector = EmotionDetectorV2()
info = detector.get_model_info()
print(info)  # Should show transformer model loaded

# If slow, ensure model is cached:
# ~/.cache/huggingface/transformers/
```

### **Issue: No emotional tracking**
```python
# Check consent
print(pipeline.consent_manager.is_tracking_enabled())  # Should be True

# Check detector
result = pipeline.emotion_detector.detect_emotion("I'm stressed!")
print(result)  # Should show emotion and intensity
```

### **Issue: Too many/few check-ins**
```python
# Adjust intensity threshold
pipeline.consent_manager.update_preferences(intensity_threshold=0.9)  # Fewer
pipeline.consent_manager.update_preferences(intensity_threshold=0.7)  # More
```

---

**Integration Time:** 3-4 hours  
**Difficulty:** Medium (well-defined integration points)  
**Risk:** Low (backwards compatible, can disable)  

Ready to make Penny genuinely remember how you feel! 🧠❤️
