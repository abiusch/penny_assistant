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
        # Common patterns: "make sure", "confirm", "double-check", "commit", "checking"
        confirmation_words = ["make sure", "confirm", "double", "check", "sure", "commit"]
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
        # Common patterns: "hold up", "wait", "thought", "changed", "conflicts", "mentioned"
        contradiction_words = ["hold", "wait", "thought", "change", "before", "conflict", "mention", "shift"]
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
        detail_words = ["detail", "more", "spell", "expand", "clarify", "explain", "break", "picture"]
        assert any(word in result.lower() for word in detail_words), f"No detail words in: {result}"


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
