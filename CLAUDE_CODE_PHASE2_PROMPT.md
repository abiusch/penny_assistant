# CLAUDE CODE TASK: Week 8.5 Phase 2 - Personality Layer

**Project:** PennyGPT AI Companion  
**Task:** Format clarifying questions in Penny's voice  
**Duration:** 4-6 hours  
**This is:** Part 4 of 5 for Week 8.5  
**Prerequisite:** Phase 1 (1A, 1B, 1C) must be complete with all tests passing

---

## 🎯 CONTEXT

**What You Built in Phase 1:**
- ✅ Complete JudgmentEngine with 5 detection methods
- ✅ Detects: vague referents, high stakes, missing params, contradictions, low confidence
- ✅ Returns raw questions like: "vague_referent: action=fix" or "high_stakes: confirm=delete, scope=all"

**What We're Building in Phase 2:**
- ✅ PennyStyleClarifier - Formats raw questions in Penny's authentic voice
- ✅ Different templates for different trigger types
- ✅ Frustration detection (be gentler if user is frustrated)
- ✅ Keep it casual, confident, witty - NO corporate speak!

**The Goal:**
Raw question → Penny-style question

```python
# Before Phase 2:
"vague_referent: action=fix" 

# After Phase 2:
"Quick check—you mean the auth bug or the TTS latency?"
```

---

## 📋 WHAT TO BUILD

### **Create File: `src/judgment/penny_style_clarifier.py`**

```python
"""
Penny Style Clarifier - Formats clarifying questions in Penny's voice.

Rules:
- Casual, confident, playful
- Max 1-2 questions at a time
- No long disclaimers
- Quick "why I'm asking" in Penny tone
- Empathetic if user frustrated
"""

from typing import Dict, List, Optional
import random
import re
from .judgment_engine import Decision, StakesLevel

class PennyStyleClarifier:
    """
    Formats clarifying questions in Penny's authentic voice.
    
    Personality traits:
    - Casual, confident, witty
    - Direct, no hedging
    - Uses slang when appropriate
    - Sassy but constructive
    - Enthusiastic
    
    Anti-patterns to avoid:
    - Corporate speak ("I apologize, but...")
    - Over-explaining
    - Multiple questions at once
    - Hedging ("perhaps", "maybe")
    - Long disclaimers
    """
    
    def __init__(self):
        """Initialize clarifier with Penny-style templates."""
        
        # Templates for vague referents
        self.VAGUE_REFERENT_TEMPLATES = [
            "Quick check so I don't go off into the weeds—do you mean {option_a} or {option_b}?",
            "Before I sprint in the wrong direction: {clarification}?",
            "Two-second check: {clarification}?",
            "Real quick—{clarification}?",
            "Just to nail this—{clarification}?",
        ]
        
        # Templates for missing parameters
        self.MISSING_PARAM_TEMPLATES = [
            "Two-second clarity question: what's the {param}?",
            "Real quick—what's the {param} here?",
            "Need one detail: {param}?",
            "Quick Q: {param}?",
            "What's the {param}?",
        ]
        
        # Templates for high stakes
        self.HIGH_STAKES_TEMPLATES = [
            "Wanna make sure I nail this—{clarification}?",
            "Let me double-check before I do something irreversible: {clarification}?",
            "Quick confirmation so I don't mess this up: {clarification}?",
            "Before I commit: {clarification}?",
            "Just checking—{clarification}? (Don't wanna yeet the wrong thing)",
        ]
        
        # Templates for contradictions
        self.CONTRADICTION_TEMPLATES = [
            "Hold up—last time we talked about {past_context}. Did that change?",
            "Quick sanity check: earlier you mentioned {past}, now saying {current}. Which is current?",
            "Wait—I thought we were doing {past}. Did the plan shift?",
            "Heads up: this conflicts with {past_context}. What's the new direction?",
            "Real quick—before we switched from {past}, what changed?",
        ]
        
        # Templates for low confidence
        self.LOW_CONFIDENCE_TEMPLATES = [
            "Wanna spell that out a bit more? Not 100% sure what you're after.",
            "Can you give me a bit more detail? Wanna make sure I get this right.",
            "What's the full picture here? Need a couple more details.",
            "Break that down for me? Wanna make sure I'm tracking.",
            "Can you expand on that? Want to nail this for you.",
        ]
        
        # Frustrated user templates (gentler but still Penny)
        self.FRUSTRATED_TEMPLATES = [
            "On it—quick check so I don't waste time: {clarification}?",
            "Got it—one quick thing: {clarification}?",
            "Absolutely—just need: {clarification}?",
            "Hear you—real quick: {clarification}?",
            "I'm on this—just need to know: {clarification}?",
        ]
        
        # Frustration indicators
        self.FRUSTRATION_INDICATORS = [
            'fuck', 'shit', 'damn', 'already', 'just', 'come on',
            'jesus', 'christ', 'dammit', 'god', 'please', 'hurry'
        ]
    
    def format_question(
        self, 
        decision: Decision,
        user_input: str = "",
        user_seems_frustrated: bool = False
    ) -> str:
        """
        Format clarifying question in Penny's voice.
        
        Args:
            decision: Decision object from JudgmentEngine
            user_input: Original user input (for frustration detection)
            user_seems_frustrated: Override frustration detection
        
        Returns:
            Formatted question in Penny's style (1-2 sentences max)
        
        Examples:
            Input: "vague_referent: action=fix"
            Output: "Quick check—you mean the auth bug or the TTS latency?"
            
            Input: "high_stakes: confirm=delete, scope=all"
            Output: "Wanna make sure I nail this—you mean delete ALL items?"
        """
        # Detect frustration if not provided
        if not user_seems_frustrated and user_input:
            user_seems_frustrated = self.detect_frustration(user_input)
        
        # Parse the raw question
        raw_question = decision.clarify_question
        
        # Route to appropriate formatter based on question type
        if raw_question.startswith("vague_referent:"):
            return self._format_vague_referent(raw_question, user_seems_frustrated)
        
        elif raw_question.startswith("missing_param:"):
            return self._format_missing_param(raw_question, user_seems_frustrated)
        
        elif raw_question.startswith("high_stakes:"):
            return self._format_high_stakes(raw_question, user_seems_frustrated)
        
        elif raw_question.startswith("contradiction:"):
            return self._format_contradiction(raw_question, user_seems_frustrated)
        
        elif raw_question.startswith("low_confidence:"):
            return self._format_low_confidence(raw_question, user_seems_frustrated)
        
        else:
            # Fallback for unknown format
            return "Can you give me a bit more detail on that?"
    
    def _format_vague_referent(self, raw_question: str, frustrated: bool) -> str:
        """Format vague referent question."""
        # Example input: "vague_referent: action=fix"
        
        if frustrated:
            # Use gentler frustrated templates
            template = random.choice(self.FRUSTRATED_TEMPLATES)
            return template.format(clarification="which specific thing")
        
        # Parse action if present
        action = ""
        if "action=" in raw_question:
            action = raw_question.split("action=")[1].strip()
        
        # Choose template
        template = random.choice(self.VAGUE_REFERENT_TEMPLATES)
        
        # Format based on whether we have specific options
        if "or" in raw_question or "option_" in raw_question:
            # Has specific options
            return template.format(
                option_a="the first thing",
                option_b="the second thing",
                clarification="which one specifically"
            )
        else:
            # Generic clarification
            clarification = f"which {action} exactly" if action else "which thing specifically"
            return template.format(
                option_a="X",
                option_b="Y",
                clarification=clarification
            )
    
    def _format_missing_param(self, raw_question: str, frustrated: bool) -> str:
        """Format missing parameter question."""
        # Example input: "missing_param: action=schedule, needs=date, time"
        
        if frustrated:
            template = random.choice(self.FRUSTRATED_TEMPLATES)
            return template.format(clarification="what's the date and time")
        
        # Extract what's needed
        needs = []
        if "needs=" in raw_question:
            needs_str = raw_question.split("needs=")[1].strip()
            needs = [n.strip() for n in needs_str.split(",")]
        
        # Choose template
        template = random.choice(self.MISSING_PARAM_TEMPLATES)
        
        # Format parameter list
        if len(needs) > 1:
            param = " and ".join(needs)
        elif needs:
            param = needs[0]
        else:
            param = "details"
        
        return template.format(param=param)
    
    def _format_high_stakes(self, raw_question: str, frustrated: bool) -> str:
        """Format high stakes confirmation question."""
        # Example input: "high_stakes: confirm=delete, scope=all items"
        
        if frustrated:
            # Still need confirmation even if frustrated
            template = "I hear you—just need to confirm: {clarification}?"
        else:
            template = random.choice(self.HIGH_STAKES_TEMPLATES)
        
        # Extract confirmation details
        action = "do this"
        scope = ""
        
        if "confirm=" in raw_question:
            action = raw_question.split("confirm=")[1].split(",")[0].strip()
        
        if "scope=" in raw_question:
            scope = raw_question.split("scope=")[1].strip()
        
        # Build clarification
        if scope:
            clarification = f"you mean {action} {scope}"
        else:
            clarification = f"you're sure about this {action}"
        
        return template.format(clarification=clarification)
    
    def _format_contradiction(self, raw_question: str, frustrated: bool) -> str:
        """Format contradiction clarification question."""
        # Example input: "contradiction: past=Rust, now=Python"
        
        if frustrated:
            return "Real quick—I thought we were doing something else. What changed?"
        
        # Extract past and current
        past = "something else"
        current = "this"
        
        if "past=" in raw_question:
            past = raw_question.split("past=")[1].split(",")[0].strip()
        
        if "now=" in raw_question:
            current = raw_question.split("now=")[1].strip()
        
        # Choose template
        template = random.choice(self.CONTRADICTION_TEMPLATES)
        
        return template.format(
            past_context=past,
            past=past,
            current=current
        )
    
    def _format_low_confidence(self, raw_question: str, frustrated: bool) -> str:
        """Format low confidence clarification question."""
        # Example input: "low_confidence: unclear_what, unclear_action"
        
        if frustrated:
            return "Got it—can you spell that out a bit more so I nail this?"
        
        # Choose template
        template = random.choice(self.LOW_CONFIDENCE_TEMPLATES)
        
        return template
    
    def detect_frustration(self, user_input: str) -> bool:
        """
        Detect if user seems frustrated.
        
        Indicators:
        - Profanity
        - "just", "already", "come on"
        - ALL CAPS (multiple words)
        - Multiple punctuation marks (!!!, ???)
        
        Args:
            user_input: The user's message
        
        Returns:
            True if frustration detected
        
        Examples:
            "Just fix the fucking bug already" → True
            "JUST DO IT" → True
            "Can you help me?" → False
        """
        input_lower = user_input.lower()
        
        # Check for profanity or frustration words
        if any(indicator in input_lower for indicator in self.FRUSTRATION_INDICATORS):
            return True
        
        # Check for ALL CAPS (at least 2 words)
        words = user_input.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 2]
        if len(caps_words) >= 2:
            return True
        
        # Check for multiple punctuation marks
        if '!!!' in user_input or '???' in user_input or '!!' in user_input:
            return True
        
        return False
    
    def add_context_hint(
        self, 
        question: str, 
        decision: Decision
    ) -> str:
        """
        Optionally add brief "I can help once I know" hint.
        
        Only adds if:
        - Intent is clear
        - Question isn't already too long
        - Would be genuinely helpful
        
        Args:
            question: Already formatted question
            decision: Decision object with intent
        
        Returns:
            Question with optional context hint
        
        Example:
            Input: "Quick check—you mean the auth bug or TTS latency?"
            Output: "Quick check—you mean the auth bug or TTS latency? I can fix it once I know which one."
        """
        # Don't add hint if question is already long
        if len(question) > 100:
            return question
        
        # Don't add hint if no clear intent
        if not decision.intent or decision.intent == 'general_request':
            return question
        
        # Map intents to helpful hints
        intent_hints = {
            'fix_issue': "I can fix it once I know which one.",
            'create_something': "I can create it once I know the details.",
            'delete_something': "I can delete it once I confirm.",
            'get_explanation': "I can explain once I know what specifically.",
        }
        
        hint = intent_hints.get(decision.intent)
        if hint:
            return f"{question} {hint}"
        
        return question
```

---

### **Update File: `src/judgment/__init__.py`**

Add PennyStyleClarifier to exports:

```python
"""
Judgment & Clarify System

Prevents drift in learning systems by detecting when to clarify vs answer.
"""

from .judgment_engine import JudgmentEngine, Decision, StakesLevel, ResponseStrategy
from .penny_style_clarifier import PennyStyleClarifier

__all__ = [
    'JudgmentEngine', 
    'Decision', 
    'StakesLevel', 
    'ResponseStrategy',
    'PennyStyleClarifier'
]
```

---

### **Create Tests: `tests/test_penny_style_clarifier.py`**

```python
"""
Tests for Phase 2: Penny Style Clarifier
"""

import pytest
from src.judgment.judgment_engine import JudgmentEngine, Decision, StakesLevel, ResponseStrategy
from src.judgment.penny_style_clarifier import PennyStyleClarifier


class TestPennyStyleBasics:
    """Test basic functionality of PennyStyleClarifier."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_clarifier_initializes(self, clarifier):
        """Test: Clarifier initializes with templates"""
        assert clarifier is not None
        assert len(clarifier.VAGUE_REFERENT_TEMPLATES) > 0
        assert len(clarifier.MISSING_PARAM_TEMPLATES) > 0
        assert len(clarifier.HIGH_STAKES_TEMPLATES) > 0
    
    def test_format_question_returns_string(self, clarifier):
        """Test: format_question returns a string"""
        decision = Decision(
            intent="fix_issue",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="vague_referent: action=fix",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.3,
            reasoning="Test"
        )
        
        result = clarifier.format_question(decision)
        assert isinstance(result, str)
        assert len(result) > 0


class TestFrustrationDetection:
    """Test frustration detection."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_detects_profanity(self, clarifier):
        """Test: Detects profanity as frustration"""
        assert clarifier.detect_frustration("Just fix the fucking bug") is True
        assert clarifier.detect_frustration("This shit isn't working") is True
    
    def test_detects_just_already(self, clarifier):
        """Test: Detects 'just' and 'already' as frustration indicators"""
        assert clarifier.detect_frustration("Just do it already") is True
        assert clarifier.detect_frustration("Come on, already!") is True
    
    def test_detects_all_caps(self, clarifier):
        """Test: Detects ALL CAPS as frustration"""
        assert clarifier.detect_frustration("JUST FIX IT") is True
        assert clarifier.detect_frustration("DO IT NOW") is True
    
    def test_detects_multiple_punctuation(self, clarifier):
        """Test: Detects multiple punctuation as frustration"""
        assert clarifier.detect_frustration("Fix this!!!") is True
        assert clarifier.detect_frustration("What is this???") is True
    
    def test_no_frustration_normal_text(self, clarifier):
        """Test: Normal text is not flagged as frustrated"""
        assert clarifier.detect_frustration("Can you help me?") is False
        assert clarifier.detect_frustration("Please fix the bug") is False
        assert clarifier.detect_frustration("What's the status?") is False


class TestVagueReferentFormatting:
    """Test formatting of vague referent questions."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_formats_vague_referent_normally(self, clarifier):
        """Test: Vague referent gets casual Penny-style question"""
        decision = Decision(
            intent="fix_issue",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="vague_referent: action=fix",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.3,
            reasoning="Vague"
        )
        
        result = clarifier.format_question(decision)
        
        # Should be casual, not corporate
        assert "I apologize" not in result
        assert "perhaps" not in result
        assert "maybe" not in result
        
        # Should be short
        assert len(result) < 150
    
    def test_formats_vague_referent_when_frustrated(self, clarifier):
        """Test: Frustrated user gets gentler response"""
        decision = Decision(
            intent="fix_issue",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="vague_referent: action=fix",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.3,
            reasoning="Vague"
        )
        
        result = clarifier.format_question(
            decision, 
            user_input="Just fix the fucking thing already",
            user_seems_frustrated=True
        )
        
        # Should still clarify but be empathetic
        assert len(result) > 0
        # Should not be dismissive
        assert "whatever" not in result.lower()


class TestMissingParamFormatting:
    """Test formatting of missing parameter questions."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_formats_missing_single_param(self, clarifier):
        """Test: Missing single parameter formatted clearly"""
        decision = Decision(
            intent="create_something",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="missing_param: action=schedule, needs=date",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.5,
            reasoning="Missing param"
        )
        
        result = clarifier.format_question(decision)
        
        # Should mention the parameter
        assert "date" in result.lower()
        # Should be concise
        assert len(result) < 100
    
    def test_formats_missing_multiple_params(self, clarifier):
        """Test: Missing multiple parameters formatted with 'and'"""
        decision = Decision(
            intent="create_something",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="missing_param: action=schedule, needs=date, time",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.5,
            reasoning="Missing params"
        )
        
        result = clarifier.format_question(decision)
        
        # Should mention both parameters
        assert "date" in result.lower() or "time" in result.lower()


class TestHighStakesFormatting:
    """Test formatting of high stakes questions."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_formats_high_stakes_with_confirmation(self, clarifier):
        """Test: High stakes gets confirmation tone"""
        decision = Decision(
            intent="delete_something",
            stakes_level=StakesLevel.HIGH,
            clarify_needed=True,
            clarify_question="high_stakes: confirm=delete, scope=all test data",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.8,
            reasoning="High stakes"
        )
        
        result = clarifier.format_question(decision)
        
        # Should indicate it's asking for confirmation
        # Common patterns: "make sure", "confirm", "double-check"
        confirmation_words = ["make sure", "confirm", "double", "check", "sure"]
        assert any(word in result.lower() for word in confirmation_words)


class TestContradictionFormatting:
    """Test formatting of contradiction questions."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_formats_contradiction_with_context(self, clarifier):
        """Test: Contradiction mentions what changed"""
        decision = Decision(
            intent="general_request",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="contradiction: past=Rust, now=Python",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.5,
            reasoning="Contradiction"
        )
        
        result = clarifier.format_question(decision)
        
        # Should reference the contradiction somehow
        # Common patterns: "hold up", "wait", "thought", "changed"
        contradiction_words = ["hold", "wait", "thought", "change", "before"]
        assert any(word in result.lower() for word in contradiction_words)


class TestLowConfidenceFormatting:
    """Test formatting of low confidence questions."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_formats_low_confidence_asks_for_details(self, clarifier):
        """Test: Low confidence asks for more details"""
        decision = Decision(
            intent="general_request",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="low_confidence: unclear_what, unclear_action",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.2,
            reasoning="Low confidence"
        )
        
        result = clarifier.format_question(decision)
        
        # Should ask for more information
        detail_words = ["detail", "more", "spell", "expand", "clarify", "explain"]
        assert any(word in result.lower() for word in detail_words)


class TestContextHints:
    """Test optional context hint additions."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_adds_context_hint_when_appropriate(self, clarifier):
        """Test: Context hint added for clear intent"""
        decision = Decision(
            intent="fix_issue",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="vague_referent: action=fix",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.3,
            reasoning="Vague"
        )
        
        question = "Quick check—which bug?"
        result = clarifier.add_context_hint(question, decision)
        
        # Should add hint for clear intent
        assert len(result) >= len(question)
    
    def test_no_hint_for_long_questions(self, clarifier):
        """Test: No hint added if question already long"""
        decision = Decision(
            intent="fix_issue",
            stakes_level=StakesLevel.LOW,
            clarify_needed=True,
            clarify_question="vague_referent: action=fix",
            response_strategy=ResponseStrategy.CLARIFY,
            confidence=0.3,
            reasoning="Vague"
        )
        
        long_question = "This is already a very long question that goes on and on and probably doesn't need any additional context hints added to it."
        result = clarifier.add_context_hint(long_question, decision)
        
        # Should not add hint if already long
        assert result == long_question


class TestPersonalityConsistency:
    """Test that all outputs maintain Penny's personality."""
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    def test_no_corporate_speak_in_any_template(self, clarifier):
        """Test: No corporate language in any output"""
        corporate_phrases = [
            "i apologize",
            "i'm sorry for",
            "thank you for your patience",
            "we appreciate",
            "kindly",
            "per your request"
        ]
        
        # Check all template lists
        all_templates = (
            clarifier.VAGUE_REFERENT_TEMPLATES +
            clarifier.MISSING_PARAM_TEMPLATES +
            clarifier.HIGH_STAKES_TEMPLATES +
            clarifier.CONTRADICTION_TEMPLATES +
            clarifier.LOW_CONFIDENCE_TEMPLATES +
            clarifier.FRUSTRATED_TEMPLATES
        )
        
        for template in all_templates:
            template_lower = template.lower()
            for phrase in corporate_phrases:
                assert phrase not in template_lower, f"Found corporate phrase '{phrase}' in template: {template}"
    
    def test_questions_are_concise(self, clarifier):
        """Test: All formatted questions are concise (< 150 chars)"""
        test_decisions = [
            Decision(
                intent="fix_issue",
                stakes_level=StakesLevel.LOW,
                clarify_needed=True,
                clarify_question="vague_referent: action=fix",
                response_strategy=ResponseStrategy.CLARIFY,
                confidence=0.3,
                reasoning="Test"
            ),
            Decision(
                intent="create_something",
                stakes_level=StakesLevel.LOW,
                clarify_needed=True,
                clarify_question="missing_param: action=schedule, needs=date",
                response_strategy=ResponseStrategy.CLARIFY,
                confidence=0.5,
                reasoning="Test"
            ),
            Decision(
                intent="delete_something",
                stakes_level=StakesLevel.HIGH,
                clarify_needed=True,
                clarify_question="high_stakes: confirm=delete, scope=all",
                response_strategy=ResponseStrategy.CLARIFY,
                confidence=0.8,
                reasoning="Test"
            ),
        ]
        
        for decision in test_decisions:
            result = clarifier.format_question(decision)
            assert len(result) < 150, f"Question too long: {result}"


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

## ✅ DELIVERABLES

**Phase 2 Checklist:**
- [ ] `src/judgment/penny_style_clarifier.py` created
- [ ] PennyStyleClarifier class complete with all formatters
- [ ] Templates sound like Penny (casual, confident, witty)
- [ ] Frustration detection implemented
- [ ] Context hint functionality added
- [ ] `src/judgment/__init__.py` updated with exports
- [ ] `tests/test_penny_style_clarifier.py` created with 20+ tests
- [ ] All tests passing
- [ ] No corporate speak in any template
- [ ] All questions under 150 characters

---

## 🎯 SUCCESS CRITERIA

**You'll know it's working when:**

```python
engine = JudgmentEngine()
clarifier = PennyStyleClarifier()

# Test vague referent
decision = engine.analyze_request("Fix that thing", {})
question = clarifier.format_question(decision)
print(question)
# Output: "Quick check—which thing specifically?"

# Test high stakes
decision = engine.analyze_request("Delete all test data", {})
question = clarifier.format_question(decision)
print(question)
# Output: "Wanna make sure I nail this—you mean delete ALL items?"

# Test frustration handling
decision = engine.analyze_request("Fix that bug", {})
question = clarifier.format_question(decision, "Just fix the fucking bug already")
print(question)
# Output: "Got it—one quick thing: which bug specifically?"
```

---

## 🎨 PERSONALITY GUIDELINES

**Penny's voice is:**
- ✅ Casual ("Quick check", "Real quick")
- ✅ Confident (no hedging, direct)
- ✅ Witty (occasional sass)
- ✅ Enthusiastic ("Wanna nail this")
- ✅ Brief (1-2 sentences max)

**Penny NEVER:**
- ❌ Apologizes unnecessarily
- ❌ Uses corporate speak
- ❌ Hedges ("perhaps", "maybe")
- ❌ Over-explains
- ❌ Asks multiple questions at once

---

## 📝 TESTING APPROACH

**Test categories:**
1. Basic functionality (initialization, returns strings)
2. Frustration detection (profanity, caps, punctuation)
3. Each trigger type (vague, missing param, high stakes, contradiction, low confidence)
4. Personality consistency (no corporate speak, concise)
5. Context hints (when to add, when not to)
6. Edge cases (long questions, empty inputs)

**Expected test count:** 20-25 tests

---

## 🎉 PHASE 2 COMPLETE!

**After Phase 2, you'll have:**
- ✅ Complete detection layer (Phase 1)
- ✅ Personality layer (Phase 2)
- ✅ Questions formatted in Penny's authentic voice
- ✅ Frustration handling
- ✅ All templates tested

**Next:**
- Phase 3: Pipeline Integration (connect to research_first_pipeline.py)

---

**Ready to make Penny's clarifications sound authentic! 🎨🚀**
