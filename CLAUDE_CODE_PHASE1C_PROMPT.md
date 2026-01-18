# CLAUDE CODE TASK: Week 8.5 Phase 1C - Contradictions & Confidence

**Project:** PennyGPT AI Companion  
**Task:** Add contradiction detection and confidence assessment  
**Duration:** 2-3 hours  
**This is:** Part 3 of 5 for Week 8.5  
**Prerequisite:** Phases 1A and 1B must be complete and working

---

## 🎯 CONTEXT

**What You Built So Far:**
- ✅ Phase 1A: Vague referent detection
- ✅ Phase 1B: Stakes assessment + missing parameter detection

**What We're Adding in Phase 1C:**
- ✅ Contradiction detection (conflicts with past context)
- ✅ Confidence assessment (how sure are we about understanding?)
- ✅ Complete the detection layer!

**Why These Two Together:**
Both involve comparing current request with PAST context/memory to detect potential issues.

---

## 📋 WHAT TO BUILD

### **Modify File: `src/judgment/judgment_engine.py`**

**Add to `__init__` method:**

```python
def __init__(self):
    """Initialize judgment engine with detection patterns."""
    # Existing from Phase 1A and 1B...
    self.vague_referents = [...]
    self.high_stakes_keywords = {...}
    self.actions_requiring_params = {...}
    self.context_window = 50
    
    # NEW: Preference/decision keywords
    self.preference_keywords = [
        'prefer', 'like', 'want', 'should', 'use',
        'choose', 'go with', 'decided', 'planning'
    ]
    
    # NEW: Contradiction indicators
    self.contradiction_phrases = [
        'actually', 'instead', 'rather', 'change my mind',
        'on second thought', 'wait', 'no', 'not'
    ]
    
    # NEW: Confidence thresholds
    self.high_confidence_threshold = 0.8
    self.low_confidence_threshold = 0.4
```

---

**Modify `analyze_request` method to use confidence:**

```python
def analyze_request(
    self, 
    user_input: str, 
    context: dict
) -> Decision:
    """
    Analyze user request and decide whether to clarify or answer.
    
    Args:
        user_input: Current user message
        context: Dictionary with conversation history, memory, etc.
    
    Returns:
        Decision object with structured response strategy
    """
    # Phase 1A: Check vague referents
    has_vague_referent = self._detect_vague_referents(user_input, context)
    
    # Phase 1B: Check stakes level
    stakes = self._assess_stakes(user_input, context)
    
    # Phase 1B: Check for missing parameters
    missing_param = self._detect_missing_params(user_input, context)
    
    # Phase 1C: NEW - Check for contradictions
    has_contradiction = self._detect_contradiction(user_input, context)
    
    # Phase 1C: NEW - Assess confidence
    confidence = self._assess_confidence(user_input, context)
    
    # Extract intent
    intent = self._extract_intent(user_input)
    
    # Decide whether to clarify
    clarify_needed = (
        has_vague_referent or
        missing_param or
        (stakes == StakesLevel.HIGH) or
        has_contradiction or
        (stakes == StakesLevel.MEDIUM and confidence < self.low_confidence_threshold)
    )
    
    if clarify_needed:
        # Generate appropriate question based on trigger priority
        if has_contradiction:
            question = self._generate_clarifying_question_for_contradiction(
                user_input, context
            )
            reasoning = "Contradiction detected with past context"
        elif has_vague_referent:
            question = self._generate_clarifying_question_for_vague_referent(
                user_input, context
            )
            reasoning = "Vague referent detected without clear antecedent"
        elif missing_param:
            question = self._generate_clarifying_question_for_missing_param(
                user_input, context
            )
            reasoning = "Missing required parameter for this action"
        elif stakes == StakesLevel.HIGH:
            question = self._generate_clarifying_question_for_high_stakes(
                user_input, context
            )
            reasoning = "High-stakes action requires confirmation"
        else:  # Low confidence
            question = self._generate_clarifying_question_for_low_confidence(
                user_input, context
            )
            reasoning = f"Low confidence ({confidence:.2f}) in understanding request"
        
        return Decision(
            intent=intent,
            stakes_level=stakes,
            clarify_needed=True,
            clarify_question=question,
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=confidence,
            reasoning=reasoning
        )
    else:
        return Decision(
            intent=intent,
            stakes_level=stakes,
            clarify_needed=False,
            clarify_question=None,
            response_strategy=ResponseStrategy.ANSWER,
            confidence=confidence,
            reasoning="Clear request, proceed with answer"
        )
```

---

**Add new method: `_detect_contradiction`**

```python
def _detect_contradiction(self, user_input: str, context: dict) -> bool:
    """
    Detect contradictions with past context/memory.
    
    Looks for:
    - Preference reversals ("I prefer X" → "Use Y")
    - Decision changes ("Decided on X" → "Let's do Y")
    - Explicit contradictions ("actually", "instead", "change my mind")
    
    Args:
        user_input: The user's message
        context: Context dictionary with conversation_history
    
    Returns:
        True if contradiction detected
    
    Examples:
        Past: "I prefer Rust for this project"
        Now: "Use Python for the API"
        → Contradiction detected
        
        Past: "We decided to use MongoDB"
        Now: "Set up PostgreSQL"
        → Contradiction detected
        
        No past context → No contradiction possible
    """
    # If no conversation history, can't have contradiction
    conversation_history = context.get('conversation_history', [])
    if not conversation_history:
        return False
    
    input_lower = user_input.lower()
    
    # Check for explicit contradiction phrases
    if any(phrase in input_lower for phrase in self.contradiction_phrases):
        # User is explicitly changing something
        return True
    
    # Look for preference/decision keywords in current input
    has_preference_keyword = any(
        keyword in input_lower 
        for keyword in self.preference_keywords
    )
    
    if not has_preference_keyword:
        # Current input doesn't express preference/decision
        # Look for tech stack or tool mentions that might contradict past
        tech_keywords = self._extract_tech_keywords(user_input)
        if tech_keywords:
            # Check recent history for conflicting tech mentions
            for past_msg in conversation_history[-5:]:  # Last 5 messages
                if past_msg.get('role') == 'user':
                    past_content = past_msg.get('content', '').lower()
                    past_tech = self._extract_tech_keywords(past_content)
                    
                    # If past mentioned different tech for similar context
                    if past_tech and past_tech != tech_keywords:
                        # Simple contradiction check
                        if any(keyword in past_content for keyword in self.preference_keywords):
                            return True
    
    # Check recent conversation history for contradicting preferences
    for past_msg in conversation_history[-3:]:  # Last 3 messages only
        if past_msg.get('role') == 'user':
            past_content = past_msg.get('content', '').lower()
            
            # Check if past message had preference keyword
            if any(keyword in past_content for keyword in self.preference_keywords):
                # Compare entities mentioned
                # Simple heuristic: if different nouns, might be contradiction
                current_nouns = self._extract_key_nouns(user_input)
                past_nouns = self._extract_key_nouns(past_content)
                
                # If both have nouns and they're different
                if current_nouns and past_nouns and not current_nouns.intersection(past_nouns):
                    # Likely contradiction
                    return True
    
    return False
```

---

**Add new method: `_assess_confidence`**

```python
def _assess_confidence(self, user_input: str, context: dict) -> float:
    """
    Assess confidence in understanding the request.
    
    Factors that LOWER confidence:
    - Very short input (< 3 words)
    - Many vague terms
    - Ambiguous pronouns
    - No clear action verb
    - Missing context
    
    Factors that RAISE confidence:
    - Specific nouns (file names, clear references)
    - Clear action verbs
    - Complete parameters
    - Detailed request
    
    Args:
        user_input: The user's message
        context: Context dictionary
    
    Returns:
        Confidence score 0.0-1.0
        - 0.8-1.0: High confidence
        - 0.4-0.8: Medium confidence
        - 0.0-0.4: Low confidence
    
    Examples:
        "Fix it" → 0.2 (very vague, short)
        "Fix the authentication bug in user_login.py" → 0.9 (specific)
        "What's 2+2?" → 0.95 (clear question)
        "Do the thing" → 0.15 (extremely vague)
    """
    # Start with baseline confidence
    confidence = 0.7
    
    # Factor 1: Input length
    words = user_input.split()
    word_count = len(words)
    
    if word_count < 3:
        confidence -= 0.3  # Very short
    elif word_count < 5:
        confidence -= 0.15  # Short
    elif word_count > 8:
        confidence += 0.1  # Detailed
    
    # Factor 2: Vague referents
    vague_count = sum(
        1 for ref in self.vague_referents 
        if ref in user_input.lower()
    )
    confidence -= (vague_count * 0.15)
    
    # Factor 3: Specific nouns (file names, clear terms)
    has_specific_noun = self._has_specific_noun(user_input)
    if has_specific_noun:
        confidence += 0.15
    
    # Factor 4: Clear action verb
    action = self._extract_action_verb(user_input)
    if action and action != 'do':
        confidence += 0.1
    
    # Factor 5: Question words (usually clear intent)
    question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
    if any(user_input.lower().startswith(q) for q in question_words):
        confidence += 0.15
    
    # Factor 6: Has context from conversation history
    conversation_history = context.get('conversation_history', [])
    if conversation_history:
        confidence += 0.05  # Slight boost for having context
    
    # Clamp to 0.0-1.0 range
    confidence = max(0.0, min(1.0, confidence))
    
    return confidence
```

---

**Add helper method: `_extract_tech_keywords`**

```python
def _extract_tech_keywords(self, text: str) -> set:
    """
    Extract technology/tool keywords from text.
    
    Used for detecting contradictions like:
    "Use Python" → "Use Rust"
    
    Args:
        text: Text to extract from
    
    Returns:
        Set of tech keywords found
    """
    tech_keywords = {
        'python', 'rust', 'javascript', 'typescript', 'go', 'java',
        'react', 'vue', 'angular', 'svelte',
        'postgres', 'postgresql', 'mysql', 'mongodb', 'redis',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes',
        'fastapi', 'django', 'flask', 'express'
    }
    
    text_lower = text.lower()
    found = set()
    
    for keyword in tech_keywords:
        if keyword in text_lower:
            found.add(keyword)
    
    return found
```

---

**Add helper method: `_extract_key_nouns`**

```python
def _extract_key_nouns(self, text: str) -> set:
    """
    Extract key nouns from text (simple heuristic).
    
    Used for detecting contradictions in preferences.
    
    Args:
        text: Text to extract from
    
    Returns:
        Set of likely nouns (words > 3 chars, not common words)
    """
    # Common words to ignore
    common_words = {
        'the', 'this', 'that', 'with', 'from', 'have', 'would',
        'should', 'could', 'will', 'can', 'want', 'need', 'like',
        'prefer', 'use', 'make', 'get', 'take'
    }
    
    words = text.lower().split()
    nouns = set()
    
    for word in words:
        # Clean word (remove punctuation)
        clean_word = ''.join(c for c in word if c.isalnum())
        
        # Keep words that are likely nouns
        if (len(clean_word) > 3 and 
            clean_word not in common_words and
            clean_word not in self.vague_referents):
            nouns.add(clean_word)
    
    return nouns
```

---

**Add helper method: `_has_specific_noun`**

```python
def _has_specific_noun(self, text: str) -> bool:
    """
    Check if text contains specific nouns (file names, clear references).
    
    Indicators of specific nouns:
    - Contains file extensions (.py, .js, .md)
    - Contains underscores or hyphens (variable_name, file-name)
    - Contains technical terms
    
    Args:
        text: Text to check
    
    Returns:
        True if specific noun found
    """
    # File extensions
    extensions = ['.py', '.js', '.ts', '.md', '.txt', '.json', '.yaml', '.sql']
    if any(ext in text for ext in extensions):
        return True
    
    # Snake_case or kebab-case identifiers
    if '_' in text or '-' in text:
        # Make sure it's not just a hyphen in regular text
        words = text.split()
        if any('_' in word or (word.count('-') >= 2) for word in words):
            return True
    
    # Technical/specific terms (longer words)
    words = text.split()
    long_words = [w for w in words if len(w) > 8]
    if long_words:
        return True
    
    return False
```

---

**Add new method: `_generate_clarifying_question_for_contradiction`**

```python
def _generate_clarifying_question_for_contradiction(
    self,
    user_input: str,
    context: dict
) -> str:
    """
    Generate clarifying question for detected contradiction.
    
    Returns raw question that will be styled by personality layer.
    
    Args:
        user_input: The user's message
        context: Context dictionary with conversation_history
    
    Returns:
        Raw clarifying question
    
    Example:
        Past: "Use Rust"
        Now: "Use Python"
        → "contradiction: past=Rust, now=Python"
    """
    # Extract what changed
    current_tech = self._extract_tech_keywords(user_input)
    
    # Find past tech from recent history
    past_tech = set()
    conversation_history = context.get('conversation_history', [])
    for past_msg in conversation_history[-5:]:
        if past_msg.get('role') == 'user':
            past_content = past_msg.get('content', '')
            past_tech.update(self._extract_tech_keywords(past_content))
    
    # Generate question
    if current_tech and past_tech:
        past_str = ', '.join(past_tech)
        current_str = ', '.join(current_tech)
        return f"contradiction: past={past_str}, now={current_str}"
    else:
        return "contradiction: conflicting_with_previous_statement"
```

---

**Add new method: `_generate_clarifying_question_for_low_confidence`**

```python
def _generate_clarifying_question_for_low_confidence(
    self,
    user_input: str,
    context: dict
) -> str:
    """
    Generate clarifying question for low confidence understanding.
    
    Returns raw question that will be styled by personality layer.
    
    Args:
        user_input: The user's message
        context: Context dictionary
    
    Returns:
        Raw clarifying question
    
    Example:
        "Do it" → "low_confidence: unclear_what, unclear_how"
    """
    # Identify what's unclear
    unclear_aspects = []
    
    # Check for vague referents
    if any(ref in user_input.lower() for ref in self.vague_referents):
        unclear_aspects.append('unclear_what')
    
    # Check for missing action
    action = self._extract_action_verb(user_input)
    if not action or action == 'do':
        unclear_aspects.append('unclear_action')
    
    # Check for missing details
    if len(user_input.split()) < 4:
        unclear_aspects.append('needs_details')
    
    aspects_str = ', '.join(unclear_aspects) if unclear_aspects else 'unclear_request'
    return f"low_confidence: {aspects_str}"
```

---

### **Add Tests: `tests/test_judgment_engine_phase1c.py`**

```python
"""
Tests for Phase 1C: Contradiction Detection and Confidence Assessment
"""

import pytest
from src.judgment.judgment_engine import (
    JudgmentEngine,
    StakesLevel,
    ResponseStrategy
)


class TestContradictionDetection:
    """Test contradiction detection with past context."""
    
    @pytest.fixture
    def engine(self):
        return JudgmentEngine()
    
    def test_contradiction_tech_stack(self, engine):
        """Test: Contradicting tech stack preference"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'I prefer Rust for this project'},
                {'role': 'assistant', 'content': 'Sounds good!'}
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request("Use Python for the API", context)
        
        # Should detect contradiction
        assert decision.clarify_needed is True
        assert "contradiction" in decision.clarify_question or "contradiction" in decision.reasoning.lower()
    
    def test_explicit_contradiction_phrase(self, engine):
        """Test: User says 'actually' or 'instead'"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'Set up MongoDB'},
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request("Actually, use PostgreSQL instead", context)
        
        assert decision.clarify_needed is True
        # User explicitly changed mind, should detect
    
    def test_no_contradiction_without_context(self, engine):
        """Test: No contradiction possible without past context"""
        empty_context = {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request("Use Python", empty_context)
        
        # Can't have contradiction without past context
        # Might clarify for OTHER reasons, but not contradiction
        assert "contradiction" not in decision.reasoning.lower()
    
    def test_no_contradiction_same_tech(self, engine):
        """Test: No contradiction if same preference"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'Use Python for this'},
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request("Let's write the Python script", context)
        
        # Same tech, no contradiction
        # Might clarify for other reasons, but not contradiction
        if decision.clarify_needed:
            assert "contradiction" not in decision.reasoning.lower()


class TestConfidenceAssessment:
    """Test confidence scoring."""
    
    @pytest.fixture
    def engine(self):
        return JudgmentEngine()
    
    @pytest.fixture
    def empty_context(self):
        return {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
    
    def test_high_confidence_specific_request(self, engine, empty_context):
        """Test: Specific request has high confidence"""
        decision = engine.analyze_request(
            "Fix the authentication bug in user_login.py",
            empty_context
        )
        
        assert decision.confidence > 0.7
        # Specific file name, clear action, detailed
    
    def test_low_confidence_vague_request(self, engine, empty_context):
        """Test: Vague request has low confidence"""
        decision = engine.analyze_request("Fix it", empty_context)
        
        assert decision.confidence < 0.5
        # Very short, vague referent "it"
    
    def test_high_confidence_clear_question(self, engine, empty_context):
        """Test: Clear question has high confidence"""
        decision = engine.analyze_request("What is Python?", empty_context)
        
        assert decision.confidence > 0.8
        # Clear question, specific term
    
    def test_medium_confidence_moderate_detail(self, engine, empty_context):
        """Test: Moderate detail gives medium confidence"""
        decision = engine.analyze_request("Create a new file", empty_context)
        
        assert 0.4 < decision.confidence < 0.8
        # Clear action, but missing details
    
    def test_very_low_confidence_extremely_vague(self, engine, empty_context):
        """Test: Extremely vague request has very low confidence"""
        decision = engine.analyze_request("Do the thing", empty_context)
        
        assert decision.confidence < 0.4
        # Multiple vague terms, short, unclear


class TestPhase1CIntegration:
    """Test all three phases working together."""
    
    @pytest.fixture
    def engine(self):
        return JudgmentEngine()
    
    def test_all_clear_high_confidence(self, engine):
        """Test: Everything clear, high confidence, no clarification"""
        context = {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request(
            "What is the capital of France?",
            context
        )
        
        assert decision.clarify_needed is False
        assert decision.confidence > 0.8
        assert decision.stakes_level == StakesLevel.LOW
        assert decision.response_strategy == ResponseStrategy.ANSWER
    
    def test_multiple_triggers_prioritize_contradiction(self, engine):
        """Test: Contradiction takes priority when multiple triggers"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'I decided to use MongoDB'},
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request(
            "Actually use that other database",  # vague + contradiction
            context
        )
        
        assert decision.clarify_needed is True
        # Should prioritize contradiction in reasoning
        assert "contradiction" in decision.reasoning.lower()
    
    def test_medium_stakes_low_confidence_clarify(self, engine):
        """Test: Medium stakes + low confidence → clarify"""
        context = {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        decision = engine.analyze_request(
            "Send that email",  # medium stakes, vague
            context
        )
        
        assert decision.clarify_needed is True
        # Either due to vague referent OR low confidence + medium stakes
    
    def test_complete_detection_layer_working(self, engine):
        """Test: Full detection layer integration"""
        # Test 1: Vague
        decision1 = engine.analyze_request("Fix that bug", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision1.clarify_needed is True
        
        # Test 2: High stakes
        decision2 = engine.analyze_request("Delete all production data", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision2.clarify_needed is True
        assert decision2.stakes_level == StakesLevel.HIGH
        
        # Test 3: Missing params
        decision3 = engine.analyze_request("Schedule a meeting", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision3.clarify_needed is True
        
        # Test 4: Clear request
        decision4 = engine.analyze_request("What is Python?", {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        })
        assert decision4.clarify_needed is False


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## ✅ DELIVERABLES

**Phase 1C Checklist:**
- [ ] `judgment_engine.py` modified with contradiction detection
- [ ] `judgment_engine.py` modified with confidence assessment
- [ ] `_detect_contradiction()` method implemented
- [ ] `_assess_confidence()` method implemented
- [ ] Helper methods implemented (_extract_tech_keywords, _extract_key_nouns, etc.)
- [ ] Question generators for new triggers implemented
- [ ] `tests/test_judgment_engine_phase1c.py` created
- [ ] All 15+ tests passing
- [ ] Phase 1A and 1B tests still passing (no regression)
- [ ] **DETECTION LAYER COMPLETE!** ✅

---

## 🎯 SUCCESS CRITERIA

**You'll know it's working when:**

```python
engine = JudgmentEngine()

# Contradiction - should clarify
context_with_history = {
    'conversation_history': [
        {'role': 'user', 'content': 'I prefer Rust'}
    ],
    'semantic_memory': [],
    'emotional_state': None,
    'personality_state': None
}
decision = engine.analyze_request("Use Python", context_with_history)
assert decision.clarify_needed == True

# High confidence - should NOT clarify
decision = engine.analyze_request("What is Python?", {})
assert decision.confidence > 0.8
assert decision.clarify_needed == False

# Low confidence - should clarify
decision = engine.analyze_request("Do it", {})
assert decision.confidence < 0.4
assert decision.clarify_needed == True
```

---

## 🎉 PHASE 1 COMPLETE!

**After Phase 1C, you'll have:**
- ✅ Complete detection layer
- ✅ 5 detection methods (vague, stakes, params, contradiction, confidence)
- ✅ ~40-50 tests covering all scenarios
- ✅ Robust decision-making logic

**Next Steps:**
- Phase 2: Personality Layer (format questions in Penny's voice)
- Phase 3: Pipeline Integration (connect to research_first_pipeline.py)

---

**Ready to complete the detection layer? Let's finish Phase 1C!** 🚀
