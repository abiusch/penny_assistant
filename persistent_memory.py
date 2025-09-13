#!/usr/bin/env python3
"""
Persistent Memory System for Penny - Cross-Session Relationship Building
Stores user facts, preferences, inside jokes, and conversation history
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class MemoryType(Enum):
    USER_FACT = "user_fact"           # "CJ likes FastAPI"
    PREFERENCE = "preference"         # "Prefers technical details"
    INSIDE_JOKE = "inside_joke"       # "Calls Josh 'Brochacho'"
    CONVERSATION_SUMMARY = "conv_summary"  # "Discussed microservices on 2025-09-10"
    PERSONALITY_FEEDBACK = "personality_feedback"  # "User laughed at sarcasm level"
    TECHNICAL_INTEREST = "tech_interest"  # "Interested in voice AI"

@dataclass
class MemoryItem:
    id: Optional[int]
    memory_type: MemoryType
    key: str
    value: str
    confidence: float  # 0.0 - 1.0
    created_at: datetime
    last_accessed: datetime
    access_count: int
    context: str  # Additional context/metadata
    
class PersistentMemory:
    """Persistent memory system for cross-session relationship building"""
    
    def __init__(self, db_path: str = "penny_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the memory database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 1.0,
                created_at TIMESTAMP NOT NULL,
                last_accessed TIMESTAMP NOT NULL,
                access_count INTEGER DEFAULT 1,
                context TEXT DEFAULT '',
                UNIQUE(memory_type, key)
            )
        """)
        
        # Conversation sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start TIMESTAMP NOT NULL,
                session_end TIMESTAMP,
                interface_type TEXT NOT NULL,  -- 'voice' or 'text'
                message_count INTEGER DEFAULT 0,
                topics TEXT,  -- JSON array of topics discussed
                mood TEXT DEFAULT 'neutral',
                summary TEXT DEFAULT ''
            )
        """)
        
        # User reactions table for feedback learning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_input TEXT NOT NULL,
                penny_response TEXT NOT NULL,
                reaction_type TEXT,  -- 'positive', 'negative', 'neutral'
                reaction_indicators TEXT,  -- 'lol', 'thanks', 'confused', etc.
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (session_id) REFERENCES conversation_sessions(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"📚 Memory database initialized: {self.db_path}")
    
    def store_memory(self, memory_type: MemoryType, key: str, value: str, 
                    confidence: float = 1.0, context: str = "") -> bool:
        """Store or update a memory item"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # Try to update existing memory
            cursor.execute("""
                UPDATE memory_items 
                SET value = ?, confidence = ?, last_accessed = ?, 
                    access_count = access_count + 1, context = ?
                WHERE memory_type = ? AND key = ?
            """, (value, confidence, now, context, memory_type.value, key))
            
            if cursor.rowcount == 0:
                # Insert new memory
                cursor.execute("""
                    INSERT INTO memory_items 
                    (memory_type, key, value, confidence, created_at, last_accessed, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (memory_type.value, key, value, confidence, now, now, context))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error storing memory: {e}")
            return False
    
    def recall_memory(self, memory_type: MemoryType, key: str) -> Optional[MemoryItem]:
        """Recall a specific memory item"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, memory_type, key, value, confidence, created_at, 
                       last_accessed, access_count, context
                FROM memory_items 
                WHERE memory_type = ? AND key = ?
            """, (memory_type.value, key))
            
            row = cursor.fetchone()
            if row:
                # Update access count and time
                cursor.execute("""
                    UPDATE memory_items 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE id = ?
                """, (datetime.now(), row[0]))
                conn.commit()
                
                conn.close()
                return MemoryItem(
                    id=row[0],
                    memory_type=MemoryType(row[1]),
                    key=row[2],
                    value=row[3],
                    confidence=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    last_accessed=datetime.fromisoformat(row[6]),
                    access_count=row[7] + 1,
                    context=row[8]
                )
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"❌ Error recalling memory: {e}")
            return None
    
    def search_memories(self, memory_type: Optional[MemoryType] = None, 
                       search_term: str = "", limit: int = 10) -> List[MemoryItem]:
        """Search memories by type and/or content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT id, memory_type, key, value, confidence, created_at, 
                       last_accessed, access_count, context
                FROM memory_items 
                WHERE 1=1
            """
            params = []
            
            if memory_type:
                query += " AND memory_type = ?"
                params.append(memory_type.value)
            
            if search_term:
                query += " AND (key LIKE ? OR value LIKE ? OR context LIKE ?)"
                term = f"%{search_term}%"
                params.extend([term, term, term])
            
            query += " ORDER BY last_accessed DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memories.append(MemoryItem(
                    id=row[0],
                    memory_type=MemoryType(row[1]),
                    key=row[2],
                    value=row[3],
                    confidence=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    last_accessed=datetime.fromisoformat(row[6]),
                    access_count=row[7],
                    context=row[8]
                ))
            
            conn.close()
            return memories
            
        except Exception as e:
            print(f"❌ Error searching memories: {e}")
            return []
    
    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get a summary of what Penny knows about the user"""
        summary = {
            "user_facts": self.search_memories(MemoryType.USER_FACT, limit=20),
            "preferences": self.search_memories(MemoryType.PREFERENCE, limit=10),
            "inside_jokes": self.search_memories(MemoryType.INSIDE_JOKE, limit=10),
            "technical_interests": self.search_memories(MemoryType.TECHNICAL_INTEREST, limit=15),
            "recent_conversations": self.search_memories(MemoryType.CONVERSATION_SUMMARY, limit=5)
        }
        
        return summary
    
    def start_conversation_session(self, interface_type: str) -> int:
        """Start tracking a new conversation session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO conversation_sessions (session_start, interface_type)
                VALUES (?, ?)
            """, (datetime.now(), interface_type))
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"📝 Started {interface_type} conversation session: {session_id}")
            return session_id
            
        except Exception as e:
            print(f"❌ Error starting session: {e}")
            return 0
    
    def end_conversation_session(self, session_id: int, summary: str = ""):
        """End a conversation session with summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE conversation_sessions 
                SET session_end = ?, summary = ?
                WHERE id = ?
            """, (datetime.now(), summary, session_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error ending session: {e}")
    
    def log_user_reaction(self, session_id: int, user_input: str, 
                         penny_response: str, reaction_indicators: List[str]):
        """Log user reaction for personality feedback learning"""
        try:
            # Analyze reaction type
            positive_indicators = ['lol', 'haha', '😂', '😄', 'funny', 'love it', 'perfect', 'thanks']
            negative_indicators = ['confused', 'what', 'huh', 'wrong', 'no', 'stop']
            
            reaction_type = 'neutral'
            for indicator in reaction_indicators:
                if any(pos in indicator.lower() for pos in positive_indicators):
                    reaction_type = 'positive'
                    break
                elif any(neg in indicator.lower() for neg in negative_indicators):
                    reaction_type = 'negative'
                    break
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_reactions 
                (session_id, user_input, penny_response, reaction_type, 
                 reaction_indicators, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, user_input, penny_response, reaction_type, 
                  json.dumps(reaction_indicators), datetime.now()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error logging reaction: {e}")
    
    def extract_and_store_facts(self, user_input: str, context: Dict[str, Any] = None):
        """Extract and store user facts from conversation"""
        context = context or {}
        user_input_lower = user_input.lower()
        
        # Extract facts about user preferences
        if "i like" in user_input_lower or "i love" in user_input_lower:
            # Extract what they like
            for phrase in ["i like", "i love"]:
                if phrase in user_input_lower:
                    start = user_input_lower.index(phrase) + len(phrase)
                    preference = user_input[start:].strip().split('.')[0]
                    if preference and len(preference) < 100:
                        self.store_memory(
                            MemoryType.PREFERENCE, 
                            f"likes_{preference[:30]}", 
                            preference,
                            confidence=0.8,
                            context=f"Said: '{user_input}'"
                        )
        
        # Extract technical interests
        tech_terms = ['python', 'fastapi', 'ai', 'voice', 'programming', 'coding', 
                     'microservices', 'architecture', 'development']
        for term in tech_terms:
            if term in user_input_lower:
                self.store_memory(
                    MemoryType.TECHNICAL_INTEREST,
                    f"interest_{term}",
                    f"Shows interest in {term}",
                    confidence=0.7,
                    context=f"Mentioned in: '{user_input}'"
                )
        
        # Extract relationship info
        if 'josh' in user_input_lower or 'brochacho' in user_input_lower:
            self.store_memory(
                MemoryType.USER_FACT,
                "friend_josh",
                "Has a friend/colleague named Josh (sometimes called 'brochacho')",
                confidence=0.9,
                context=f"Mentioned: '{user_input}'"
            )
        
        if 'reneille' in user_input_lower:
            self.store_memory(
                MemoryType.USER_FACT,
                "friend_reneille",
                "Has a friend/colleague named Reneille",
                confidence=0.9,
                context=f"Mentioned: '{user_input}'"
            )
    
    def get_memory_stats(self) -> Dict[str, int]:
        """Get statistics about stored memories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            for memory_type in MemoryType:
                cursor.execute("""
                    SELECT COUNT(*) FROM memory_items WHERE memory_type = ?
                """, (memory_type.value,))
                count = cursor.fetchone()[0]
                stats[memory_type.value] = count
            
            conn.close()
            return stats
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def cleanup_old_memories(self, days_old: int = 90):
        """Clean up very old, low-confidence memories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            cursor.execute("""
                DELETE FROM memory_items 
                WHERE last_accessed < ? AND confidence < 0.3 AND access_count < 2
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old memories")
                
        except Exception as e:
            print(f"❌ Error cleaning memories: {e}")

# Memory-enhanced personality integration
class MemoryEnhancedPersonality:
    """Integrates persistent memory with existing personality system"""
    
    def __init__(self, memory_system: PersistentMemory):
        self.memory = memory_system
    
    def enhance_context_with_memory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance conversation context with relevant memories"""
        enhanced_context = context.copy()
        
        # Add relationship memories
        summary = self.memory.get_relationship_summary()
        enhanced_context['remembered_facts'] = []
        enhanced_context['inside_jokes'] = []
        enhanced_context['preferences'] = []
        
        # Add relevant facts (more selective)
        for fact in summary['user_facts'][:3]:  
            enhanced_context['remembered_facts'].append(f"{fact.key}: {fact.value}")
        
        for joke in summary['inside_jokes'][:2]:  # Limit inside jokes
            enhanced_context['inside_jokes'].append(f"{joke.key}: {joke.value}")
            
        for pref in summary['preferences'][:3]:  # Limit preferences
            enhanced_context['preferences'].append(f"{pref.key}: {pref.value}")
        
        # Add memory-aware instructions for LLM
        if enhanced_context.get('remembered_facts') or enhanced_context.get('preferences'):
            enhanced_context['memory_instruction'] = "Use what you know about the user naturally - don't list facts, weave them into conversation"
        
        return enhanced_context
    
    def learn_from_conversation(self, user_input: str, penny_response: str, 
                               context: Dict[str, Any]):
        """Learn from the current conversation exchange"""
        # Extract and store new facts
        self.memory.extract_and_store_facts(user_input, context)
        
        # Store conversation summary if significant topics were discussed
        topics = context.get('topic', 'conversation')
        if topics != 'conversation':
            self.memory.store_memory(
                MemoryType.CONVERSATION_SUMMARY,
                f"conv_{datetime.now().strftime('%Y%m%d_%H%M')}",
                f"Discussed {topics}",
                confidence=0.8,
                context=f"User: {user_input[:50]}..."
            )

def create_memory_system(db_path: str = "penny_memory.db") -> PersistentMemory:
    """Factory function to create memory system"""
    return PersistentMemory(db_path)

# Example usage and testing
if __name__ == "__main__":
    print("🧠 Testing Persistent Memory System...")
    
    # Create memory system
    memory = create_memory_system("test_memory.db")
    
    # Test storing memories
    memory.store_memory(MemoryType.USER_FACT, "name", "CJ", 1.0, "Primary user")
    memory.store_memory(MemoryType.PREFERENCE, "coding_style", "Likes FastAPI and clean code", 0.9)
    memory.store_memory(MemoryType.INSIDE_JOKE, "josh_nickname", "Calls Josh 'brochacho'", 1.0)
    memory.store_memory(MemoryType.TECHNICAL_INTEREST, "ai_voice", "Working on voice AI assistant", 0.8)
    
    # Test recalling
    name_memory = memory.recall_memory(MemoryType.USER_FACT, "name")
    if name_memory:
        print(f"✅ Recalled: {name_memory.key} = {name_memory.value}")
    
    # Test search
    tech_memories = memory.search_memories(MemoryType.TECHNICAL_INTEREST)
    print(f"✅ Found {len(tech_memories)} technical interests")
    
    # Test relationship summary
    summary = memory.get_relationship_summary()
    print(f"✅ Relationship summary has {len(summary['user_facts'])} facts")
    
    # Test conversation session
    session_id = memory.start_conversation_session("text")
    memory.end_conversation_session(session_id, "Test conversation completed")
    
    # Test stats
    stats = memory.get_memory_stats()
    print(f"✅ Memory stats: {stats}")
    
    # Clean up test database
    os.remove("test_memory.db")
    print("🧠 Memory system test completed!")
