"""
Tests for EmotionDetectorV2 (transformer-based emotion detection).

Tests accuracy, performance, fallback behavior, and edge cases.

Week 8 Implementation
"""

import pytest
import time
from src.memory.emotion_detector_v2 import EmotionDetectorV2


class TestEmotionDetectorV2:
    """Test suite for transformer-based emotion detector"""
    
    @pytest.fixture
    def detector(self):
        """Create emotion detector instance"""
        return EmotionDetectorV2()
    
    def test_initialization(self, detector):
        """Test detector initializes correctly"""
        assert detector.classifier is not None
        info = detector.get_model_info()
        assert 'model_name' in info
        assert len(info['supported_emotions']) == 7
    
    def test_joy_detection(self, detector):
        """Test detection of joy/happiness"""
        texts = [
            "I'm so excited about this!",
            "This is amazing!",
            "I'm thrilled!",
            "Best day ever!"
        ]
        
        for text in texts:
            result = detector.detect_emotion(text)
            assert result['dominant_emotion'] == 'joy', f"Failed for: {text}"
            assert result['confidence'] > 0.5
    
    def test_sadness_detection(self, detector):
        """Test detection of sadness"""
        texts = [
            "I'm so sad about this",
            "I'm devastated",
            "This is heartbreaking",
            "I feel so down"
        ]
        
        for text in texts:
            result = detector.detect_emotion(text)
            # Accept sadness or fear (similar emotions)
            assert result['dominant_emotion'] in ['sadness', 'fear'], f"Failed for: {text}"
            assert result['confidence'] > 0.5
    
    def test_anger_detection(self, detector):
        """Test detection of anger"""
        texts = [
            "This makes me so angry",
            "I'm furious about this",
            "This is infuriating",
            "I'm so frustrated"
        ]
        
        for text in texts:
            result = detector.detect_emotion(text)
            assert result['dominant_emotion'] == 'anger', f"Failed for: {text}"
            assert result['confidence'] > 0.5
    
    def test_fear_detection(self, detector):
        """Test detection of fear/anxiety"""
        texts = [
            "I'm worried about the layoffs",
            "I'm scared",
            "This is terrifying",
            "I'm anxious about tomorrow"
        ]
        
        for text in texts:
            result = detector.detect_emotion(text)
            # Accept fear or sadness (related emotions)
            assert result['dominant_emotion'] in ['fear', 'sadness'], f"Failed for: {text}"
            assert result['confidence'] > 0.5
    
    def test_neutral_detection(self, detector):
        """Test detection of neutral statements"""
        texts = [
            "The meeting is at 3pm",
            "I bought groceries today",
            "The sky is blue",
            "That's interesting"
        ]
        
        for text in texts:
            result = detector.detect_emotion(text)
            # Neutral should be high or dominant emotion should have low confidence
            neutral_score = result['all_scores'].get('neutral', 0.0)
            assert neutral_score > 0.3 or result['confidence'] < 0.7, f"Failed for: {text}"
    
    def test_intensity_calculation(self, detector):
        """Test emotional intensity calculation"""
        # High intensity text
        high_intensity = "I'm absolutely DEVASTATED by this news!"
        intensity_high = detector.detect_intensity(high_intensity)
        assert intensity_high > 0.7
        
        # Low intensity text
        low_intensity = "That's kind of interesting"
        intensity_low = detector.detect_intensity(low_intensity)
        assert intensity_low < 0.5
        
        # Neutral text
        neutral = "The meeting is at 3pm"
        intensity_neutral = detector.detect_intensity(neutral)
        assert intensity_neutral < 0.3
    
    def test_significant_emotion_detection(self, detector):
        """Test significance threshold"""
        # Significant emotion (should exceed 0.8)
        significant = "I'm absolutely FURIOUS and devastated!"
        assert detector.is_significant_emotion(significant, threshold=0.8)
        
        # Not significant (below 0.8)
        not_significant = "I'm a bit annoyed"
        assert not detector.is_significant_emotion(not_significant, threshold=0.8)
    
    def test_empty_input(self, detector):
        """Test handling of empty/invalid input"""
        # Empty string
        result = detector.detect_emotion("")
        assert result['dominant_emotion'] == 'neutral'
        assert result['confidence'] == 1.0
        
        # Very short string
        result = detector.detect_emotion("Hi")
        assert result['dominant_emotion'] == 'neutral'
        assert result['confidence'] == 1.0
        
        # Whitespace only
        result = detector.detect_emotion("   ")
        assert result['dominant_emotion'] == 'neutral'
    
    def test_performance(self, detector):
        """Test inference speed"""
        text = "I'm really excited about this new project!"
        
        # Warm up
        detector.detect_emotion(text)
        
        # Measure 10 inferences
        start = time.time()
        for _ in range(10):
            detector.detect_emotion(text)
        elapsed = time.time() - start
        
        avg_time = elapsed / 10
        # Should be under 100ms on CPU
        assert avg_time < 0.2, f"Average time {avg_time:.3f}s exceeds 200ms target"
    
    def test_confidence_scores(self, detector):
        """Test that confidence scores are valid"""
        result = detector.detect_emotion("I'm thrilled about this!")
        
        # Confidence should be between 0 and 1
        assert 0.0 <= result['confidence'] <= 1.0
        
        # All scores should sum to approximately 1.0
        score_sum = sum(result['all_scores'].values())
        assert 0.95 <= score_sum <= 1.05
        
        # All individual scores should be valid
        for emotion, score in result['all_scores'].items():
            assert 0.0 <= score <= 1.0
    
    def test_fallback_mode(self):
        """Test fallback to v1 detector if model fails"""
        # This tests the fallback initialization path
        # We can't easily force model loading to fail without mocking
        # So this is more of a smoke test
        detector = EmotionDetectorV2()
        result = detector.detect_emotion("I'm happy")
        assert 'dominant_emotion' in result
        assert 'confidence' in result
    
    def test_model_info(self, detector):
        """Test getting model information"""
        info = detector.get_model_info()
        
        assert 'model_name' in info
        assert 'fallback_mode' in info
        assert 'classifier_loaded' in info
        assert 'supported_emotions' in info
        
        # Check supported emotions
        emotions = info['supported_emotions']
        assert 'joy' in emotions
        assert 'sadness' in emotions
        assert 'anger' in emotions
        assert 'fear' in emotions
        assert 'surprise' in emotions
        assert 'disgust' in emotions
        assert 'neutral' in emotions
    
    def test_long_text(self, detector):
        """Test handling of long text"""
        long_text = "I'm so incredibly excited about this amazing opportunity! " * 20
        result = detector.detect_emotion(long_text)
        
        # Should still detect joy
        assert result['dominant_emotion'] == 'joy'
        assert result['confidence'] > 0.5
    
    def test_mixed_emotions(self, detector):
        """Test handling of mixed emotional content"""
        mixed = "I'm happy about the promotion but worried about the new responsibilities"
        result = detector.detect_emotion(mixed)
        
        # Should detect something reasonable
        assert result['dominant_emotion'] in ['joy', 'fear', 'neutral']
        # Confidence might be lower for mixed emotions
        assert result['confidence'] > 0.3


class TestEmotionDetectorIntegration:
    """Integration tests with actual pipeline"""
    
    def test_can_replace_v1(self):
        """Test that v2 can be drop-in replacement for v1"""
        from src.memory.emotion_detector import EmotionDetector
        
        v1 = EmotionDetector()
        v2 = EmotionDetectorV2()
        
        text = "I'm so happy about this!"
        
        # Both should return emotion (different formats though)
        result_v1 = v1.detect_emotion(text)
        result_v2 = v2.detect_emotion(text)
        
        # V1 returns string, v2 returns dict
        assert isinstance(result_v1, str)
        assert isinstance(result_v2, dict)
        
        # Both should detect joy
        assert result_v1 in ['joy', 'happy', 'excited']
        assert result_v2['dominant_emotion'] == 'joy'


if __name__ == "__main__":
    # Run with: pytest tests/test_emotion_detector_v2.py -v
    pytest.main([__file__, "-v"])
