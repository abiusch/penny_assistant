"""
Emotion Detector for Text Analysis
Detects emotional state and sentiment from text using keyword/pattern matching
"""

from dataclasses import dataclass
from typing import Tuple, List, Dict, Any
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmotionResult:
    """Result of emotion detection"""
    primary_emotion: str  # joy, sadness, anger, fear, surprise, neutral
    confidence: float  # 0.0 to 1.0
    sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1.0 to 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'primary_emotion': self.primary_emotion,
            'confidence': self.confidence,
            'sentiment': self.sentiment,
            'sentiment_score': self.sentiment_score
        }


class EmotionDetector:
    """Detects emotions and sentiment from text using keyword matching"""

    # Emotion keyword dictionaries
    EMOTION_KEYWORDS = {
        'joy': [
            'happy', 'great', 'awesome', 'excellent', 'wonderful', 'fantastic',
            'love', 'excited', 'thrilled', 'delighted', 'pleased', 'glad',
            'cheerful', 'joyful', 'amazing', 'brilliant', 'perfect', 'yay',
            '😊', '😄', '😃', '🎉', '❤️', '😍'
        ],
        'sadness': [
            'sad', 'unhappy', 'depressed', 'disappointed', 'miserable', 'down',
            'unfortunate', 'sorry', 'regret', 'miss', 'lonely', 'hurt',
            'crying', 'tears', 'heartbroken', 'devastated', 'grief',
            '😢', '😭', '😞', '☹️'
        ],
        'anger': [
            'angry', 'mad', 'furious', 'annoyed', 'frustrated', 'irritated',
            'rage', 'hate', 'disgusted', 'outraged', 'pissed', 'upset',
            'annoying', 'terrible', 'awful', 'horrible', 'worst', 'stupid',
            '😠', '😡', '🤬'
        ],
        'fear': [
            'afraid', 'scared', 'worried', 'anxious', 'nervous', 'terrified',
            'fear', 'panic', 'frightened', 'concerned', 'stress', 'tense',
            'alarmed', 'uneasy', 'dread', 'horror',
            '😨', '😰', '😱'
        ],
        'surprise': [
            'surprised', 'shocked', 'amazed', 'astonished', 'unexpected',
            'wow', 'whoa', 'omg', 'unbelievable', 'incredible', 'stunning',
            'mind-blowing', 'surprising', 'startled',
            '😲', '😮', '🤯'
        ]
    }

    # Sentiment word lists
    POSITIVE_WORDS = [
        'good', 'great', 'excellent', 'wonderful', 'fantastic', 'amazing',
        'love', 'like', 'enjoy', 'happy', 'best', 'perfect', 'nice',
        'beautiful', 'awesome', 'brilliant', 'pleased', 'glad', 'thanks',
        'helpful', 'useful', 'appreciate', 'yes', 'sure', 'absolutely'
    ]

    NEGATIVE_WORDS = [
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'dislike',
        'sad', 'angry', 'no', 'not', 'never', 'problem', 'issue', 'wrong',
        'fail', 'failed', 'error', 'difficult', 'hard', 'annoying',
        'frustrating', 'disappointed', 'unfortunately', 'sorry'
    ]

    # Intensifiers (multiply emotion score)
    INTENSIFIERS = {
        'very': 1.5,
        'really': 1.5,
        'extremely': 2.0,
        'incredibly': 2.0,
        'absolutely': 1.8,
        'totally': 1.7,
        'completely': 1.8,
        'so': 1.4,
        'quite': 1.3
    }

    def __init__(self):
        """Initialize emotion detector"""
        logger.info("Initialized EmotionDetector with keyword-based matching")

    def detect_emotion(self, text: str) -> EmotionResult:
        """
        Detect primary emotion from text.

        Args:
            text: Text to analyze

        Returns:
            EmotionResult with emotion, confidence, and sentiment
        """
        if not text or not text.strip():
            return EmotionResult(
                primary_emotion='neutral',
                confidence=1.0,
                sentiment='neutral',
                sentiment_score=0.0
            )

        text_lower = text.lower()

        # Count emotion keyword matches
        emotion_scores = {}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Base score
                    match_score = 1.0

                    # Check for intensifiers before the keyword
                    for intensifier, multiplier in self.INTENSIFIERS.items():
                        pattern = rf'\b{intensifier}\s+\w*{keyword}'
                        if re.search(pattern, text_lower):
                            match_score *= multiplier

                    score += match_score

            if score > 0:
                emotion_scores[emotion] = score

        # Determine primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores, key=emotion_scores.get)
            max_score = emotion_scores[primary_emotion]

            # Calculate confidence (normalize by total score)
            total_score = sum(emotion_scores.values())
            confidence = min(max_score / (total_score + 1), 1.0)
        else:
            primary_emotion = 'neutral'
            confidence = 0.8  # High confidence in neutral when no emotion keywords

        # Get sentiment
        sentiment, sentiment_score = self.get_sentiment(text)

        return EmotionResult(
            primary_emotion=primary_emotion,
            confidence=confidence,
            sentiment=sentiment,
            sentiment_score=sentiment_score
        )

    def get_sentiment(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of text.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (sentiment_label, sentiment_score)
            sentiment_label: 'positive', 'negative', or 'neutral'
            sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
        """
        if not text or not text.strip():
            return ('neutral', 0.0)

        text_lower = text.lower()

        # Count positive and negative words
        positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text_lower)

        # Check for negations (flip polarity)
        negation_patterns = [
            r'\bnot\s+\w+',
            r"\bdon't\s+\w+",
            r"\bdoesn't\s+\w+",
            r"\bdidn't\s+\w+",
            r"\bwon't\s+\w+",
            r"\bcan't\s+\w+",
            r"\bnever\s+\w+"
        ]

        has_negation = any(re.search(pattern, text_lower) for pattern in negation_patterns)

        # If negation detected, reduce positive sentiment
        if has_negation and positive_count > 0:
            positive_count = max(0, positive_count - 1)
            negative_count += 0.5

        # Calculate sentiment score
        total_words = positive_count + negative_count

        if total_words == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = (positive_count - negative_count) / (total_words + 1)

        # Determine sentiment label
        if sentiment_score > 0.2:
            sentiment = 'positive'
        elif sentiment_score < -0.2:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'

        # Clamp score to [-1, 1]
        sentiment_score = max(-1.0, min(1.0, sentiment_score))

        return (sentiment, sentiment_score)

    def analyze_emotional_trajectory(self, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze emotional trajectory over multiple conversation turns.

        Args:
            turns: List of conversation turns with 'user_input' and 'assistant_response'

        Returns:
            Dictionary with trajectory analysis
        """
        if not turns:
            return {
                'emotions': [],
                'sentiments': [],
                'overall_trend': 'neutral',
                'emotional_variance': 0.0
            }

        emotions = []
        sentiments = []
        sentiment_scores = []

        for turn in turns:
            # Analyze user input
            user_text = turn.get('user_input', '')
            if user_text:
                result = self.detect_emotion(user_text)
                emotions.append(result.primary_emotion)
                sentiments.append(result.sentiment)
                sentiment_scores.append(result.sentiment_score)

        # Calculate overall trend
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            if avg_sentiment > 0.2:
                overall_trend = 'improving'
            elif avg_sentiment < -0.2:
                overall_trend = 'declining'
            else:
                overall_trend = 'stable'

            # Calculate emotional variance (how much emotions change)
            if len(sentiment_scores) > 1:
                variance = sum((s - avg_sentiment) ** 2 for s in sentiment_scores) / len(sentiment_scores)
                emotional_variance = variance ** 0.5  # Standard deviation
            else:
                emotional_variance = 0.0
        else:
            overall_trend = 'neutral'
            emotional_variance = 0.0

        return {
            'emotions': emotions,
            'sentiments': sentiments,
            'sentiment_scores': sentiment_scores,
            'overall_trend': overall_trend,
            'emotional_variance': round(emotional_variance, 3)
        }

    def get_dominant_emotion(self, turns: List[Dict[str, Any]]) -> Tuple[str, float]:
        """
        Get the dominant emotion across multiple turns.

        Args:
            turns: List of conversation turns

        Returns:
            Tuple of (emotion, frequency)
        """
        emotions = []

        for turn in turns:
            user_text = turn.get('user_input', '')
            if user_text:
                result = self.detect_emotion(user_text)
                emotions.append(result.primary_emotion)

        if not emotions:
            return ('neutral', 1.0)

        # Count emotion frequencies
        emotion_counts = {}
        for emotion in emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        # Find most common
        dominant = max(emotion_counts, key=emotion_counts.get)
        frequency = emotion_counts[dominant] / len(emotions)

        return (dominant, frequency)
