#!/usr/bin/env python3
"""
Enhanced Emotional Memory System for PennyGPT
Builds on existing memory system to add emotional intelligence and relationship tracking
"""

import json
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path
import re
from enum import Enum


class EmotionalState(Enum):
    """Detected user emotional states."""
    HAPPY = "happy"
    EXCITED = "excited"
    SAD = "sad"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    WORRIED = "worried"
    TIRED = "tired"
    PLAYFUL = "playful"
    SERIOUS = "serious"
    NEUTRAL = "neutral"


class RelationshipType(Enum):
    """Types of relationships PennyGPT tracks."""
    FAMILY = "family"
    FRIEND = "friend"
    COLLEAGUE = "colleague"
    PARTNER = "partner"
    PET = "pet"
    OTHER = "other"


@dataclass
class EmotionalContext:
    """Emotional context for a conversation turn."""
    detected_emotion: EmotionalState
    confidence: float
    emotional_indicators: List[str]  # Words/phrases that indicated emotion
    user_stress_level: float  # 0-1 scale
    conversation_tone: str  # casual, formal, intimate, etc.
    timestamp: float


@dataclass
class FamilyMember:
    """Information about a family member or relationship."""
    name: str
    relationship_type: RelationshipType
    notes: List[str]
    last_mentioned: float
    mention_count: int
    emotional_associations: Dict[str, float]  # emotion -> strength
    important_facts: List[str]
    
    
@dataclass
class ValueAlignment:
    """Tracks user's values and ethical framework."""
    category: str  # ethics, politics, lifestyle, etc.
    value_statement: str
    confidence: float
    supporting_evidence: List[str]
    last_reinforced: float


@dataclass
class LearningGoal:
    """Things the user wants to learn or explore together."""
    topic: str
    user_interest_level: float
    current_knowledge_level: str  # beginner, intermediate, advanced
    learning_style_preference: str  # visual, detailed, conversational
    exploration_permission: bool  # Can PennyGPT research this proactively
    last_discussed: float


class EmotionalMemorySystem:
    """Enhanced memory system with emotional intelligence and relationship tracking."""
    
    def __init__(self, base_memory_manager):
        self.base_memory = base_memory_manager
        self.db_path = base_memory_manager.db_path
        
        # Emotional analysis patterns
        self.emotion_patterns = {
            EmotionalState.HAPPY: ["happy", "great", "awesome", "wonderful", "excited", "love", "perfect"],
            EmotionalState.SAD: ["sad", "disappointed", "down", "upset", "depressed", "awful"],
            EmotionalState.FRUSTRATED: ["frustrated", "annoying", "stupid", "hate", "ugh", "why"],
            EmotionalState.WORRIED: ["worried", "concerned", "anxious", "nervous", "scared"],
            EmotionalState.CURIOUS: ["why", "how", "what", "tell me about", "explain", "learn"],
            EmotionalState.TIRED: ["tired", "exhausted", "sleepy", "worn out", "drained"],
            EmotionalState.PLAYFUL: ["haha", "lol", "funny", "joke", "play", "fun"],
            EmotionalState.SERIOUS: ["important", "serious", "need to", "must", "critical"]
        }
        
        # Current emotional state
        self.current_emotional_context: Optional[EmotionalContext] = None
        
        # Relationship tracking
        self.family_members: Dict[str, FamilyMember] = {}
        self.value_alignments: Dict[str, ValueAlignment] = {}
        self.learning_goals: Dict[str, LearningGoal] = {}
        
        # Initialize enhanced database
        self._init_emotional_database()
        self._load_emotional_data()
    
    def _init_emotional_database(self):
        """Initialize emotional memory database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Emotional context for each conversation
            conn.execute("""
                CREATE TABLE IF NOT EXISTS emotional_context (
                    turn_id TEXT PRIMARY KEY,
                    detected_emotion TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    emotional_indicators TEXT,  -- JSON list
                    user_stress_level REAL DEFAULT 0.0,
                    conversation_tone TEXT DEFAULT 'neutral',
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (turn_id) REFERENCES conversations (turn_id)
                )
            """)
            
            # Family and relationship tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    name TEXT PRIMARY KEY,
                    relationship_type TEXT NOT NULL,
                    notes TEXT,  -- JSON list
                    last_mentioned REAL NOT NULL,
                    mention_count INTEGER DEFAULT 1,
                    emotional_associations TEXT,  -- JSON dict
                    important_facts TEXT  -- JSON list
                )
            """)
            
            # Value alignment tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS value_alignments (
                    category TEXT NOT NULL,
                    value_statement TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    supporting_evidence TEXT,  -- JSON list
                    last_reinforced REAL NOT NULL,
                    PRIMARY KEY (category, value_statement)
                )
            """)
            
            # Learning goals and interests
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_goals (
                    topic TEXT PRIMARY KEY,
                    user_interest_level REAL NOT NULL,
                    current_knowledge_level TEXT DEFAULT 'beginner',
                    learning_style_preference TEXT DEFAULT 'conversational',
                    exploration_permission INTEGER DEFAULT 0,
                    last_discussed REAL NOT NULL
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_emotional_timestamp ON emotional_context(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_mentioned ON relationships(last_mentioned)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_values_reinforced ON value_alignments(last_reinforced)")
    
    def _load_emotional_data(self):
        """Load emotional data from database."""
        with sqlite3.connect(self.db_path) as conn:
            # Load relationships
            cursor = conn.execute("SELECT * FROM relationships")
            for row in cursor.fetchall():
                name, rel_type, notes_json, last_mentioned, mention_count, emotions_json, facts_json = row
                
                self.family_members[name] = FamilyMember(
                    name=name,
                    relationship_type=RelationshipType(rel_type),
                    notes=json.loads(notes_json) if notes_json else [],
                    last_mentioned=last_mentioned,
                    mention_count=mention_count,
                    emotional_associations=json.loads(emotions_json) if emotions_json else {},
                    important_facts=json.loads(facts_json) if facts_json else []
                )
            
            # Load value alignments
            cursor = conn.execute("SELECT * FROM value_alignments")
            for row in cursor.fetchall():
                category, value_statement, confidence, evidence_json, last_reinforced = row
                key = f"{category}:{value_statement}"
                
                self.value_alignments[key] = ValueAlignment(
                    category=category,
                    value_statement=value_statement,
                    confidence=confidence,
                    supporting_evidence=json.loads(evidence_json) if evidence_json else [],
                    last_reinforced=last_reinforced
                )
            
            # Load learning goals
            cursor = conn.execute("SELECT * FROM learning_goals")
            for row in cursor.fetchall():
                topic, interest, knowledge, style, permission, last_discussed = row
                
                self.learning_goals[topic] = LearningGoal(
                    topic=topic,
                    user_interest_level=interest,
                    current_knowledge_level=knowledge,
                    learning_style_preference=style,
                    exploration_permission=bool(permission),
                    last_discussed=last_discussed
                )
    
    def analyze_emotional_context(self, user_input: str, assistant_response: str) -> EmotionalContext:
        """Analyze emotional context of a conversation turn."""
        user_lower = user_input.lower()
        
        # Detect primary emotion
        emotion_scores = {}
        detected_indicators = []
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in user_lower:
                    score += 1
                    detected_indicators.append(pattern)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Determine primary emotion
        if emotion_scores:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            confidence = min(1.0, emotion_scores[primary_emotion] / 3.0)
        else:
            primary_emotion = EmotionalState.NEUTRAL
            confidence = 0.5
        
        # Estimate stress level based on language patterns
        stress_indicators = ["urgent", "asap", "quickly", "stressed", "overwhelmed", "busy", "deadline"]
        stress_level = min(1.0, sum(1 for indicator in stress_indicators if indicator in user_lower) / 3.0)
        
        # Determine conversation tone
        tone = "casual"
        if any(formal in user_lower for formal in ["please", "could you", "would you mind"]):
            tone = "formal"
        elif any(intimate in user_lower for intimate in ["feel", "think", "personal", "family"]):
            tone = "intimate"
        elif primary_emotion in [EmotionalState.PLAYFUL, EmotionalState.HAPPY]:
            tone = "playful"
        elif primary_emotion in [EmotionalState.SERIOUS, EmotionalState.WORRIED]:
            tone = "serious"
        
        context = EmotionalContext(
            detected_emotion=primary_emotion,
            confidence=confidence,
            emotional_indicators=detected_indicators,
            user_stress_level=stress_level,
            conversation_tone=tone,
            timestamp=time.time()
        )
        
        self.current_emotional_context = context
        return context
    
    def extract_relationship_mentions(self, user_input: str) -> List[Tuple[str, RelationshipType]]:
        """Extract mentions of family members and relationships."""
        mentions = []
        text_lower = user_input.lower()
        
        # Common relationship indicators
        relationship_patterns = {
            RelationshipType.FAMILY: [
                r'\b(my )?(mom|mother|dad|father|sister|brother|son|daughter|wife|husband|grandma|grandpa|aunt|uncle|cousin)\b',
                r'\b(my )?(family|parents|kids|children)\b'
            ],
            RelationshipType.FRIEND: [
                r'\b(my )?(friend|buddy|bestie)\b',
                r'\b(my friend|a friend of mine)\b'
            ],
            RelationshipType.COLLEAGUE: [
                r'\b(my )?(colleague|coworker|boss|manager|team)\b'
            ],
            RelationshipType.PARTNER: [
                r'\b(my )?(partner|boyfriend|girlfriend|fiancé|fiancée|spouse)\b'
            ],
            RelationshipType.PET: [
                r'\b(my )?(dog|cat|pet|puppy|kitten)\b'
            ]
        }
        
        # Look for relationship mentions
        for rel_type, patterns in relationship_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    name = match.group(0).strip()
                    mentions.append((name, rel_type))
        
        # Look for specific names (capitalized words that might be names)
        # Only check for names after relationship indicators
        name_pattern = r'\b[A-Z][a-z]{2,}\b'  # At least 3 letters
        potential_names = re.findall(name_pattern, user_input)
        
        # Filter out common words that aren't names
        common_words = {
            'I', 'The', 'This', 'That', 'When', 'Where', 'How', 'What', 'Why', 
            'Can', 'Could', 'Would', 'Should', 'Hello', 'Thanks', 'You', 'Ugh',
            'My', 'Your', 'His', 'Her', 'Their', 'We', 'They', 'He', 'She',
            'And', 'But', 'Or', 'So', 'Because', 'If', 'Then', 'Now', 'Here',
            'There', 'Yes', 'No', 'Maybe', 'Please', 'Sorry', 'Okay', 'Well'
        }
        
        # Only add names if they appear near relationship indicators
        relationship_context = ' '.join([m[0] for m in mentions])
        
        for name in potential_names:
            if (name not in common_words and 
                len(name) > 2 and 
                name.isalpha() and
                # Only add if we found other relationship mentions in this text
                (mentions or any(rel_word in text_lower for rel_word in 
                    ['mom', 'dad', 'family', 'friend', 'dog', 'cat', 'manager', 'boss']))):
                mentions.append((name, RelationshipType.OTHER))
        
        return mentions
    
    def update_relationship_knowledge(self, user_input: str, assistant_response: str):
        """Update knowledge about family members and relationships."""
        mentions = self.extract_relationship_mentions(user_input)
        current_time = time.time()
        
        for name, rel_type in mentions:
            if name in self.family_members:
                # Update existing relationship
                member = self.family_members[name]
                member.last_mentioned = current_time
                member.mention_count += 1
                
                # Update emotional associations
                if self.current_emotional_context:
                    emotion = self.current_emotional_context.detected_emotion.value
                    if emotion in member.emotional_associations:
                        member.emotional_associations[emotion] += 0.1
                    else:
                        member.emotional_associations[emotion] = 0.1
            else:
                # New relationship
                emotional_associations = {}
                if self.current_emotional_context:
                    emotion = self.current_emotional_context.detected_emotion.value
                    emotional_associations[emotion] = 0.2
                
                self.family_members[name] = FamilyMember(
                    name=name,
                    relationship_type=rel_type,
                    notes=[f"First mentioned: {user_input}"],
                    last_mentioned=current_time,
                    mention_count=1,
                    emotional_associations=emotional_associations,
                    important_facts=[]
                )
            
            # Save to database
            self._save_relationship_to_db(self.family_members[name])
    
    def detect_value_alignments(self, user_input: str, assistant_response: str):
        """Detect and track user's values and beliefs."""
        user_lower = user_input.lower()
        current_time = time.time()
        
        # Value indicators
        value_patterns = {
            'privacy': ['privacy', 'private', 'personal data', 'surveillance', 'tracking'],
            'family': ['family first', 'family time', 'important to me', 'family values'],
            'learning': ['learning', 'education', 'knowledge', 'understand', 'grow'],
            'efficiency': ['efficient', 'productive', 'organized', 'streamlined'],
            'creativity': ['creative', 'artistic', 'imagination', 'innovative'],
            'humor': ['funny', 'humor', 'joke', 'laugh', 'comedy'],
            'honesty': ['honest', 'truth', 'direct', 'straightforward'],
            'kindness': ['kind', 'compassionate', 'help others', 'caring']
        }
        
        for category, patterns in value_patterns.items():
            for pattern in patterns:
                if pattern in user_lower:
                    # Check if this reinforces an existing value or creates a new one
                    key = f"{category}:values_{pattern}"
                    
                    if key in self.value_alignments:
                        # Reinforce existing value
                        alignment = self.value_alignments[key]
                        alignment.confidence = min(1.0, alignment.confidence + 0.1)
                        alignment.last_reinforced = current_time
                        alignment.supporting_evidence.append(user_input[:100])
                    else:
                        # New value detected
                        self.value_alignments[key] = ValueAlignment(
                            category=category,
                            value_statement=f"Values {pattern}",
                            confidence=0.3,
                            supporting_evidence=[user_input[:100]],
                            last_reinforced=current_time
                        )
                    
                    self._save_value_alignment_to_db(self.value_alignments[key])
    
    def track_learning_interests(self, user_input: str, assistant_response: str):
        """Track what the user wants to learn about."""
        user_lower = user_input.lower()
        current_time = time.time()
        
        # Learning indicators
        learning_phrases = [
            "tell me about", "explain", "how does", "what is", "learn about",
            "understand", "teach me", "help me learn"
        ]
        
        # Extract topics
        topics = self.base_memory._extract_topics(user_input)
        
        for phrase in learning_phrases:
            if phrase in user_lower:
                # Extract the topic after the learning phrase
                pattern = f"{phrase} ([^.!?]*)"
                match = re.search(pattern, user_lower)
                if match:
                    topic = match.group(1).strip()[:50]  # Limit length
                    
                    if topic in self.learning_goals:
                        # Update existing learning goal
                        goal = self.learning_goals[topic]
                        goal.user_interest_level = min(1.0, goal.user_interest_level + 0.1)
                        goal.last_discussed = current_time
                    else:
                        # New learning goal
                        self.learning_goals[topic] = LearningGoal(
                            topic=topic,
                            user_interest_level=0.5,
                            current_knowledge_level="beginner",
                            learning_style_preference="conversational",
                            exploration_permission=False,  # Require explicit permission
                            last_discussed=current_time
                        )
                    
                    self._save_learning_goal_to_db(self.learning_goals[topic])
    
    def _save_relationship_to_db(self, member: FamilyMember):
        """Save relationship to database with transaction safety."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    conn.execute("""BEGIN IMMEDIATE TRANSACTION""")
                    conn.execute("""
                        INSERT OR REPLACE INTO relationships 
                        (name, relationship_type, notes, last_mentioned, mention_count, 
                         emotional_associations, important_facts)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        member.name,
                        member.relationship_type.value,
                        json.dumps(member.notes),
                        member.last_mentioned,
                        member.mention_count,
                        json.dumps(member.emotional_associations),
                        json.dumps(member.important_facts)
                    ))
                    conn.commit()
                    break
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"Database error saving relationship {member.name}: {e}")
                    break
            except Exception as e:
                print(f"Error saving relationship {member.name}: {e}")
                break
    
    def _save_value_alignment_to_db(self, alignment: ValueAlignment):
        """Save value alignment to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO value_alignments 
                (category, value_statement, confidence, supporting_evidence, last_reinforced)
                VALUES (?, ?, ?, ?, ?)
            """, (
                alignment.category,
                alignment.value_statement,
                alignment.confidence,
                json.dumps(alignment.supporting_evidence),
                alignment.last_reinforced
            ))
    
    def _save_learning_goal_to_db(self, goal: LearningGoal):
        """Save learning goal to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO learning_goals 
                (topic, user_interest_level, current_knowledge_level, 
                 learning_style_preference, exploration_permission, last_discussed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                goal.topic,
                goal.user_interest_level,
                goal.current_knowledge_level,
                goal.learning_style_preference,
                int(goal.exploration_permission),
                goal.last_discussed
            ))
    
    def get_enhanced_context_for_llm(self) -> str:
        """Get enhanced context including emotional intelligence for LLM."""
        context_parts = []
        
        # Add base conversation context
        base_context = self.base_memory.get_context_for_llm()
        if base_context:
            context_parts.append(base_context)
        
        # Add emotional context
        if self.current_emotional_context:
            emotion = self.current_emotional_context.detected_emotion.value
            tone = self.current_emotional_context.conversation_tone
            stress = self.current_emotional_context.user_stress_level
            
            emotion_context = f"User emotion: {emotion} ({tone} tone)"
            if stress > 0.3:
                emotion_context += f", stress level: {stress:.1f}"
            context_parts.append(emotion_context)
        
        # Add family/relationship context
        recent_relationships = [
            member for member in self.family_members.values()
            if time.time() - member.last_mentioned < 86400  # Last 24 hours
        ]
        if recent_relationships:
            rel_context = "Recently mentioned: " + ", ".join([
                f"{member.name} ({member.relationship_type.value})"
                for member in recent_relationships[:3]
            ])
            context_parts.append(rel_context)
        
        # Add strong value alignments
        strong_values = [
            alignment for alignment in self.value_alignments.values()
            if alignment.confidence > 0.6
        ]
        if strong_values:
            values_context = "User values: " + ", ".join([
                alignment.value_statement for alignment in strong_values[:3]
            ])
            context_parts.append(values_context)
        
        return "\n".join(context_parts)
    
    def process_conversation_turn(self, user_input: str, assistant_response: str, turn_id: str):
        """Process a conversation turn through emotional intelligence system."""
        
        # Analyze emotional context
        emotional_context = self.analyze_emotional_context(user_input, assistant_response)
        
        # Update relationship knowledge
        self.update_relationship_knowledge(user_input, assistant_response)
        
        # Detect value alignments
        self.detect_value_alignments(user_input, assistant_response)
        
        # Track learning interests
        self.track_learning_interests(user_input, assistant_response)
        
        # Save emotional context to database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO emotional_context 
                (turn_id, detected_emotion, confidence, emotional_indicators, 
                 user_stress_level, conversation_tone, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                turn_id,
                emotional_context.detected_emotion.value,
                emotional_context.confidence,
                json.dumps(emotional_context.emotional_indicators),
                emotional_context.user_stress_level,
                emotional_context.conversation_tone,
                emotional_context.timestamp
            ))
    
    def get_emotional_insights(self) -> Dict[str, Any]:
        """Get insights about user's emotional patterns and relationships."""
        insights = {
            'emotional_patterns': {},
            'relationship_summary': {},
            'value_alignments': {},
            'learning_interests': {}
        }
        
        # Emotional patterns from recent conversations
        week_ago = time.time() - (7 * 24 * 60 * 60)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT detected_emotion, COUNT(*) as count
                FROM emotional_context 
                WHERE timestamp > ?
                GROUP BY detected_emotion
                ORDER BY count DESC
            """, (week_ago,))
            
            for emotion, count in cursor.fetchall():
                insights['emotional_patterns'][emotion] = count
        
        # Relationship summary
        for name, member in self.family_members.items():
            insights['relationship_summary'][name] = {
                'type': member.relationship_type.value,
                'mentions': member.mention_count,
                'last_mentioned_days_ago': (time.time() - member.last_mentioned) / 86400,
                'primary_emotions': member.emotional_associations
            }
        
        # Strong value alignments
        for key, alignment in self.value_alignments.items():
            if alignment.confidence > 0.5:
                insights['value_alignments'][alignment.category] = {
                    'statement': alignment.value_statement,
                    'confidence': alignment.confidence
                }
        
        # Active learning interests
        for topic, goal in self.learning_goals.items():
            if goal.user_interest_level > 0.4:
                insights['learning_interests'][topic] = {
                    'interest_level': goal.user_interest_level,
                    'knowledge_level': goal.current_knowledge_level,
                    'exploration_permitted': goal.exploration_permission
                }
        
        return insights


def create_enhanced_memory_system(base_memory_manager):
    """Factory function to create an enhanced memory system."""
    return EmotionalMemorySystem(base_memory_manager)


# Integration function for the main pipeline
def integrate_emotional_memory(memory_manager):
    """Integrate emotional memory system with existing memory manager."""
    return create_enhanced_memory_system(memory_manager)
