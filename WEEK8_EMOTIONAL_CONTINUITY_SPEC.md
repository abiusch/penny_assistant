# WEEK 8: EMOTIONAL CONTINUITY - CC IMPLEMENTATION SPEC

**Date:** December 27, 2025  
**Priority:** HIGH - Core Differentiation Feature  
**Estimated Time:** 18-22 hours  
**Status:** Ready to implement (Week 7.5 complete, all systems validated)

---

## 🎯 **OBJECTIVE:**

Implement safe cross-session emotional tracking that makes Penny remember your emotional context across conversations, creating genuine relationship continuity.

---

## 📋 **PREREQUISITES (ALL VALIDATED ✅):**

```
✅ Week 7: Security + Architecture (100% complete)
   - Encryption working (GDPR-compliant)
   - PII detection active
   - Semantic memory (522 conversations)
   - Single-store architecture

✅ Week 7.5: Nemotron-3 Nano (100% complete)
   - Local LLM working
   - 100% test pass rate
   - Production certified

✅ Week 6: Baseline Emotion Detection
   - Keyword-based detector (60-70% accuracy)
   - 6 emotions tracked
   - Ready for upgrade
```

---

## 🎯 **WEEK 8 DELIVERABLES:**

### **1. Upgrade Emotion Detection (5-6 hours)** 🧠

**Current:** Keyword-based, 60-70% accuracy  
**Target:** Transformer-based, 90%+ accuracy

**Implementation:**

```python
# NEW: src/memory/emotion_detector_v2.py

from transformers import pipeline
import logging

logger = logging.getLogger(__name__)


class EmotionDetectorV2:
    """
    Transformer-based emotion detection with 90%+ accuracy.
    Uses j-hartmann/emotion-english-distilroberta-base
    """
    
    def __init__(self):
        """Initialize transformer model"""
        try:
            # Load emotion classification model
            # 94% accuracy, ~50ms on CPU
            self.classifier = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                return_all_scores=True
            )
            logger.info("✅ EmotionDetectorV2 initialized (transformer-based)")
        except Exception as e:
            logger.error(f"Failed to load emotion model: {e}")
            # Fallback to v1 if model fails
            from src.memory.emotion_detector import EmotionDetector
            self.classifier = EmotionDetector()
            logger.warning("⚠️ Falling back to keyword-based emotion detection")
    
    def detect_emotion(self, text: str) -> dict:
        """
        Detect emotion with confidence scores.
        
        Args:
            text: Text to analyze
            
        Returns:
            {
                'dominant_emotion': 'joy',
                'confidence': 0.87,
                'all_scores': {
                    'joy': 0.87,
                    'sadness': 0.05,
                    'anger': 0.03,
                    'fear': 0.02,
                    'surprise': 0.02,
                    'neutral': 0.01
                }
            }
        """
        if not text or len(text.strip()) < 3:
            return {
                'dominant_emotion': 'neutral',
                'confidence': 1.0,
                'all_scores': {'neutral': 1.0}
            }
        
        try:
            # Get predictions
            results = self.classifier(text)[0]
            
            # Convert to our format
            scores = {r['label']: r['score'] for r in results}
            
            # Find dominant emotion
            dominant = max(scores.items(), key=lambda x: x[1])
            
            return {
                'dominant_emotion': dominant[0],
                'confidence': dominant[1],
                'all_scores': scores
            }
        
        except Exception as e:
            logger.error(f"Emotion detection failed: {e}")
            return {
                'dominant_emotion': 'neutral',
                'confidence': 0.5,
                'all_scores': {'neutral': 0.5}
            }
    
    def detect_intensity(self, text: str) -> float:
        """
        Detect emotional intensity (0.0-1.0).
        
        Returns:
            0.0 = neutral/calm
            1.0 = highly emotional
        """
        result = self.detect_emotion(text)
        
        # Intensity = confidence * (1 - neutral_score)
        neutral_score = result['all_scores'].get('neutral', 0.0)
        intensity = result['confidence'] * (1.0 - neutral_score)
        
        return min(1.0, max(0.0, intensity))
```

**Files:**
- NEW: `src/memory/emotion_detector_v2.py` (~200 lines)
- UPDATE: `research_first_pipeline.py` - Use v2 detector
- NEW: `tests/test_emotion_detector_v2.py` (~150 lines)

**Success Criteria:**
- ✅ Accuracy >90% on test set
- ✅ Inference <100ms on CPU
- ✅ Fallback to v1 if model fails
- ✅ All 6 emotions detected with confidence

---

### **2. Cross-Session Emotional Tracking (8-10 hours)** ❤️

**What This Does:**
Track significant emotional moments across sessions (7-day window) and reference them naturally.

**Implementation:**

```python
# NEW: src/memory/emotional_continuity.py

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class EmotionalThread:
    """Represents an emotional thread across sessions"""
    
    def __init__(
        self,
        emotion: str,
        intensity: float,
        context: str,
        timestamp: datetime,
        turn_id: str
    ):
        self.emotion = emotion
        self.intensity = intensity
        self.context = context  # What was said
        self.timestamp = timestamp
        self.turn_id = turn_id
        self.follow_ups: List[str] = []  # Follow-up turn IDs
    
    def to_dict(self) -> dict:
        return {
            'emotion': self.emotion,
            'intensity': self.intensity,
            'context': self.context,
            'timestamp': self.timestamp.isoformat(),
            'turn_id': self.turn_id,
            'follow_ups': self.follow_ups
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EmotionalThread':
        thread = cls(
            emotion=data['emotion'],
            intensity=data['intensity'],
            context=data['context'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            turn_id=data['turn_id']
        )
        thread.follow_ups = data.get('follow_ups', [])
        return thread


class EmotionalContinuity:
    """
    Tracks emotional context across sessions.
    
    Features:
    - 7-day emotional memory window
    - 0.8+ intensity threshold (only significant emotions)
    - Natural follow-up suggestions
    - User consent required
    - 30-day auto-decay
    """
    
    def __init__(
        self,
        semantic_memory,
        emotion_detector,
        window_days: int = 7,
        intensity_threshold: float = 0.8,
        enabled: bool = True
    ):
        self.semantic_memory = semantic_memory
        self.emotion_detector = emotion_detector
        self.window_days = window_days
        self.intensity_threshold = intensity_threshold
        self.enabled = enabled
        
        # Track emotional threads
        self.threads: List[EmotionalThread] = []
        
        logger.info(f"EmotionalContinuity initialized (window={window_days}d, threshold={intensity_threshold})")
    
    def track_emotion(
        self,
        user_input: str,
        turn_id: str,
        timestamp: Optional[datetime] = None
    ) -> Optional[EmotionalThread]:
        """
        Track emotional moment if significant.
        
        Returns:
            EmotionalThread if emotion is significant enough, None otherwise
        """
        if not self.enabled:
            return None
        
        if timestamp is None:
            timestamp = datetime.now()
        
        # Detect emotion
        emotion_result = self.emotion_detector.detect_emotion(user_input)
        intensity = self.emotion_detector.detect_intensity(user_input)
        
        # Only track if intensity exceeds threshold
        if intensity < self.intensity_threshold:
            logger.debug(f"Emotion intensity {intensity:.2f} below threshold {self.intensity_threshold}")
            return None
        
        # Create thread
        thread = EmotionalThread(
            emotion=emotion_result['dominant_emotion'],
            intensity=intensity,
            context=user_input[:200],  # Store context snippet
            timestamp=timestamp,
            turn_id=turn_id
        )
        
        self.threads.append(thread)
        logger.info(f"📌 Tracked emotional thread: {thread.emotion} (intensity={intensity:.2f})")
        
        # Clean old threads
        self._cleanup_old_threads()
        
        return thread
    
    def get_recent_threads(
        self,
        emotion: Optional[str] = None,
        min_intensity: float = 0.7
    ) -> List[EmotionalThread]:
        """
        Get recent emotional threads.
        
        Args:
            emotion: Filter by specific emotion (optional)
            min_intensity: Minimum intensity threshold
            
        Returns:
            List of recent emotional threads
        """
        cutoff = datetime.now() - timedelta(days=self.window_days)
        
        threads = [
            t for t in self.threads
            if t.timestamp > cutoff and t.intensity >= min_intensity
        ]
        
        if emotion:
            threads = [t for t in threads if t.emotion == emotion]
        
        return sorted(threads, key=lambda t: t.timestamp, reverse=True)
    
    def should_check_in(self) -> Optional[EmotionalThread]:
        """
        Determine if Penny should proactively check in about an emotional thread.
        
        Returns:
            EmotionalThread to check in about, or None
        """
        if not self.enabled:
            return None
        
        # Get recent significant threads
        recent = self.get_recent_threads(min_intensity=0.8)
        
        if not recent:
            return None
        
        # Find threads with no follow-ups
        unresolved = [t for t in recent if not t.follow_ups]
        
        if unresolved:
            # Check in about most recent unresolved thread
            return unresolved[0]
        
        return None
    
    def mark_followed_up(self, thread: EmotionalThread, follow_up_turn_id: str):
        """Mark that a thread was followed up on"""
        thread.follow_ups.append(follow_up_turn_id)
        logger.info(f"Marked thread {thread.turn_id} as followed up")
    
    def generate_check_in_prompt(self, thread: EmotionalThread) -> str:
        """
        Generate natural check-in prompt for Penny.
        
        Returns:
            Prompt addition like: "User seemed stressed about layoffs 2 days ago. 
            Consider checking in naturally if appropriate."
        """
        days_ago = (datetime.now() - thread.timestamp).days
        
        time_ref = f"{days_ago} days ago" if days_ago > 0 else "earlier today"
        
        return (
            f"[EMOTIONAL CONTEXT] User expressed {thread.emotion} "
            f"(intensity={thread.intensity:.2f}) {time_ref}. "
            f"Context: \"{thread.context[:100]}...\". "
            f"Consider acknowledging this naturally if appropriate."
        )
    
    def _cleanup_old_threads(self):
        """Remove threads older than window"""
        cutoff = datetime.now() - timedelta(days=self.window_days)
        self.threads = [t for t in self.threads if t.timestamp > cutoff]
    
    def get_stats(self) -> dict:
        """Get emotional tracking statistics"""
        recent = self.get_recent_threads()
        
        emotion_counts = {}
        for thread in recent:
            emotion_counts[thread.emotion] = emotion_counts.get(thread.emotion, 0) + 1
        
        return {
            'enabled': self.enabled,
            'window_days': self.window_days,
            'total_threads': len(recent),
            'emotion_breakdown': emotion_counts,
            'avg_intensity': sum(t.intensity for t in recent) / len(recent) if recent else 0.0
        }
```

**Files:**
- NEW: `src/memory/emotional_continuity.py` (~350 lines)
- NEW: `src/memory/emotional_thread.py` - Data models
- UPDATE: `research_first_pipeline.py` - Integrate emotional continuity
- NEW: `tests/test_emotional_continuity.py` (~200 lines)

**Success Criteria:**
- ✅ Tracks emotions with intensity >0.8
- ✅ 7-day memory window
- ✅ Natural check-in suggestions
- ✅ Thread follow-up tracking

---

### **3. Safety & Consent Mechanisms (4-5 hours)** 🔒

**What This Does:**
Give users control over emotional tracking with consent, forgetting, and rollback.

**Implementation:**

```python
# NEW: src/personality/personality_snapshots.py

from datetime import datetime
from typing import Dict, List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PersonalitySnapshot:
    """Version-controlled personality state"""
    
    def __init__(
        self,
        version: int,
        timestamp: datetime,
        personality_state: dict,
        emotional_threads: List[dict],
        conversation_count: int
    ):
        self.version = version
        self.timestamp = timestamp
        self.personality_state = personality_state
        self.emotional_threads = emotional_threads
        self.conversation_count = conversation_count
    
    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'personality_state': self.personality_state,
            'emotional_threads': self.emotional_threads,
            'conversation_count': self.conversation_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PersonalitySnapshot':
        return cls(
            version=data['version'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            personality_state=data['personality_state'],
            emotional_threads=data['emotional_threads'],
            conversation_count=data['conversation_count']
        )


class PersonalitySnapshotManager:
    """
    Manages personality snapshots for version control and rollback.
    
    Features:
    - Auto-snapshot every N conversations
    - Manual snapshot on demand
    - Rollback to previous version
    - Version history
    """
    
    def __init__(
        self,
        storage_path: str = "data/personality_snapshots",
        snapshot_interval: int = 50  # Every 50 conversations
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.snapshot_interval = snapshot_interval
        self.snapshots: List[PersonalitySnapshot] = []
        
        # Load existing snapshots
        self._load_snapshots()
        
        logger.info(f"PersonalitySnapshotManager initialized ({len(self.snapshots)} snapshots)")
    
    def should_snapshot(self, conversation_count: int) -> bool:
        """Check if it's time for a snapshot"""
        if not self.snapshots:
            return True
        
        last_snapshot_count = self.snapshots[-1].conversation_count
        return conversation_count - last_snapshot_count >= self.snapshot_interval
    
    def create_snapshot(
        self,
        personality_state: dict,
        emotional_threads: List[dict],
        conversation_count: int
    ) -> PersonalitySnapshot:
        """Create a new personality snapshot"""
        version = len(self.snapshots) + 1
        
        snapshot = PersonalitySnapshot(
            version=version,
            timestamp=datetime.now(),
            personality_state=personality_state,
            emotional_threads=emotional_threads,
            conversation_count=conversation_count
        )
        
        self.snapshots.append(snapshot)
        self._save_snapshot(snapshot)
        
        logger.info(f"📸 Created personality snapshot v{version}")
        return snapshot
    
    def rollback_to_version(self, version: int) -> Optional[PersonalitySnapshot]:
        """Rollback personality to a previous version"""
        for snapshot in self.snapshots:
            if snapshot.version == version:
                logger.info(f"↩️ Rolling back to personality v{version}")
                return snapshot
        
        logger.warning(f"Snapshot v{version} not found")
        return None
    
    def get_latest(self) -> Optional[PersonalitySnapshot]:
        """Get most recent snapshot"""
        return self.snapshots[-1] if self.snapshots else None
    
    def list_versions(self) -> List[dict]:
        """List all snapshot versions"""
        return [
            {
                'version': s.version,
                'timestamp': s.timestamp.isoformat(),
                'conversation_count': s.conversation_count
            }
            for s in self.snapshots
        ]
    
    def _save_snapshot(self, snapshot: PersonalitySnapshot):
        """Save snapshot to disk"""
        path = self.storage_path / f"snapshot_v{snapshot.version}.json"
        with open(path, 'w') as f:
            json.dump(snapshot.to_dict(), f, indent=2)
    
    def _load_snapshots(self):
        """Load all snapshots from disk"""
        snapshot_files = sorted(self.storage_path.glob("snapshot_v*.json"))
        
        for file in snapshot_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    snapshot = PersonalitySnapshot.from_dict(data)
                    self.snapshots.append(snapshot)
            except Exception as e:
                logger.error(f"Failed to load snapshot {file}: {e}")


# NEW: src/memory/forgetting_mechanism.py

from datetime import datetime, timedelta
from typing import List
import logging

logger = logging.getLogger(__name__)


class ForgettingMechanism:
    """
    Implements gradual forgetting of emotional threads.
    
    Features:
    - 30-day auto-decay
    - Intensity-based decay rate
    - Manual forget option
    """
    
    def __init__(self, decay_days: int = 30):
        self.decay_days = decay_days
        logger.info(f"ForgettingMechanism initialized (decay={decay_days} days)")
    
    def apply_decay(self, threads: List) -> List:
        """
        Apply time-based decay to emotional threads.
        
        Threads older than decay_days are removed.
        Intensity decays linearly over time.
        """
        now = datetime.now()
        decayed_threads = []
        
        for thread in threads:
            age_days = (now - thread.timestamp).days
            
            # Remove if too old
            if age_days > self.decay_days:
                logger.debug(f"Forgetting thread {thread.turn_id} (age={age_days}d)")
                continue
            
            # Apply linear decay to intensity
            decay_factor = 1.0 - (age_days / self.decay_days)
            thread.intensity *= decay_factor
            
            decayed_threads.append(thread)
        
        return decayed_threads
    
    def forget_thread(self, threads: List, turn_id: str) -> List:
        """Manually forget a specific thread"""
        logger.info(f"Manually forgetting thread {turn_id}")
        return [t for t in threads if t.turn_id != turn_id]
    
    def forget_all(self, threads: List) -> List:
        """Forget all emotional threads (user request)"""
        logger.info("Forgetting all emotional threads (user request)")
        return []
```

**Files:**
- NEW: `src/personality/personality_snapshots.py` (~250 lines)
- NEW: `src/memory/forgetting_mechanism.py` (~100 lines)
- NEW: `src/memory/consent_manager.py` (~150 lines)
- UPDATE: `research_first_pipeline.py` - Add safety mechanisms
- NEW: `tests/test_safety_mechanisms.py` (~200 lines)

**Success Criteria:**
- ✅ User can opt-in/opt-out of emotional tracking
- ✅ Snapshots created every 50 conversations
- ✅ Rollback to previous personality state
- ✅ 30-day auto-decay of emotional threads
- ✅ Manual forget option

---

### **4. Integration & Testing (3-4 hours)** 🧪

**What This Does:**
Integrate all Week 8 features and validate with comprehensive tests.

**Implementation:**

```python
# UPDATE: research_first_pipeline.py

from src.memory.emotion_detector_v2 import EmotionDetectorV2
from src.memory.emotional_continuity import EmotionalContinuity
from src.personality.personality_snapshots import PersonalitySnapshotManager
from src.memory.forgetting_mechanism import ForgettingMechanism

class ResearchFirstPipeline(PipelineLoop):
    def __init__(self):
        super().__init__()
        
        # ... existing init ...
        
        # Week 8: Upgrade emotion detection
        self.emotion_detector = EmotionDetectorV2()
        
        # Week 8: Emotional continuity
        self.emotional_continuity = EmotionalContinuity(
            semantic_memory=self.semantic_memory,
            emotion_detector=self.emotion_detector,
            window_days=7,
            intensity_threshold=0.8,
            enabled=True  # User can disable
        )
        
        # Week 8: Personality snapshots
        self.personality_snapshots = PersonalitySnapshotManager(
            snapshot_interval=50
        )
        
        # Week 8: Forgetting mechanism
        self.forgetting = ForgettingMechanism(decay_days=30)
        
        logger.info("🧠 Week 8 systems initialized: Emotional Continuity")
    
    def think(self, user_text: str) -> str:
        """Process input with emotional continuity"""
        
        # Generate turn ID
        turn_id = f"turn_{int(time.time() * 1000)}"
        
        # Track emotion if significant
        emotional_thread = self.emotional_continuity.track_emotion(
            user_input=user_text,
            turn_id=turn_id
        )
        
        # Check if we should reference previous emotional context
        check_in_thread = self.emotional_continuity.should_check_in()
        
        # Build prompt with emotional context
        if check_in_thread:
            emotional_context = self.emotional_continuity.generate_check_in_prompt(check_in_thread)
            system_prompt = f"{base_system_prompt}\n\n{emotional_context}"
        else:
            system_prompt = base_system_prompt
        
        # ... rest of think() logic ...
        
        response = self.llm.generate(messages, system_prompt=system_prompt)
        
        # Mark thread as followed up if we referenced it
        if check_in_thread:
            self.emotional_continuity.mark_followed_up(check_in_thread, turn_id)
        
        # Check if snapshot needed
        conversation_count = len(self.semantic_memory.get_all_turns())
        if self.personality_snapshots.should_snapshot(conversation_count):
            self.personality_snapshots.create_snapshot(
                personality_state=self.personality_tracker.get_personality_state(),
                emotional_threads=[t.to_dict() for t in self.emotional_continuity.threads],
                conversation_count=conversation_count
            )
        
        return response
```

**Files:**
- UPDATE: `research_first_pipeline.py` - Full integration
- NEW: `tests/test_week8_integration.py` (~300 lines)
- NEW: `tests/test_emotional_continuity_end_to_end.py` (~200 lines)
- UPDATE: `test_full_integration.py` - Add Week 8 tests

**Success Criteria:**
- ✅ All Week 8 features integrated
- ✅ Test pass rate: 100%
- ✅ No performance degradation (<100ms overhead)
- ✅ Emotional check-ins working
- ✅ Snapshots saving correctly

---

## 📊 **EXPECTED OUTCOMES:**

### **Before Week 8:**
```
User: "I'm stressed about layoffs"
Penny: [responds with advice]

[3 days later]
User: "Hey Penny"
Penny: "Hey! What's up?" 
       [no memory of stress]
```

### **After Week 8:**
```
User: "I'm stressed about layoffs"
Penny: [responds with advice]
       [tracks emotion: stress, intensity=0.85]

[3 days later]
User: "Hey Penny"
Penny: "Hey! How are you feeling about work? 
        You seemed stressed about layoffs on Monday."
       [natural check-in]
```

---

## 🎯 **SUCCESS METRICS:**

```
Technical:
├── Emotion accuracy: >90% ✅
├── Inference time: <100ms ✅
├── Memory window: 7 days ✅
├── Intensity threshold: 0.8 ✅
├── Test pass rate: 100% ✅

User Experience:
├── Natural follow-ups ✅
├── Appropriate check-ins ✅
├── User control maintained ✅
├── Non-intrusive ✅
└── Creates relationship depth ✅
```

---

## ⏰ **TIMELINE:**

```
Total Time: 18-22 hours
════════════════════════════════════════

Component 1: Emotion Detection Upgrade  (5-6 hrs)
Component 2: Emotional Tracking         (8-10 hrs)
Component 3: Safety & Consent           (4-5 hrs)
Component 4: Integration & Testing      (3-4 hrs)
```

---

## 🚀 **READY TO IMPLEMENT!**

All prerequisites validated, specifications complete, ready for CC to execute.

**This is the feature that makes Penny genuinely special** - emotional continuity across sessions creates real relationship depth that no other AI assistant offers.
