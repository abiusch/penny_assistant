# CLAUDE CODE TASK: Week 8.5 Phase 3 - Pipeline Integration

**Project:** PennyGPT AI Companion  
**Task:** Integrate Judgment & Clarify System into research_first_pipeline.py  
**Duration:** 4-6 hours  
**This is:** Part 5 of 5 for Week 8.5 - FINAL PHASE!  
**Prerequisite:** Phases 1 and 2 must be complete with all tests passing

---

## 🎯 CONTEXT

**What You Built So Far:**
- ✅ Phase 1: Complete detection layer (5 methods, 43 tests)
- ✅ Phase 2: Personality layer (Penny's voice, 18 tests)

**What We're Building in Phase 3:**
- ✅ Integrate JudgmentEngine into main pipeline
- ✅ Add clarification before tool calls
- ✅ Format responses with PennyStyleClarifier
- ✅ End-to-end testing
- ✅ **COMPLETE WEEK 8.5!**

**The Goal:**
```python
# Current flow:
User input → Tools → Response

# New flow with judgment:
User input → Judgment check → Clarify OR Tools → Response
```

---

## 📋 WHAT TO BUILD

### **Step 1: Modify `research_first_pipeline.py`**

**Add imports at top:**

```python
# Add to existing imports
from src.judgment import JudgmentEngine, PennyStyleClarifier
```

**Add judgment initialization in `__init__`:**

```python
def __init__(self, config_path: str = "config.json"):
    """Initialize the research-first pipeline."""
    # ... existing code ...
    
    # NEW: Initialize judgment system
    self.judgment_engine = JudgmentEngine()
    self.clarifier = PennyStyleClarifier()
    
    print("✅ Judgment & Clarify system initialized")
```

**Add judgment check method:**

```python
def _should_clarify(self, user_input: str, context: dict) -> tuple[bool, str]:
    """
    Check if we should clarify before proceeding.
    
    Args:
        user_input: The user's message
        context: Conversation context
    
    Returns:
        (should_clarify: bool, clarifying_question: str or None)
    
    Example:
        should_clarify, question = self._should_clarify("Fix that bug", context)
        if should_clarify:
            return question  # Ask for clarification
        # else: proceed with tools
    """
    # Build context for judgment engine
    judgment_context = {
        'conversation_history': context.get('conversation_history', []),
        'semantic_memory': context.get('semantic_memory', []),
        'emotional_state': context.get('emotional_state'),
        'personality_state': context.get('personality_state')
    }
    
    # Get judgment decision
    decision = self.judgment_engine.analyze_request(user_input, judgment_context)
    
    # If clarification needed, format in Penny's voice
    if decision.clarify_needed:
        clarifying_question = self.clarifier.format_question(
            decision,
            user_input=user_input
        )
        
        # Log judgment decision
        print(f"🤔 Judgment: Clarifying due to {decision.reasoning}")
        print(f"💬 Question: {clarifying_question}")
        
        return True, clarifying_question
    
    return False, None
```

**Modify main processing method to use judgment:**

Find the main processing method (likely `process_request` or `handle_message`) and add judgment check:

```python
def process_request(self, user_input: str, context: dict) -> str:
    """
    Process user request with judgment check.
    
    Args:
        user_input: User's message
        context: Conversation context
    
    Returns:
        Response string (either clarifying question or actual response)
    """
    # NEW: Check if we should clarify first
    should_clarify, clarifying_question = self._should_clarify(user_input, context)
    
    if should_clarify:
        # Return clarifying question instead of processing
        return clarifying_question
    
    # EXISTING: Proceed with normal processing (tools, LLM, etc.)
    # ... rest of existing code ...
```

---

### **Step 2: Add Judgment Logging**

**Create method to log judgment decisions:**

```python
def _log_judgment_decision(self, decision, user_input: str):
    """
    Log judgment decision for analysis.
    
    Useful for:
    - Understanding when judgment triggers
    - Tuning detection thresholds
    - Debugging clarification logic
    
    Args:
        decision: Decision object from JudgmentEngine
        user_input: Original user input
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_input': user_input,
        'clarify_needed': decision.clarify_needed,
        'reasoning': decision.reasoning,
        'stakes_level': decision.stakes_level.value,
        'confidence': decision.confidence,
        'intent': decision.intent
    }
    
    # Log to file for analysis
    log_file = 'data/judgment_logs.jsonl'
    os.makedirs('data', exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
```

**Call logging in `_should_clarify`:**

```python
def _should_clarify(self, user_input: str, context: dict) -> tuple[bool, str]:
    # ... existing code ...
    
    decision = self.judgment_engine.analyze_request(user_input, judgment_context)
    
    # NEW: Log decision
    self._log_judgment_decision(decision, user_input)
    
    # ... rest of existing code ...
```

---

### **Step 3: Add Configuration Options**

**Add judgment settings to config.json:**

```json
{
  "judgment": {
    "enabled": true,
    "log_decisions": true,
    "confidence_threshold": 0.4,
    "always_clarify_high_stakes": true
  }
}
```

**Read config in `__init__`:**

```python
def __init__(self, config_path: str = "config.json"):
    # ... existing code ...
    
    # Read judgment config
    self.judgment_config = self.config.get('judgment', {})
    self.judgment_enabled = self.judgment_config.get('enabled', True)
    
    if self.judgment_enabled:
        self.judgment_engine = JudgmentEngine()
        self.clarifier = PennyStyleClarifier()
        print("✅ Judgment & Clarify system initialized")
    else:
        print("⚠️  Judgment system disabled in config")
```

**Use config in `_should_clarify`:**

```python
def _should_clarify(self, user_input: str, context: dict) -> tuple[bool, str]:
    # Check if judgment is enabled
    if not self.judgment_enabled:
        return False, None
    
    # ... rest of existing code ...
```

---

### **Step 4: Create Integration Tests**

**Create file: `tests/test_week8_5_integration.py`**

```python
"""
Integration tests for Week 8.5 Judgment & Clarify System
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.judgment import JudgmentEngine, PennyStyleClarifier


class TestJudgmentIntegration:
    """Test judgment system integration end-to-end."""
    
    @pytest.fixture
    def engine(self):
        return JudgmentEngine()
    
    @pytest.fixture
    def clarifier(self):
        return PennyStyleClarifier()
    
    @pytest.fixture
    def empty_context(self):
        return {
            'conversation_history': [],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
    
    def test_vague_request_gets_penny_style_question(self, engine, clarifier, empty_context):
        """Test: Vague request → Penny-style clarifying question"""
        # User says something vague
        user_input = "Fix that thing"
        
        # Judgment detects vague referent
        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True
        
        # Clarifier formats in Penny's voice
        question = clarifier.format_question(decision, user_input)
        
        # Should be casual, not corporate
        assert "I apologize" not in question
        assert len(question) < 150
        assert "?" in question
    
    def test_clear_request_proceeds_without_clarification(self, engine, clarifier, empty_context):
        """Test: Clear request → No clarification needed"""
        user_input = "What is Python?"
        
        decision = engine.analyze_request(user_input, empty_context)
        
        # Should NOT need clarification
        assert decision.clarify_needed is False
        assert decision.confidence > 0.8
    
    def test_high_stakes_gets_confirmation(self, engine, clarifier, empty_context):
        """Test: High stakes → Confirmation question"""
        user_input = "Delete all production data"
        
        decision = engine.analyze_request(user_input, empty_context)
        
        # Should need clarification (high stakes)
        assert decision.clarify_needed is True
        assert decision.stakes_level.value == 'HIGH'
        
        # Question should indicate confirmation needed
        question = clarifier.format_question(decision, user_input)
        confirmation_words = ['sure', 'confirm', 'double', 'check']
        assert any(word in question.lower() for word in confirmation_words)
    
    def test_frustrated_user_gets_empathetic_response(self, engine, clarifier, empty_context):
        """Test: Frustrated user → Empathetic but brief clarification"""
        user_input = "Just fix the fucking bug already"
        
        # Clarifier detects frustration
        is_frustrated = clarifier.detect_frustration(user_input)
        assert is_frustrated is True
        
        # Still needs clarification (vague "the bug")
        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True
        
        # Question should be empathetic
        question = clarifier.format_question(decision, user_input)
        
        # Should acknowledge but still clarify
        assert len(question) > 0
        # Should not be dismissive
        assert "whatever" not in question.lower()
    
    def test_missing_params_gets_parameter_question(self, engine, clarifier, empty_context):
        """Test: Missing params → Question about specific param"""
        user_input = "Schedule a meeting"
        
        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True
        
        question = clarifier.format_question(decision, user_input)
        
        # Should ask about date/time
        assert "date" in question.lower() or "time" in question.lower()
    
    def test_contradiction_detected_and_questioned(self, engine, clarifier):
        """Test: Contradiction → Question about what changed"""
        context = {
            'conversation_history': [
                {'role': 'user', 'content': 'I prefer Rust for this project'}
            ],
            'semantic_memory': [],
            'emotional_state': None,
            'personality_state': None
        }
        
        user_input = "Use Python for the API"
        
        decision = engine.analyze_request(user_input, context)
        assert decision.clarify_needed is True
        
        question = clarifier.format_question(decision, user_input)
        
        # Should reference the contradiction
        contradiction_words = ['hold', 'wait', 'thought', 'change']
        assert any(word in question.lower() for word in contradiction_words)
    
    def test_end_to_end_flow(self, engine, clarifier, empty_context):
        """Test: Complete flow from user input to Penny response"""
        # Scenario: User asks vague question
        user_input = "Debug it"
        
        # Step 1: Judgment detects issue
        decision = engine.analyze_request(user_input, empty_context)
        assert decision.clarify_needed is True
        assert decision.confidence < 0.5
        
        # Step 2: Format in Penny's voice
        question = clarifier.format_question(decision, user_input)
        
        # Step 3: Verify output is Penny-like
        assert isinstance(question, str)
        assert len(question) > 10
        assert len(question) < 150
        assert "?" in question
        
        # Should be casual
        penny_markers = ['quick', 'real', 'check', 'need', 'what']
        assert any(marker in question.lower() for marker in penny_markers)


class TestPipelineIntegration:
    """Test integration with research_first_pipeline if available."""
    
    def test_pipeline_has_judgment_engine(self):
        """Test: Pipeline has judgment engine initialized"""
        try:
            from research_first_pipeline import ResearchFirstPipeline
            pipeline = ResearchFirstPipeline()
            
            # Should have judgment components
            assert hasattr(pipeline, 'judgment_engine')
            assert hasattr(pipeline, 'clarifier')
        except ImportError:
            pytest.skip("research_first_pipeline not found")
    
    def test_pipeline_clarifies_vague_requests(self):
        """Test: Pipeline uses judgment for vague requests"""
        try:
            from research_first_pipeline import ResearchFirstPipeline
            pipeline = ResearchFirstPipeline()
            
            # Test with vague request
            response = pipeline.process_request("Fix that bug", {})
            
            # Should be a clarifying question (short, ends with ?)
            assert len(response) < 200
            assert "?" in response
        except ImportError:
            pytest.skip("research_first_pipeline not found")
    
    def test_pipeline_proceeds_with_clear_requests(self):
        """Test: Pipeline doesn't clarify clear requests"""
        try:
            from research_first_pipeline import ResearchFirstPipeline
            pipeline = ResearchFirstPipeline()
            
            # Test with clear request
            response = pipeline.process_request("What is 2+2?", {})
            
            # Should process normally (might be longer, might have answer)
            # At minimum, should not be asking for clarification
            # (This is a weak test - improve based on actual pipeline behavior)
            assert len(response) > 0
        except ImportError:
            pytest.skip("research_first_pipeline not found")


class TestJudgmentLogging:
    """Test judgment decision logging."""
    
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
    
    def test_logs_created_on_decision(self, engine, empty_context):
        """Test: Judgment decisions are logged"""
        # This test assumes logging is implemented
        # Adjust based on actual implementation
        
        user_input = "Fix that bug"
        decision = engine.analyze_request(user_input, empty_context)
        
        # Verify decision has necessary fields for logging
        assert hasattr(decision, 'clarify_needed')
        assert hasattr(decision, 'reasoning')
        assert hasattr(decision, 'confidence')
        assert hasattr(decision, 'stakes_level')


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

---

### **Step 5: Create Simple Demo Script**

**Create file: `demo_week8_5.py`**

```python
"""
Demo script for Week 8.5 Judgment & Clarify System

Shows how the judgment system works end-to-end.
"""

from src.judgment import JudgmentEngine, PennyStyleClarifier

def demo_judgment_system():
    """Demonstrate the judgment system with various scenarios."""
    
    print("=" * 60)
    print("🧠 WEEK 8.5 JUDGMENT & CLARIFY SYSTEM DEMO")
    print("=" * 60)
    print()
    
    # Initialize
    engine = JudgmentEngine()
    clarifier = PennyStyleClarifier()
    
    # Empty context for demos
    empty_context = {
        'conversation_history': [],
        'semantic_memory': [],
        'emotional_state': None,
        'personality_state': None
    }
    
    # Test scenarios
    scenarios = [
        ("Fix that thing", "Vague referent"),
        ("Delete all production data", "High stakes"),
        ("Schedule a meeting", "Missing parameters"),
        ("What is Python?", "Clear question - no clarification"),
        ("Just fix the fucking bug already", "Frustrated user"),
    ]
    
    for user_input, description in scenarios:
        print(f"📝 Scenario: {description}")
        print(f"👤 User: \"{user_input}\"")
        print()
        
        # Get judgment decision
        decision = engine.analyze_request(user_input, empty_context)
        
        print(f"   🤔 Judgment Analysis:")
        print(f"      - Clarify needed: {decision.clarify_needed}")
        print(f"      - Confidence: {decision.confidence:.2f}")
        print(f"      - Stakes: {decision.stakes_level.value}")
        print(f"      - Reasoning: {decision.reasoning}")
        print()
        
        if decision.clarify_needed:
            # Format in Penny's voice
            question = clarifier.format_question(decision, user_input)
            print(f"   💬 Penny: \"{question}\"")
        else:
            print(f"   ✅ Penny: Proceeding with request (no clarification needed)")
        
        print()
        print("-" * 60)
        print()
    
    print("✅ Demo complete!")
    print()
    print("Summary:")
    print("  - Vague requests → Get clarification")
    print("  - High stakes → Get confirmation")
    print("  - Missing params → Ask for details")
    print("  - Clear requests → Proceed directly")
    print("  - Frustrated users → Empathetic clarification")

if __name__ == '__main__':
    demo_judgment_system()
```

---

## ✅ DELIVERABLES

**Phase 3 Checklist:**
- [ ] `research_first_pipeline.py` modified with judgment integration
- [ ] `_should_clarify()` method implemented
- [ ] `_log_judgment_decision()` method implemented (optional but recommended)
- [ ] Config options added for judgment system
- [ ] `tests/test_week8_5_integration.py` created with 10+ tests
- [ ] `demo_week8_5.py` created for demonstrations
- [ ] All 71+ tests passing (61 from Phase 1+2, 10+ new)
- [ ] Judgment system working end-to-end
- [ ] **WEEK 8.5 COMPLETE!** 🎉

---

## 🎯 SUCCESS CRITERIA

**You'll know it's working when:**

```python
# Run demo
python demo_week8_5.py

# Output should show:
# ✅ Vague requests getting clarification
# ✅ High stakes getting confirmation
# ✅ Clear requests proceeding directly
# ✅ Frustrated users getting empathetic responses

# Run integration tests
pytest tests/test_week8_5_integration.py -v

# All tests should pass
```

---

## 📊 WEEK 8.5 FINAL STATUS

**After Phase 3:**
- ✅ Phase 1: Detection Layer (43 tests)
- ✅ Phase 2: Personality Layer (18 tests)
- ✅ Phase 3: Pipeline Integration (10+ tests)
- ✅ **TOTAL: 71+ tests passing**
- ✅ **WEEK 8.5 COMPLETE!**

**What you built:**
1. ✅ 5 detection methods (vague, stakes, params, contradictions, confidence)
2. ✅ Penny-style clarifier with 30+ templates
3. ✅ Frustration detection
4. ✅ Full pipeline integration
5. ✅ Logging and configuration
6. ✅ Comprehensive test coverage

---

## 🎉 AFTER COMPLETION

**Week 8.5 protects all future learning!**

Now ready for:
- Week 9-10: Hebbian Learning (safe - judgment prevents bad patterns)
- Week 11: Outcome Tracking (reliable - judgment ensures clear inputs)
- Week 12: Goal Continuity (protected - judgment maintains clarity)
- Week 13: User Model (accurate - judgment prevents wrong assumptions)

---

## 💡 TESTING TIPS

**Key integration tests:**
1. Vague input → Penny-style clarification
2. Clear input → Proceeds directly
3. High stakes → Gets confirmation
4. Frustrated user → Empathetic response
5. Missing params → Asks for details
6. Contradiction → Questions the change

**Expected behavior:**
- Clarifying questions are always in Penny's voice
- No corporate speak ever appears
- Questions are brief (< 150 chars)
- Frustration is detected and handled gracefully
- Clear requests proceed without unnecessary clarification

---

**Ready to complete Week 8.5! Final push! 🚀**
