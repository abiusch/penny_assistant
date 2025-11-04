#!/usr/bin/env python3
"""
PennyGPT Memory System
Handles conversation memory, context, and user preferences
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import uuid


@dataclass
class ConversationTurn:
    """A single turn in a conversation."""
    turn_id: str
    timestamp: float
    user_input: str
    assistant_response: str
    context: Dict[str, Any]
    session_id: str
    response_time_ms: float = 0.0
    confidence: float = 1.0


@dataclass
class UserPreference:
    """A user preference or learned behavior."""
    key: str
    value: Any
    confidence: float
    last_updated: float
    frequency: int = 1


@dataclass
class ConversationSummary:
    """Summary of a conversation session."""
    session_id: str
    start_time: float
    end_time: float
    turn_count: int
    topics: List[str]
    summary: str
    user_satisfaction: Optional[float] = None


class MemoryManager:
    """Manages conversation memory, context, and user preferences."""
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Memory configuration
        self.max_context_turns = 10  # Number of turns to keep in active context
        self.max_session_age_days = 30  # How long to keep detailed conversations
        self.summary_threshold = 20  # Turns before creating session summary
        
        # Current session
        self.current_session_id = str(uuid.uuid4())
        self.active_context: List[ConversationTurn] = []
        self.user_preferences: Dict[str, UserPreference] = {}
        
        # Initialize database
        self._init_database()
        self._load_user_preferences()
    
    def _init_database(self):
        """Initialize the SQLite database with WAL mode for concurrent access."""
        with sqlite3.connect(self.db_path) as conn:
            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")  # 5 second timeout
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    turn_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT NOT NULL,
                    context TEXT,  -- JSON
                    response_time_ms REAL DEFAULT 0,
                    confidence REAL DEFAULT 1.0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT,  -- JSON
                    confidence REAL DEFAULT 1.0,
                    last_updated REAL NOT NULL,
                    frequency INTEGER DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_summaries (
                    session_id TEXT PRIMARY KEY,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    turn_count INTEGER NOT NULL,
                    topics TEXT,  -- JSON list
                    summary TEXT,
                    user_satisfaction REAL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_preferences_updated ON user_preferences(last_updated)")
    
    def _load_user_preferences(self):
        """Load user preferences from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM user_preferences")
            for row in cursor.fetchall():
                key, value_json, confidence, last_updated, frequency = row
                try:
                    value = json.loads(value_json)
                    self.user_preferences[key] = UserPreference(
                        key=key,
                        value=value,
                        confidence=confidence,
                        last_updated=last_updated,
                        frequency=frequency
                    )
                except json.JSONDecodeError:
                    continue
    
    def start_new_session(self) -> str:
        """Start a new conversation session."""
        # Save current session if it has content
        if self.active_context:
            self._save_session_summary()
        
        # Start new session
        self.current_session_id = str(uuid.uuid4())
        self.active_context.clear()
        
        print(f"🧠 Started new conversation session: {self.current_session_id[:8]}")
        return self.current_session_id
    
    def add_conversation_turn(
        self, 
        user_input: str, 
        assistant_response: str,
        context: Optional[Dict[str, Any]] = None,
        response_time_ms: float = 0.0,
        confidence: float = 1.0
    ) -> ConversationTurn:
        """Add a new conversation turn to memory."""
        
        turn = ConversationTurn(
            turn_id=str(uuid.uuid4()),
            timestamp=time.time(),
            user_input=user_input,
            assistant_response=assistant_response,
            context=context or {},
            session_id=self.current_session_id,
            response_time_ms=response_time_ms,
            confidence=confidence
        )
        
        # Add to active context
        self.active_context.append(turn)
        
        # Trim context if too long
        if len(self.active_context) > self.max_context_turns:
            self.active_context = self.active_context[-self.max_context_turns:]
        
        # Save to database
        self._save_turn_to_db(turn)
        
        # Learn from this interaction
        self._learn_from_interaction(user_input, assistant_response, context)
        
        # Create session summary if needed
        if len(self.active_context) >= self.summary_threshold:
            self._save_session_summary()
            self.start_new_session()
        
        return turn
    
    def _save_turn_to_db(self, turn: ConversationTurn):
        """Save a conversation turn to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations 
                (turn_id, session_id, timestamp, user_input, assistant_response, 
                 context, response_time_ms, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                turn.turn_id,
                turn.session_id,
                turn.timestamp,
                turn.user_input,
                turn.assistant_response,
                json.dumps(turn.context),
                turn.response_time_ms,
                turn.confidence
            ))
    
    def _learn_from_interaction(self, user_input: str, assistant_response: str, context: Optional[Dict]):
        """Learn user preferences from the interaction."""
        
        # Extract potential preferences
        user_lower = user_input.lower()
        
        # Preferred response style
        if any(word in user_lower for word in ['thanks', 'thank you', 'great', 'perfect']):
            self._update_preference('response_style', 'helpful', confidence=0.1)
        
        if any(word in user_lower for word in ['funny', 'joke', 'humor']):
            self._update_preference('response_style', 'humorous', confidence=0.2)
            
        if any(word in user_lower for word in ['brief', 'short', 'quickly']):
            self._update_preference('response_length', 'concise', confidence=0.15)
            
        if any(word in user_lower for word in ['explain', 'detail', 'more info']):
            self._update_preference('response_length', 'detailed', confidence=0.15)
        
        # Time patterns
        hour = datetime.now().hour
        if 6 <= hour < 12:
            self._update_preference('active_time', 'morning', confidence=0.05)
        elif 12 <= hour < 18:
            self._update_preference('active_time', 'afternoon', confidence=0.05)
        else:
            self._update_preference('active_time', 'evening', confidence=0.05)
        
        # Topic interests
        topics = self._extract_topics(user_input)
        for topic in topics:
            self._update_preference(f'topic_interest_{topic}', True, confidence=0.1)
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from text (simple keyword-based)."""
        topic_keywords = {
            'technology': ['ai', 'computer', 'software', 'tech', 'coding', 'programming'],
            'weather': ['weather', 'rain', 'sunny', 'temperature', 'forecast'],
            'calendar': ['meeting', 'appointment', 'schedule', 'calendar', 'event'],
            'music': ['song', 'music', 'playlist', 'artist', 'album'],
            'news': ['news', 'current', 'events', 'politics', 'world'],
            'health': ['health', 'exercise', 'diet', 'medical', 'fitness'],
            'entertainment': ['movie', 'tv', 'show', 'game', 'entertainment']
        }
        
        text_lower = text.lower()
        detected_topics = []
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_topics.append(topic)
        
        return detected_topics
    
    def _update_preference(self, key: str, value: Any, confidence: float = 0.1):
        """Update a user preference with confidence weighting."""
        current_time = time.time()
        
        if key in self.user_preferences:
            # Update existing preference
            pref = self.user_preferences[key]
            
            # Weighted average for confidence
            total_conf = pref.confidence + confidence
            if pref.value == value:
                # Reinforcing existing preference
                pref.confidence = min(1.0, total_conf)
                pref.frequency += 1
            else:
                # Conflicting preference - weighted update
                if confidence > pref.confidence:
                    pref.value = value
                    pref.confidence = confidence
                    pref.frequency = 1
                else:
                    # Keep existing, but reduce confidence slightly
                    pref.confidence = max(0.1, pref.confidence - 0.05)
            
            pref.last_updated = current_time
        else:
            # New preference
            self.user_preferences[key] = UserPreference(
                key=key,
                value=value,
                confidence=confidence,
                last_updated=current_time,
                frequency=1
            )
        
        # Save to database
        self._save_preference_to_db(self.user_preferences[key])
    
    def _save_preference_to_db(self, preference: UserPreference):
        """Save a user preference to the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO user_preferences 
                (key, value, confidence, last_updated, frequency)
                VALUES (?, ?, ?, ?, ?)
            """, (
                preference.key,
                json.dumps(preference.value),
                preference.confidence,
                preference.last_updated,
                preference.frequency
            ))
    
    def get_conversation_context(self, include_preferences: bool = True) -> Dict[str, Any]:
        """Get current conversation context for the LLM."""
        context = {
            'session_id': self.current_session_id,
            'turn_count': len(self.active_context),
            'recent_turns': []
        }
        
        # Add recent conversation turns
        for turn in self.active_context[-5:]:  # Last 5 turns
            context['recent_turns'].append({
                'user': turn.user_input,
                'assistant': turn.assistant_response,
                'timestamp': turn.timestamp
            })
        
        # Add user preferences if requested
        if include_preferences:
            context['user_preferences'] = {}
            for key, pref in self.user_preferences.items():
                if pref.confidence > 0.3:  # Only include confident preferences
                    context['user_preferences'][key] = {
                        'value': pref.value,
                        'confidence': pref.confidence
                    }
        
        return context
    
    def get_context_for_llm(self) -> str:
        """Format context as a string for LLM prompt injection."""
        context = self.get_conversation_context()
        
        context_parts = []
        
        # Add conversation history
        if context['recent_turns']:
            context_parts.append("Recent conversation:")
            for turn in context['recent_turns'][-3:]:  # Last 3 turns
                context_parts.append(f"User: {turn['user']}")
                context_parts.append(f"Assistant: {turn['assistant']}")
        
        # Add confident preferences
        preferences = context.get('user_preferences', {})
        if preferences:
            pref_list = []
            for key, pref in preferences.items():
                if pref['confidence'] > 0.5:
                    pref_list.append(f"{key}: {pref['value']}")
            
            if pref_list:
                context_parts.append(f"User preferences: {', '.join(pref_list)}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _save_session_summary(self):
        """Create and save a summary of the current session."""
        if not self.active_context:
            return
        
        first_turn = self.active_context[0]
        last_turn = self.active_context[-1]
        
        # Extract topics from all turns
        all_topics = set()
        for turn in self.active_context:
            topics = self._extract_topics(turn.user_input + " " + turn.assistant_response)
            all_topics.update(topics)
        
        # Create simple summary
        summary_parts = []
        if all_topics:
            summary_parts.append(f"Discussed: {', '.join(all_topics)}")
        summary_parts.append(f"Duration: {len(self.active_context)} turns")
        
        summary = ConversationSummary(
            session_id=self.current_session_id,
            start_time=first_turn.timestamp,
            end_time=last_turn.timestamp,
            turn_count=len(self.active_context),
            topics=list(all_topics),
            summary=". ".join(summary_parts)
        )
        
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO session_summaries 
                (session_id, start_time, end_time, turn_count, topics, summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                summary.session_id,
                summary.start_time,
                summary.end_time,
                summary.turn_count,
                json.dumps(summary.topics),
                summary.summary
            ))
        
        print(f"💾 Saved session summary: {summary.summary}")
    
    def search_conversations(
        self, 
        query: str, 
        limit: int = 10,
        session_id: Optional[str] = None
    ) -> List[ConversationTurn]:
        """Search through conversation history."""
        with sqlite3.connect(self.db_path) as conn:
            if session_id:
                cursor = conn.execute("""
                    SELECT * FROM conversations 
                    WHERE session_id = ? AND (user_input LIKE ? OR assistant_response LIKE ?)
                    ORDER BY timestamp DESC LIMIT ?
                """, (session_id, f"%{query}%", f"%{query}%", limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM conversations 
                    WHERE user_input LIKE ? OR assistant_response LIKE ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
            
            turns = []
            for row in cursor.fetchall():
                turn_id, session_id, timestamp, user_input, assistant_response, context_json, response_time, confidence = row
                
                try:
                    context = json.loads(context_json) if context_json else {}
                except json.JSONDecodeError:
                    context = {}
                
                turns.append(ConversationTurn(
                    turn_id=turn_id,
                    timestamp=timestamp,
                    user_input=user_input,
                    assistant_response=assistant_response,
                    context=context,
                    session_id=session_id,
                    response_time_ms=response_time,
                    confidence=confidence
                ))
            
            return turns
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total conversations
            total_turns = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            
            # Unique sessions
            unique_sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM conversations").fetchone()[0]
            
            # Recent activity (last 7 days)
            week_ago = time.time() - (7 * 24 * 60 * 60)
            recent_turns = conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE timestamp > ?", (week_ago,)
            ).fetchone()[0]
            
            # Preferences count
            preferences_count = len(self.user_preferences)
        
        return {
            'total_conversation_turns': total_turns,
            'unique_sessions': unique_sessions,
            'recent_turns_7_days': recent_turns,
            'active_context_size': len(self.active_context),
            'user_preferences': preferences_count,
            'current_session_id': self.current_session_id[:8],
            'memory_db_size': self.db_path.stat().st_size if self.db_path.exists() else 0
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old conversation data to manage database size."""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        
        with sqlite3.connect(self.db_path) as conn:
            # Delete old conversations
            deleted_conversations = conn.execute(
                "DELETE FROM conversations WHERE timestamp < ?", (cutoff_time,)
            ).rowcount
            
            # Delete old session summaries
            deleted_summaries = conn.execute(
                "DELETE FROM session_summaries WHERE start_time < ?", (cutoff_time,)
            ).rowcount
            
            # Vacuum database to reclaim space
            conn.execute("VACUUM")
        
        print(f"🧹 Cleaned up {deleted_conversations} old conversations and {deleted_summaries} summaries")
    
    def export_memory(self, filepath: str):
        """Export memory data to JSON file."""
        data = {
            'conversations': [],
            'preferences': {},
            'sessions': [],
            'export_timestamp': time.time()
        }
        
        # Export conversations
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM conversations ORDER BY timestamp")
            for row in cursor.fetchall():
                turn_id, session_id, timestamp, user_input, assistant_response, context_json, response_time, confidence = row
                data['conversations'].append({
                    'turn_id': turn_id,
                    'session_id': session_id,
                    'timestamp': timestamp,
                    'user_input': user_input,
                    'assistant_response': assistant_response,
                    'context': json.loads(context_json) if context_json else {},
                    'response_time_ms': response_time,
                    'confidence': confidence
                })
        
        # Export preferences
        for key, pref in self.user_preferences.items():
            data['preferences'][key] = asdict(pref)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Memory exported to {filepath}")


def main():
    """Test the memory system."""
    memory = MemoryManager()
    
    print("🧠 Testing PennyGPT Memory System")
    print("=" * 40)
    
    # Simulate some conversations
    memory.add_conversation_turn(
        "Hello, how are you?",
        "Hi! I'm doing well, thanks for asking. How can I help you today?",
        response_time_ms=750
    )
    
    memory.add_conversation_turn(
        "Can you tell me a funny joke?",
        "Why don't scientists trust atoms? Because they make up everything!",
        response_time_ms=650
    )
    
    memory.add_conversation_turn(
        "That's great, thanks! What's the weather like?",
        "I'd be happy to help with weather, but I'll need to check the current conditions. Would you like me to look that up?",
        response_time_ms=580
    )
    
    # Show context
    print("\n📝 Current Context:")
    context = memory.get_context_for_llm()
    print(context)
    
    # Show preferences
    print("\n👤 Learned Preferences:")
    for key, pref in memory.user_preferences.items():
        if pref.confidence > 0.1:
            print(f"  {key}: {pref.value} (confidence: {pref.confidence:.2f})")
    
    # Show stats
    print("\n📊 Memory Stats:")
    stats = memory.get_memory_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


class PennyMemory(MemoryManager):
    """Alias for MemoryManager to match expected import name."""
    pass
