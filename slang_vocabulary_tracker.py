#!/usr/bin/env python3
"""
Slang and Vocabulary Tracker
Learns user's preferred terminology, abbreviations, and communication style
"""

import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
from collections import defaultdict
import json

class SlangVocabularyTracker:
    """
    Tracks and learns user's preferred vocabulary, slang, and terminology
    Builds a personalized dictionary for natural communication
    """
    
    def __init__(self, db_path: str = "data/personality_tracking.db"):
        self.db_path = db_path
        self._init_database()
        
        # Common words to exclude from slang detection
        self.common_words = self._load_common_words()
        
        # Slang indicators
        self.slang_patterns = {
            'abbreviations': r'\b[a-z]{2,4}\b',  # Short lowercase words (lol, btw, etc)
            'tech_slang': ['refactor', 'debug', 'merge', 'deploy', 'ship', 'prod', 'repo'],
            'casual_intensifiers': ['super', 'really', 'totally', 'literally', 'basically'],
            'casual_fillers': ['like', 'just', 'actually', 'honestly', 'tbh'],
        }
        
        # Vocabulary categories
        self.vocab_categories = {
            'technical': ['algorithm', 'architecture', 'implementation', 'optimization'],
            'casual': ['cool', 'awesome', 'nice', 'great', 'sweet'],
            'formal': ['please', 'kindly', 'appreciate', 'regards', 'furthermore'],
            'questions': ['how', 'why', 'what', 'when', 'where', 'which'],
            'emphatic': ['very', 'extremely', 'highly', 'absolutely', 'definitely']
        }
    
    def _init_database(self):
        """Initialize slang vocabulary database tables"""
        Path("data").mkdir(exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Slang and vocabulary table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS slang_vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    term TEXT UNIQUE NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_tags TEXT,
                    confidence REAL DEFAULT 0.5,
                    category TEXT,
                    user_preference_score REAL DEFAULT 0.5
                )
            ''')
            
            # Phrase patterns (multi-word expressions)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS phrase_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phrase TEXT UNIQUE NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_tags TEXT,
                    typical_usage TEXT
                )
            ''')
            
            # Terminology preferences (when user prefers one term over another)
            conn.execute('''
                CREATE TABLE IF NOT EXISTS terminology_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    preferred_term TEXT NOT NULL,
                    alternative_terms TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 1,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context TEXT
                )
            ''')
            
            conn.commit()
    
    def _load_common_words(self) -> Set[str]:
        """Load common English words to filter out non-slang"""
        # Basic common words (in production, load from a comprehensive list)
        common = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
            'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
            'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
            'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
            'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
            'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
            'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
            'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us',
            'is', 'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did', 'having'
        }
        return common
    
    async def analyze_message_vocabulary(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a user message for vocabulary patterns and slang usage
        Returns vocabulary insights and updates tracking database
        """
        message_lower = message.lower()
        words = re.findall(r'\b\w+\b', message_lower)
        
        analysis = {
            'slang_detected': [],
            'technical_terms': [],
            'casual_terms': [],
            'formal_terms': [],
            'new_vocabulary': [],
            'phrases_detected': [],
            'vocabulary_style': 'neutral'
        }
        
        # Detect slang and interesting vocabulary
        for word in words:
            if word in self.common_words:
                continue
            
            # Check if it's slang/casual
            if self._is_potential_slang(word):
                analysis['slang_detected'].append(word)
                await self._record_vocabulary_usage(word, 'slang', context)
            
            # Categorize vocabulary
            for category, terms in self.vocab_categories.items():
                if word in terms:
                    analysis[f'{category}_terms'].append(word)
                    await self._record_vocabulary_usage(word, category, context)
        
        # Detect multi-word phrases
        phrases = self._extract_phrases(message)
        for phrase in phrases:
            analysis['phrases_detected'].append(phrase)
            await self._record_phrase_usage(phrase, context)
        
        # Determine overall vocabulary style
        analysis['vocabulary_style'] = self._determine_vocabulary_style(analysis)
        
        # Check for new vocabulary
        analysis['new_vocabulary'] = await self._identify_new_vocabulary(words)
        
        return analysis
    
    def _is_potential_slang(self, word: str) -> bool:
        """Determine if a word is potentially slang or casual terminology"""
        # Check abbreviation pattern
        if len(word) <= 4 and word.isalpha():
            # Could be an abbreviation (lol, btw, etc)
            return True
        
        # Check tech slang
        if word in self.slang_patterns['tech_slang']:
            return True
        
        # Check casual intensifiers/fillers
        if word in self.slang_patterns['casual_intensifiers'] or word in self.slang_patterns['casual_fillers']:
            return True
        
        # Check for unconventional spelling (repeated letters)
        if re.search(r'(.)\1{2,}', word):  # e.g., "coool", "yesss"
            return True
        
        return False
    
    def _extract_phrases(self, message: str) -> List[str]:
        """Extract common multi-word phrases from message"""
        # Common phrase patterns
        phrase_patterns = [
            r'\b(can you|could you|would you)\b',
            r'\b(thank you|thanks|thx)\b',
            r'\b(by the way|btw)\b',
            r'\b(to be honest|tbh)\b',
            r'\b(for example|for instance|e\.?g\.?)\b',
            r'\b(in other words|i\.?e\.?)\b',
            r'\b(as soon as possible|asap)\b',
            r'\b(let me know|lmk)\b',
            r'\b(talk to you later|ttyl)\b',
        ]
        
        phrases = []
        message_lower = message.lower()
        
        for pattern in phrase_patterns:
            matches = re.finditer(pattern, message_lower)
            for match in matches:
                phrases.append(match.group(0))
        
        return phrases
    
    def _determine_vocabulary_style(self, analysis: Dict[str, Any]) -> str:
        """Determine overall vocabulary style from analysis"""
        slang_count = len(analysis['slang_detected'])
        formal_count = len(analysis['formal_terms'])
        casual_count = len(analysis['casual_terms'])
        technical_count = len(analysis['technical_terms'])
        
        if formal_count > slang_count + casual_count:
            return 'formal'
        elif slang_count + casual_count > formal_count + technical_count:
            return 'casual'
        elif technical_count > 2:
            return 'technical'
        else:
            return 'neutral'
    
    async def _identify_new_vocabulary(self, words: List[str]) -> List[str]:
        """Identify words not yet seen in vocabulary database"""
        new_words = []
        
        with sqlite3.connect(self.db_path) as conn:
            for word in words:
                if word in self.common_words:
                    continue
                
                cursor = conn.execute(
                    'SELECT term FROM slang_vocabulary WHERE term = ?',
                    (word,)
                )
                
                if cursor.fetchone() is None:
                    new_words.append(word)
        
        return new_words
    
    async def _record_vocabulary_usage(self, term: str, category: str, context: Dict[str, Any]):
        """Record usage of a vocabulary term"""
        context_tags = json.dumps({
            'topic': context.get('topic', 'general'),
            'emotion': context.get('emotion', 'neutral'),
            'conversation_type': context.get('conversation_type', 'casual')
        })
        
        with sqlite3.connect(self.db_path) as conn:
            # Check if term exists
            cursor = conn.execute(
                'SELECT id, usage_count, confidence FROM slang_vocabulary WHERE term = ?',
                (term,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update existing term
                term_id, usage_count, confidence = row
                new_usage_count = usage_count + 1
                new_confidence = min(1.0, confidence + 0.05)  # Increase confidence with usage
                
                conn.execute('''
                    UPDATE slang_vocabulary
                    SET usage_count = ?, confidence = ?, last_seen = CURRENT_TIMESTAMP,
                        context_tags = ?
                    WHERE id = ?
                ''', (new_usage_count, new_confidence, context_tags, term_id))
            else:
                # Insert new term
                conn.execute('''
                    INSERT INTO slang_vocabulary
                    (term, usage_count, context_tags, confidence, category)
                    VALUES (?, 1, ?, 0.5, ?)
                ''', (term, context_tags, category))
            
            conn.commit()
    
    async def _record_phrase_usage(self, phrase: str, context: Dict[str, Any]):
        """Record usage of a multi-word phrase"""
        context_tags = json.dumps({
            'topic': context.get('topic', 'general'),
            'emotion': context.get('emotion', 'neutral')
        })
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT id, usage_count FROM phrase_patterns WHERE phrase = ?',
                (phrase,)
            )
            row = cursor.fetchone()
            
            if row:
                # Update existing phrase
                phrase_id, usage_count = row
                conn.execute('''
                    UPDATE phrase_patterns
                    SET usage_count = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (usage_count + 1, phrase_id))
            else:
                # Insert new phrase
                conn.execute('''
                    INSERT INTO phrase_patterns
                    (phrase, usage_count, context_tags)
                    VALUES (?, 1, ?)
                ''', (phrase, context_tags))
            
            conn.commit()
    
    async def get_user_vocabulary_profile(self) -> Dict[str, Any]:
        """Get comprehensive vocabulary profile of user"""
        profile = {
            'total_unique_terms': 0,
            'most_used_terms': [],
            'slang_vocabulary': [],
            'technical_vocabulary': [],
            'casual_vocabulary': [],
            'formal_vocabulary': [],
            'common_phrases': [],
            'vocabulary_diversity_score': 0.0,
            'formality_score': 0.5,
            'technical_depth_score': 0.5
        }
        
        with sqlite3.connect(self.db_path) as conn:
            # Get total unique terms
            cursor = conn.execute('SELECT COUNT(*) FROM slang_vocabulary')
            profile['total_unique_terms'] = cursor.fetchone()[0]
            
            # Get most used terms
            cursor = conn.execute('''
                SELECT term, usage_count, category
                FROM slang_vocabulary
                ORDER BY usage_count DESC
                LIMIT 20
            ''')
            profile['most_used_terms'] = [
                {'term': row[0], 'usage_count': row[1], 'category': row[2]}
                for row in cursor.fetchall()
            ]
            
            # Get vocabulary by category
            for category in ['slang', 'technical', 'casual', 'formal']:
                cursor = conn.execute('''
                    SELECT term, usage_count, confidence
                    FROM slang_vocabulary
                    WHERE category = ?
                    ORDER BY usage_count DESC
                    LIMIT 10
                ''', (category,))
                
                profile[f'{category}_vocabulary'] = [
                    {'term': row[0], 'usage_count': row[1], 'confidence': row[2]}
                    for row in cursor.fetchall()
                ]
            
            # Get common phrases
            cursor = conn.execute('''
                SELECT phrase, usage_count
                FROM phrase_patterns
                ORDER BY usage_count DESC
                LIMIT 10
            ''')
            profile['common_phrases'] = [
                {'phrase': row[0], 'usage_count': row[1]}
                for row in cursor.fetchall()
            ]
            
            # Calculate formality score (ratio of formal to casual terms)
            formal_count = len(profile['formal_vocabulary'])
            casual_count = len(profile['casual_vocabulary']) + len(profile['slang_vocabulary'])
            
            if formal_count + casual_count > 0:
                profile['formality_score'] = formal_count / (formal_count + casual_count)
            
            # Calculate technical depth score
            technical_count = len(profile['technical_vocabulary'])
            total_meaningful_terms = max(1, profile['total_unique_terms'])
            if total_meaningful_terms > 0:
                profile['technical_depth_score'] = min(1.0, technical_count / max(1, total_meaningful_terms * 0.2))
            
            # Calculate diversity score (unique terms / total usage)
            total_usage = sum(term['usage_count'] for term in profile['most_used_terms'])
            if total_usage > 0:
                profile['vocabulary_diversity_score'] = min(1.0, profile['total_unique_terms'] / total_usage)
        
        return profile
    
    async def get_vocabulary_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for how Penny should adapt vocabulary"""
        profile = await self.get_user_vocabulary_profile()
        recommendations = []
        
        # Formality recommendations
        if profile['formality_score'] > 0.7:
            recommendations.append({
                'dimension': 'communication_formality',
                'recommendation': 'increase',
                'confidence': 0.8,
                'reason': f"User uses formal language frequently (formality score: {profile['formality_score']:.2f})"
            })
        elif profile['formality_score'] < 0.3:
            recommendations.append({
                'dimension': 'communication_formality',
                'recommendation': 'decrease',
                'confidence': 0.8,
                'reason': f"User prefers casual language (formality score: {profile['formality_score']:.2f})"
            })
        
        # Technical depth recommendations
        if profile['technical_depth_score'] > 0.6:
            recommendations.append({
                'dimension': 'technical_depth_preference',
                'recommendation': 'increase',
                'confidence': 0.7,
                'reason': f"User uses technical vocabulary heavily (score: {profile['technical_depth_score']:.2f})"
            })
        elif profile['technical_depth_score'] < 0.3:
            recommendations.append({
                'dimension': 'technical_depth_preference',
                'recommendation': 'decrease',
                'confidence': 0.7,
                'reason': f"User prefers simpler explanations (tech score: {profile['technical_depth_score']:.2f})"
            })
        
        # Slang adoption recommendations
        if len(profile['slang_vocabulary']) > 5:
            slang_terms = [term['term'] for term in profile['slang_vocabulary'][:5]]
            recommendations.append({
                'dimension': 'vocabulary_adaptation',
                'recommendation': 'adopt_slang',
                'confidence': 0.6,
                'reason': f"User frequently uses slang terms: {', '.join(slang_terms)}",
                'suggested_terms': slang_terms
            })
        
        # Phrase adoption recommendations
        if profile['common_phrases']:
            common_phrases = [p['phrase'] for p in profile['common_phrases'][:3]]
            recommendations.append({
                'dimension': 'phrase_patterns',
                'recommendation': 'adopt_phrases',
                'confidence': 0.5,
                'reason': f"User commonly uses phrases: {', '.join(common_phrases)}",
                'suggested_phrases': common_phrases
            })
        
        return recommendations

    async def get_preferred_vocabulary(
        self,
        min_confidence: float = 0.5,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get user's preferred vocabulary terms with confidence >= threshold

        Args:
            min_confidence: Minimum confidence score (0.0-1.0)
            limit: Maximum number of terms to return

        Returns:
            List of vocabulary terms with metadata
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT term, usage_count, category, confidence, user_preference_score
                FROM slang_vocabulary
                WHERE confidence >= ?
                ORDER BY usage_count DESC, confidence DESC
                LIMIT ?
            ''', (min_confidence, limit))

            terms = []
            for row in cursor.fetchall():
                terms.append({
                    'term': row[0],
                    'usage_count': row[1],
                    'category': row[2] or 'general',
                    'confidence': row[3],
                    'preference_score': row[4]
                })

            return terms

    async def get_terminology_preferences(
        self,
        min_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Get user's preferred terminology (when they prefer one term over another)

        Args:
            min_confidence: Minimum confidence score

        Returns:
            List of terminology preferences
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT preferred_term, alternative_terms, confidence, usage_count, context
                FROM terminology_preferences
                WHERE confidence >= ?
                ORDER BY confidence DESC, usage_count DESC
            ''', (min_confidence,))

            prefs = []
            for row in cursor.fetchall():
                # Parse alternative_terms (stored as JSON string)
                import json
                alternative_terms = json.loads(row[1]) if row[1] else []

                prefs.append({
                    'preferred_term': row[0],
                    'alternative_terms': alternative_terms,
                    'confidence': row[2],
                    'usage_count': row[3],
                    'context': row[4]
                })

            return prefs


if __name__ == "__main__":
    import asyncio
    
    async def test_slang_tracker():
        print("🗣️ Testing Slang Vocabulary Tracker")
        print("=" * 60)
        
        tracker = SlangVocabularyTracker()
        
        # Test messages with different vocabulary styles
        test_messages = [
            ("Hey, can you help me debug this code real quick? It's totally broken lol", 
             {'topic': 'programming', 'emotion': 'frustrated'}),
            
            ("Could you please provide a comprehensive explanation of the implementation details?",
             {'topic': 'technical', 'emotion': 'neutral'}),
            
            ("btw that refactor was awesome! super clean code",
             {'topic': 'code_review', 'emotion': 'excited'}),
            
            ("I would appreciate your assistance with optimizing this algorithm",
             {'topic': 'optimization', 'emotion': 'neutral'}),
        ]
        
        print("\n📊 Analyzing Messages:")
        for message, context in test_messages:
            print(f"\nMessage: {message}")
            analysis = await tracker.analyze_message_vocabulary(message, context)
            
            print(f"  Vocabulary style: {analysis['vocabulary_style']}")
            if analysis['slang_detected']:
                print(f"  Slang detected: {', '.join(analysis['slang_detected'])}")
            if analysis['technical_terms']:
                print(f"  Technical terms: {', '.join(analysis['technical_terms'])}")
            if analysis['phrases_detected']:
                print(f"  Phrases: {', '.join(analysis['phrases_detected'])}")
        
        # Get vocabulary profile
        print("\n\n📖 User Vocabulary Profile:")
        profile = await tracker.get_user_vocabulary_profile()
        
        print(f"  Total unique terms: {profile['total_unique_terms']}")
        print(f"  Formality score: {profile['formality_score']:.2f}")
        print(f"  Technical depth score: {profile['technical_depth_score']:.2f}")
        
        if profile['most_used_terms']:
            print(f"\n  Most used terms:")
            for term_info in profile['most_used_terms'][:5]:
                print(f"    - {term_info['term']}: {term_info['usage_count']} times ({term_info['category']})")
        
        # Get recommendations
        print("\n\n💡 Vocabulary Adaptation Recommendations:")
        recommendations = await tracker.get_vocabulary_recommendations()
        
        for i, rec in enumerate(recommendations, 1):
            print(f"\n  {i}. {rec['dimension']}")
            print(f"     Action: {rec['recommendation']}")
            print(f"     Confidence: {rec['confidence']:.2f}")
            print(f"     Reason: {rec['reason']}")
            if 'suggested_terms' in rec:
                print(f"     Suggested terms: {', '.join(rec['suggested_terms'])}")
        
        print("\n✅ Slang vocabulary tracker test completed!")
    
    asyncio.run(test_slang_tracker())
