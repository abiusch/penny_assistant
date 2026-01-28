"""
Hebbian Sequence Learner
Learns sequential patterns in conversation states to anticipate user needs
Week 9 Day 6-7: Conversation flow pattern learning
"""

import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import re
import logging

from .hebbian_types import (
    StateTransition,
    StateSequence,
    PatternTemplate,
    SkipOpportunity,
    AnticipatedResponse,
    ConversationState,
    DEFAULT_PATTERN_THRESHOLD
)

logger = logging.getLogger(__name__)


# State classification rules
STATE_INDICATORS = {
    'problem_statement': {
        'keywords': ['stuck', 'error', 'broken', 'bug', 'issue', 'problem', 'fail', 'crash', 'wrong', 'doesn\'t work'],
        'patterns': [r'\?$', r'why (is|does|doesn\'t)', r'how (do|can|should)'],
        'priority': 1
    },
    'clarification_question': {
        'keywords': ['what do you mean', 'can you explain', 'i don\'t understand', 'what is', 'huh', 'confused'],
        'patterns': [r'\?\s*$', r'what (do|did|does|is)', r'could you clarify'],
        'priority': 2
    },
    'simplified_explanation': {
        'keywords': ['simpler', 'eli5', 'easier', 'simple terms', 'dumb it down', 'in english'],
        'patterns': [r'can you (simplify|explain.+simpler)', r'too (complex|complicated)'],
        'priority': 3
    },
    'positive_feedback': {
        'keywords': ['thanks', 'thank you', 'perfect', 'great', 'awesome', 'nice', 'works', 'got it', 'makes sense'],
        'patterns': [r'^(thanks|thank you|thx)', r'!$'],
        'priority': 4
    },
    'frustration_expression': {
        'keywords': ['ugh', 'argh', 'ffs', 'wtf', 'still broken', 'still not working', 'frustrated'],
        'patterns': [r'(!{2,}|\.{3,})', r'still (not|doesn\'t|won\'t)'],
        'priority': 5
    },
    'follow_up_question': {
        'keywords': ['also', 'another question', 'what about', 'and', 'one more thing'],
        'patterns': [r'^(and|also|what about)', r'\?$'],
        'priority': 6
    },
    'code_review': {
        'keywords': ['review', 'check', 'look at', 'this code', 'my code'],
        'patterns': [r'```', r'review (this|my)'],
        'priority': 7
    },
    'debugging_help': {
        'keywords': ['debug', 'trace', 'log', 'stack trace', 'exception', 'traceback'],
        'patterns': [r'exception|traceback|error:', r'line \d+'],
        'priority': 8
    },
    'opinion_request': {
        'keywords': ['what do you think', 'your opinion', 'should i', 'best practice', 'recommend'],
        'patterns': [r'what (do you think|would you)', r'should (i|we)'],
        'priority': 9
    },
    'technical_explanation': {
        'keywords': ['explain', 'how does', 'why does', 'what happens'],
        'patterns': [r'how (does|do)', r'explain (how|why|what)'],
        'priority': 10
    },
    'casual_chat': {
        'keywords': ['hey', 'hi', 'hello', 'sup', 'yo', 'ngl', 'tbh'],
        'patterns': [r'^(hey|hi|hello|sup|yo)', r'(ngl|tbh|lol)'],
        'priority': 11
    },
    'correction_request': {
        'keywords': ['no that\'s wrong', 'incorrect', 'not what i meant', 'actually', 'no,'],
        'patterns': [r'^no[,.]?\s', r'that\'s (not|wrong)'],
        'priority': 12
    }
}


class HebbianSequenceLearner:
    """
    Learns conversation flow patterns through Markov chain transition learning

    Core Algorithm:
    1. Classify conversation states from messages
    2. Observe state transitions, update transition matrix
    3. Detect recurring sequences (n-grams)
    4. Identify skip opportunities (predictable intermediate states)
    5. Anticipate user needs based on patterns

    Example:
        >>> learner = HebbianSequenceLearner()
        >>> state = learner.classify_conversation_state("I'm stuck on this async code", {})
        >>> learner.observe_transition("problem_statement", "clarification_question")
        >>> predictions = learner.predict_next_states("clarification_question", [])
    """

    def __init__(
        self,
        db_path: str = "data/personality_tracking.db",
        pattern_threshold: int = DEFAULT_PATTERN_THRESHOLD
    ):
        """
        Initialize sequence learner

        Args:
            db_path: Path to SQLite database
            pattern_threshold: Minimum frequency to create pattern template
        """
        self.db_path = db_path
        self.pattern_threshold = pattern_threshold

        # Conversation state history (in-memory for current session)
        self.conversation_history: List[str] = []

        # Valid states
        self._valid_states = [e.value for e in ConversationState]

        # Initialize database
        self._init_db()

        logger.info(f"HebbianSequenceLearner initialized (pattern_threshold={pattern_threshold})")

    def _init_db(self) -> None:
        """Ensure database tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='conversation_state_transitions'
            """)
            if not cursor.fetchone():
                logger.warning("conversation_state_transitions table not found - schema may need to be applied")

    # ========================================================================
    # STATE CLASSIFICATION METHODS
    # ========================================================================

    def classify_conversation_state(
        self,
        message: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Classify message into conversation state

        Algorithm:
        1. Normalize message (lowercase)
        2. Check for explicit indicators (keywords, phrases)
        3. Check contextual clues (follow-up, sentiment)
        4. Use heuristics and regex patterns
        5. Return most confident classification

        Args:
            message: User's message text
            context: Contextual information (formality, mood, is_follow_up, etc.)

        Returns:
            str: Conversation state classification
        """
        if not message:
            return "casual_chat"

        context = context or {}
        message_lower = message.lower()

        # Score each state
        state_scores = defaultdict(float)

        for state, indicators in STATE_INDICATORS.items():
            score = 0.0

            # Check keywords
            for keyword in indicators['keywords']:
                if keyword in message_lower:
                    score += 1.0

            # Check patterns
            for pattern in indicators['patterns']:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    score += 0.8

            # Adjust by priority (lower = more important)
            priority = indicators['priority']
            if score > 0:
                score += (15 - priority) * 0.1

            state_scores[state] = score

        # Context adjustments
        if context.get('is_follow_up', False):
            state_scores['follow_up_question'] += 0.5

        if context.get('has_code', False):
            state_scores['code_review'] += 0.5
            state_scores['debugging_help'] += 0.3

        # Find best match
        if state_scores:
            best_state = max(state_scores, key=state_scores.get)
            if state_scores[best_state] > 0:
                return best_state

        # Default based on message characteristics
        if '?' in message:
            return 'follow_up_question'
        elif any(word in message_lower for word in ['help', 'please', 'need']):
            return 'problem_statement'
        else:
            return 'casual_chat'

    # ========================================================================
    # TRANSITION LEARNING METHODS
    # ========================================================================

    def observe_transition(
        self,
        state_from: str,
        state_to: str,
        satisfaction: Optional[float] = None,
        session_id: Optional[str] = None
    ) -> int:
        """
        Observe state transition, update transition matrix

        Algorithm:
        1. Increment transition count
        2. Recalculate transition probabilities for state_from
        3. Check if recent sequence forms a recurring pattern
        4. Update database

        Args:
            state_from: Previous conversation state
            state_to: Current conversation state
            satisfaction: Optional user satisfaction score (0.0-1.0)
            session_id: Optional session identifier

        Returns:
            int: Number of updates made
        """
        if not state_from or not state_to:
            return 0

        updates = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Update or insert transition
            cursor.execute("""
                INSERT INTO conversation_state_transitions
                (state_from, state_to, transition_count, avg_satisfaction, last_observed, first_observed)
                VALUES (?, ?, 1, ?, datetime('now'), datetime('now'))
                ON CONFLICT(state_from, state_to) DO UPDATE SET
                    transition_count = transition_count + 1,
                    avg_satisfaction = CASE
                        WHEN ? IS NOT NULL THEN
                            (avg_satisfaction * transition_count + ?) / (transition_count + 1)
                        ELSE avg_satisfaction
                    END,
                    last_observed = datetime('now')
            """, (state_from, state_to, satisfaction, satisfaction, satisfaction))

            # Recalculate probabilities for state_from
            cursor.execute("""
                SELECT state_to, transition_count
                FROM conversation_state_transitions
                WHERE state_from = ?
            """, (state_from,))

            transitions = cursor.fetchall()
            total_count = sum(t[1] for t in transitions)

            for target_state, count in transitions:
                probability = count / total_count if total_count > 0 else 0.0
                cursor.execute("""
                    UPDATE conversation_state_transitions
                    SET transition_probability = ?
                    WHERE state_from = ? AND state_to = ?
                """, (probability, state_from, target_state))
                updates += 1

            conn.commit()

        # Update conversation history
        self.conversation_history.append(state_to)

        # Check for sequence patterns
        if len(self.conversation_history) >= 3:
            self._check_for_sequence_pattern()

        return updates

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_transition_probability(
        self,
        state_from: str,
        state_to: str
    ) -> float:
        """
        Get probability of transitioning from one state to another

        Args:
            state_from: Source state
            state_to: Target state

        Returns:
            float: Transition probability (0.0-1.0)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT transition_probability
                FROM conversation_state_transitions
                WHERE state_from = ? AND state_to = ?
            """, (state_from, state_to))
            result = cursor.fetchone()
            return result[0] if result else 0.0

    def predict_next_states(
        self,
        current_state: str,
        history: Optional[List[str]] = None,
        n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Predict most likely next conversation states

        Args:
            current_state: Current conversation state
            history: Recent state history
            n: Number of top predictions to return

        Returns:
            List of (next_state, probability) tuples
        """
        history = history or []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT state_to, transition_probability
                FROM conversation_state_transitions
                WHERE state_from = ?
                ORDER BY transition_probability DESC
                LIMIT ?
            """, (current_state, n))
            predictions = cursor.fetchall()

        # Boost predictions based on history patterns
        if history and len(history) >= 2:
            recent_pattern = history[-2:] + [current_state]
            pattern_boost = self._get_pattern_boost(recent_pattern)

            if pattern_boost:
                boosted = []
                for state, prob in predictions:
                    boost = pattern_boost.get(state, 0.0)
                    boosted.append((state, min(1.0, prob + boost)))
                predictions = sorted(boosted, key=lambda x: x[1], reverse=True)[:n]

        return predictions

    def _get_pattern_boost(self, recent_pattern: List[str]) -> Dict[str, float]:
        """Get probability boosts based on matching patterns"""
        boost = {}

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Check if we have patterns starting with recent_pattern
            pattern_prefix = '>'.join(recent_pattern)
            cursor.execute("""
                SELECT sequence_json, frequency
                FROM state_sequences
                WHERE sequence_json LIKE ?
                ORDER BY frequency DESC
                LIMIT 5
            """, (f'["{recent_pattern[0]}"%',))

            for row in cursor.fetchall():
                try:
                    sequence = json.loads(row[0])
                    freq = row[1]
                    # Find next state after our pattern
                    for i in range(len(sequence) - len(recent_pattern)):
                        if sequence[i:i+len(recent_pattern)] == recent_pattern:
                            next_state = sequence[i + len(recent_pattern)] if i + len(recent_pattern) < len(sequence) else None
                            if next_state:
                                boost[next_state] = boost.get(next_state, 0) + 0.1 * (freq / 10)
                except (json.JSONDecodeError, IndexError):
                    continue

        return boost

    # ========================================================================
    # PATTERN DETECTION METHODS
    # ========================================================================

    def detect_recurring_patterns(
        self,
        min_frequency: Optional[int] = None
    ) -> List[PatternTemplate]:
        """
        Detect recurring conversation patterns

        Args:
            min_frequency: Minimum observation count (default: pattern_threshold)

        Returns:
            List of PatternTemplate objects
        """
        min_freq = min_frequency or self.pattern_threshold

        patterns = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sequence_id, sequence_json, frequency, avg_satisfaction, last_seen, first_seen
                FROM state_sequences
                WHERE frequency >= ?
                ORDER BY frequency DESC
            """, (min_freq,))

            for row in cursor.fetchall():
                try:
                    sequence = json.loads(row[1])
                    skip_opps = self._detect_skip_opportunities(sequence)

                    pattern = PatternTemplate(
                        pattern_id=row[0],
                        sequence=sequence,
                        frequency=row[2],
                        avg_satisfaction=row[3] or 0.5,
                        skip_opportunities=skip_opps,
                        last_applied=None
                    )
                    patterns.append(pattern)
                except json.JSONDecodeError:
                    continue

        return patterns

    def anticipate_user_need(
        self,
        current_state: str,
        history: Optional[List[str]] = None
    ) -> Optional[AnticipatedResponse]:
        """
        Anticipate user's next need based on patterns

        Args:
            current_state: Current conversation state
            history: Recent state history

        Returns:
            AnticipatedResponse object if confident prediction, else None
        """
        history = history or self.conversation_history

        # Get likely next states
        predictions = self.predict_next_states(current_state, history, n=5)

        if not predictions:
            return None

        # Check confidence of top prediction
        top_state, top_prob = predictions[0]

        if top_prob < 0.3:  # Not confident enough
            return None

        # Generate suggested action
        action = self._get_suggested_action(current_state, top_state)

        return AnticipatedResponse(
            current_state=current_state,
            likely_next_states=predictions[:3],
            suggested_action=action,
            confidence=top_prob
        )

    def _get_suggested_action(self, current_state: str, next_state: str) -> Optional[str]:
        """Generate suggested action based on anticipated transition"""
        suggestions = {
            ('problem_statement', 'clarification_question'): "Prepare to clarify - user may need simpler explanation",
            ('technical_explanation', 'simplified_explanation'): "Pre-compute simpler version of explanation",
            ('debugging_help', 'frustration_expression'): "Show extra empathy - user may be frustrated",
            ('code_review', 'correction_request'): "Double-check code suggestions for accuracy",
            ('clarification_question', 'positive_feedback'): "Explanation likely sufficient",
        }
        return suggestions.get((current_state, next_state))

    # ========================================================================
    # MAINTENANCE METHODS
    # ========================================================================

    def apply_temporal_decay(
        self,
        days_inactive: float = 7.0
    ) -> int:
        """
        Apply time-based decay to old transitions

        Args:
            days_inactive: Number of days since last observation

        Returns:
            int: Number of transitions decayed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Decay transitions not observed recently
            decay_factor = 0.95  # 5% decay
            cursor.execute("""
                UPDATE conversation_state_transitions
                SET transition_count = MAX(1, CAST(transition_count * ? AS INTEGER))
                WHERE julianday('now') - julianday(last_observed) >= ?
            """, (decay_factor, days_inactive))

            count = cursor.rowcount
            conn.commit()

        return count

    def reset_history(self) -> None:
        """Reset conversation history for new session"""
        self.conversation_history = []

    # ========================================================================
    # EXPORT & DEBUG METHODS
    # ========================================================================

    def export_transition_matrix(self) -> List[Dict]:
        """
        Export transition matrix for analysis

        Returns:
            List of dicts with keys: state_from, state_to, probability, count
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT state_from, state_to, transition_probability, transition_count, last_observed
                FROM conversation_state_transitions
                ORDER BY transition_probability DESC
            """)
            return [
                {
                    'state_from': row[0],
                    'state_to': row[1],
                    'probability': row[2],
                    'count': row[3],
                    'last_observed': row[4]
                }
                for row in cursor.fetchall()
            ]

    def get_statistics(self) -> Dict:
        """Get system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total transitions
            cursor.execute("SELECT COUNT(*) FROM conversation_state_transitions")
            total_transitions = cursor.fetchone()[0]

            # Total observations
            cursor.execute("SELECT SUM(transition_count) FROM conversation_state_transitions")
            total_observations = cursor.fetchone()[0] or 0

            # Unique states
            cursor.execute("""
                SELECT COUNT(DISTINCT state_from) + COUNT(DISTINCT state_to)
                FROM conversation_state_transitions
            """)
            unique_states = cursor.fetchone()[0]

            # Sequence count
            cursor.execute("SELECT COUNT(*) FROM state_sequences")
            total_sequences = cursor.fetchone()[0]

            # Most common transition
            cursor.execute("""
                SELECT state_from, state_to, transition_count
                FROM conversation_state_transitions
                ORDER BY transition_count DESC
                LIMIT 1
            """)
            most_common = cursor.fetchone()

            return {
                'total_transitions': total_transitions,
                'total_observations': total_observations,
                'unique_states': unique_states,
                'total_sequences': total_sequences,
                'most_common_transition': f"{most_common[0]} -> {most_common[1]}" if most_common else None,
                'history_length': len(self.conversation_history)
            }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _check_for_sequence_pattern(self) -> None:
        """Check if recent history forms a recurring pattern"""
        # Check 3, 4, and 5-length sequences
        for length in [3, 4, 5]:
            if len(self.conversation_history) >= length:
                sequence = self.conversation_history[-length:]
                self._update_sequence(sequence)

    def _update_sequence(self, sequence: List[str]) -> None:
        """Update or create sequence in database"""
        sequence_id = self._generate_sequence_hash(sequence)
        sequence_json = json.dumps(sequence)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO state_sequences
                (sequence_id, sequence_json, frequency, avg_satisfaction, last_seen, first_seen)
                VALUES (?, ?, 1, 0.5, datetime('now'), datetime('now'))
                ON CONFLICT(sequence_id) DO UPDATE SET
                    frequency = frequency + 1,
                    last_seen = datetime('now')
            """, (sequence_id, sequence_json))
            conn.commit()

    def _generate_sequence_hash(self, sequence: List[str]) -> str:
        """Generate hash for sequence"""
        seq_string = '>'.join(sequence)
        return hashlib.md5(seq_string.encode()).hexdigest()[:16]

    def _detect_skip_opportunities(
        self,
        sequence: List[str]
    ) -> List[SkipOpportunity]:
        """Detect states that can be skipped in sequence"""
        opportunities = []

        if len(sequence) < 3:
            return opportunities

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for i in range(len(sequence) - 2):
                state_a = sequence[i]
                state_b = sequence[i + 1]
                state_c = sequence[i + 2]

                # Check if direct A->C exists with decent probability
                cursor.execute("""
                    SELECT transition_probability
                    FROM conversation_state_transitions
                    WHERE state_from = ? AND state_to = ?
                """, (state_a, state_c))

                result = cursor.fetchone()
                if result and result[0] > 0.2:  # Has a reasonable direct path
                    # Compare with A->B probability
                    cursor.execute("""
                        SELECT transition_probability
                        FROM conversation_state_transitions
                        WHERE state_from = ? AND state_to = ?
                    """, (state_a, state_b))
                    ab_prob = cursor.fetchone()

                    if ab_prob and result[0] >= ab_prob[0] * 0.5:
                        # Direct path is at least half as likely
                        opportunities.append(SkipOpportunity(
                            from_state=state_a,
                            skip_state=state_b,
                            to_state=state_c,
                            confidence=result[0]
                        ))

        return opportunities
