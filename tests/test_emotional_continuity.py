"""
Comprehensive tests for Week 8 Emotional Continuity system.

Tests all components: emotion detection, tracking, snapshots, forgetting, consent.

Week 8 Implementation
"""

import pytest
from datetime import datetime, timedelta
from src.memory.emotion_detector_v2 import EmotionDetectorV2
from src.memory.emotional_continuity import EmotionalContinuity, EmotionalThread
from src.personality.personality_snapshots import PersonalitySnapshotManager
from src.memory.forgetting_mechanism import ForgettingMechanism
from src.memory.consent_manager import ConsentManager
from src.memory.semantic_memory import SemanticMemory


class TestEmotionalContinuityIntegration:
    """Integration tests for the full emotional continuity system"""
    
    @pytest.fixture
    def setup_system(self):
        """Setup complete emotional continuity system"""
        detector = EmotionDetectorV2()
        memory = SemanticMemory()
        tracker = EmotionalContinuity(
            semantic_memory=memory,
            emotion_detector=detector,
            window_days=7,
            intensity_threshold=0.8,
            enabled=True
        )
        consent = ConsentManager(storage_path="data/test_consent.json")
        forgetting = ForgettingMechanism(decay_days=30)
        snapshots = PersonalitySnapshotManager(
            storage_path="data/test_snapshots",
            snapshot_interval=50
        )
        
        return {
            'detector': detector,
            'memory': memory,
            'tracker': tracker,
            'consent': consent,
            'forgetting': forgetting,
            'snapshots': snapshots
        }
    
    def test_track_significant_emotion(self, setup_system):
        """Test tracking a significant emotional moment"""
        sys = setup_system
        
        # Track strong emotion
        thread = sys['tracker'].track_emotion(
            user_input="I'm absolutely devastated about the layoffs",
            turn_id="turn_001"
        )
        
        # Should create a thread
        assert thread is not None
        assert thread.emotion in ['sadness', 'fear', 'anger']
        assert thread.intensity >= 0.8
        assert "devastated" in thread.context.lower()
    
    def test_ignore_weak_emotion(self, setup_system):
        """Test that weak emotions are not tracked"""
        sys = setup_system
        
        # Track weak emotion
        thread = sys['tracker'].track_emotion(
            user_input="That's kind of interesting",
            turn_id="turn_002"
        )
        
        # Should NOT create a thread
        assert thread is None
    
    def test_check_in_suggestion(self, setup_system):
        """Test proactive check-in suggestions"""
        sys = setup_system
        
        # Create a significant emotional thread
        sys['tracker'].track_emotion(
            user_input="I'm so worried about my job interview tomorrow",
            turn_id="turn_003"
        )
        
        # Should suggest check-in
        check_in_thread = sys['tracker'].should_check_in()
        assert check_in_thread is not None
        assert check_in_thread.emotion in ['fear', 'anxiety', 'sadness']
    
    def test_check_in_prompt_generation(self, setup_system):
        """Test generating natural check-in prompts"""
        sys = setup_system
        
        # Create thread from "yesterday"
        thread = EmotionalThread(
            emotion='stress',
            intensity=0.85,
            context="Worried about project deadline",
            timestamp=datetime.now() - timedelta(days=1),
            turn_id="turn_004"
        )
        
        # Generate prompt
        prompt = sys['tracker'].generate_check_in_prompt(thread)
        
        # Should mention emotion and time
        assert 'stress' in prompt.lower() or 'worried' in prompt.lower()
        assert 'yesterday' in prompt.lower() or '1 day' in prompt.lower()
    
    def test_mark_followed_up(self, setup_system):
        """Test marking threads as followed up"""
        sys = setup_system
        
        # Create thread
        thread = sys['tracker'].track_emotion(
            user_input="I'm so excited about the promotion!",
            turn_id="turn_005"
        )
        
        # Mark as followed up
        sys['tracker'].mark_followed_up(thread, "turn_006")
        
        # Should have follow-up recorded
        assert "turn_006" in thread.follow_ups
        
        # Should no longer suggest check-in (already followed up)
        check_in = sys['tracker'].should_check_in()
        assert check_in is None
    
    def test_decay_mechanism(self, setup_system):
        """Test time-based decay of emotional threads"""
        sys = setup_system
        
        # Create old thread
        old_thread = EmotionalThread(
            emotion='anger',
            intensity=0.9,
            context="So frustrated",
            timestamp=datetime.now() - timedelta(days=15),
            turn_id="turn_007"
        )
        
        # Apply decay
        decayed = sys['forgetting'].apply_decay([old_thread])
        
        # Intensity should be reduced
        assert len(decayed) == 1
        assert decayed[0].intensity < 0.9
        assert decayed[0].intensity > 0  # Not completely gone yet
    
    def test_forget_old_threads(self, setup_system):
        """Test removing very old threads"""
        sys = setup_system
        
        # Create very old thread (35 days)
        old_thread = EmotionalThread(
            emotion='joy',
            intensity=0.85,
            context="Happy memory",
            timestamp=datetime.now() - timedelta(days=35),
            turn_id="turn_008"
        )
        
        # Apply decay (30-day threshold)
        decayed = sys['forgetting'].apply_decay([old_thread])
        
        # Should be completely removed
        assert len(decayed) == 0
    
    def test_manual_forget(self, setup_system):
        """Test manually forgetting a thread"""
        sys = setup_system
        
        # Create threads
        thread1 = EmotionalThread(
            emotion='sadness',
            intensity=0.8,
            context="Sad about X",
            timestamp=datetime.now(),
            turn_id="turn_009"
        )
        thread2 = EmotionalThread(
            emotion='joy',
            intensity=0.85,
            context="Happy about Y",
            timestamp=datetime.now(),
            turn_id="turn_010"
        )
        
        threads = [thread1, thread2]
        
        # Forget specific thread
        filtered = sys['forgetting'].forget_thread(threads, "turn_009")
        
        # Should only have one thread left
        assert len(filtered) == 1
        assert filtered[0].turn_id == "turn_010"
    
    def test_personality_snapshot_creation(self, setup_system):
        """Test creating personality snapshots"""
        sys = setup_system
        
        # Should create snapshot at conversation 50
        assert sys['snapshots'].should_snapshot(50)
        
        # Create snapshot
        snapshot = sys['snapshots'].create_snapshot(
            personality_state={'formality': 0.3, 'sarcasm': 0.6},
            emotional_threads=[],
            conversation_count=50
        )
        
        assert snapshot.version == 1
        assert snapshot.conversation_count == 50
    
    def test_personality_rollback(self, setup_system):
        """Test rolling back personality to previous version"""
        sys = setup_system
        
        # Create two snapshots
        s1 = sys['snapshots'].create_snapshot(
            personality_state={'formality': 0.3},
            emotional_threads=[],
            conversation_count=50
        )
        s2 = sys['snapshots'].create_snapshot(
            personality_state={'formality': 0.5},
            emotional_threads=[],
            conversation_count=100
        )
        
        # Rollback to v1
        restored = sys['snapshots'].rollback_to_version(1)
        
        assert restored is not None
        assert restored.personality_state['formality'] == 0.3
    
    def test_consent_management(self, setup_system):
        """Test user consent workflow"""
        sys = setup_system
        
        # Initially disabled
        assert not sys['consent'].is_tracking_enabled()
        
        # Grant consent
        sys['consent'].grant_consent(
            emotional_tracking=True,
            proactive_checkins=True
        )
        
        assert sys['consent'].is_tracking_enabled()
        assert sys['consent'].is_checkins_enabled()
        
        # Revoke consent
        sys['consent'].revoke_consent()
        
        assert not sys['consent'].is_tracking_enabled()
    
    def test_consent_preferences(self, setup_system):
        """Test updating consent preferences"""
        sys = setup_system
        
        # Grant consent first
        sys['consent'].grant_consent(emotional_tracking=True)
        
        # Update preferences
        sys['consent'].update_preferences(
            intensity_threshold=0.9,
            memory_window_days=14
        )
        
        assert sys['consent'].get_intensity_threshold() == 0.9
        assert sys['consent'].get_memory_window() == 14
    
    def test_full_workflow(self, setup_system):
        """Test complete workflow from emotion to check-in"""
        sys = setup_system
        
        # 1. User grants consent
        sys['consent'].grant_consent(emotional_tracking=True, proactive_checkins=True)
        
        # 2. Strong emotion is expressed
        thread = sys['tracker'].track_emotion(
            user_input="I'm so stressed about this deadline!",
            turn_id="turn_011"
        )
        assert thread is not None
        
        # 3. System suggests check-in
        check_in = sys['tracker'].should_check_in()
        assert check_in is not None
        
        # 4. Generate natural prompt
        prompt = sys['tracker'].generate_check_in_prompt(check_in)
        assert 'stress' in prompt.lower()
        
        # 5. Mark as followed up
        sys['tracker'].mark_followed_up(check_in, "turn_012")
        
        # 6. No longer suggests same check-in
        next_check_in = sys['tracker'].should_check_in()
        assert next_check_in is None


class TestEmotionalContinuityEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def tracker(self):
        """Create basic tracker for edge case testing"""
        detector = EmotionDetectorV2()
        memory = SemanticMemory()
        return EmotionalContinuity(
            semantic_memory=memory,
            emotion_detector=detector,
            enabled=True
        )
    
    def test_disabled_tracking(self, tracker):
        """Test that tracking respects enabled flag"""
        tracker.enabled = False
        
        thread = tracker.track_emotion(
            "I'm devastated!",
            "turn_013"
        )
        
        assert thread is None
    
    def test_empty_input(self, tracker):
        """Test handling empty input"""
        thread = tracker.track_emotion("", "turn_014")
        assert thread is None
    
    def test_very_long_context(self, tracker):
        """Test context truncation"""
        long_text = "I'm stressed about this project " * 100
        
        thread = tracker.track_emotion(long_text, "turn_015")
        
        if thread:
            # Context should be truncated to 200 chars
            assert len(thread.context) <= 200
    
    def test_concurrent_threads(self, tracker):
        """Test handling multiple emotional threads"""
        # Create multiple significant emotions
        thread1 = tracker.track_emotion(
            "I'm so excited about the promotion!",
            "turn_016"
        )
        thread2 = tracker.track_emotion(
            "But I'm worried about the new responsibilities",
            "turn_017"
        )
        
        # Both should be tracked
        recent = tracker.get_recent_threads()
        assert len(recent) >= 2
    
    def test_memory_window_boundary(self, tracker):
        """Test memory window cutoff"""
        # Create thread exactly at window boundary
        old_thread = EmotionalThread(
            emotion='joy',
            intensity=0.85,
            context="Happy",
            timestamp=datetime.now() - timedelta(days=7, hours=1),
            turn_id="turn_018"
        )
        
        tracker.threads.append(old_thread)
        
        # Should not appear in recent (outside 7-day window)
        recent = tracker.get_recent_threads()
        assert old_thread not in recent


if __name__ == "__main__":
    # Run with: pytest tests/test_emotional_continuity.py -v
    pytest.main([__file__, "-v"])
