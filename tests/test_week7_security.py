"""
Week 7 Security Tests: Encryption + PII Detection

Tests the security features implemented in Week 7:
- DataEncryption (Fernet AES-128)
- PIIDetector (PII detection and filtering)
- Semantic Memory encryption integration
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.security.encryption import DataEncryption, get_encryption
from src.security.pii_detector import PIIDetector, get_pii_detector
from src.memory.semantic_memory import SemanticMemory


class TestDataEncryption:
    """Test data encryption functionality"""

    def test_encryption_basic(self):
        """Test basic encryption and decryption"""
        # Create temporary key file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as f:
            key_file = Path(f.name)

        try:
            encryptor = DataEncryption(key_file=key_file)

            # Test string encryption
            original = "joy"
            encrypted = encryptor.encrypt(original)

            # Verify encrypted is different
            assert encrypted != original
            assert len(encrypted) > 0

            # Verify decryption
            decrypted = encryptor.decrypt(encrypted)
            assert decrypted == original

        finally:
            if key_file.exists():
                key_file.unlink()

    def test_encryption_multiple_values(self):
        """Test encrypting multiple different values"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as f:
            key_file = Path(f.name)

        try:
            encryptor = DataEncryption(key_file=key_file)

            test_values = ["joy", "sadness", "anger", "fear", "positive", "negative", "0.85", "-0.32"]

            for value in test_values:
                encrypted = encryptor.encrypt(value)
                decrypted = encryptor.decrypt(encrypted)
                assert decrypted == value, f"Failed for value: {value}"

        finally:
            if key_file.exists():
                key_file.unlink()

    def test_encryption_empty_string(self):
        """Test encryption handles empty strings"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as f:
            key_file = Path(f.name)

        try:
            encryptor = DataEncryption(key_file=key_file)

            # Empty string should return empty
            assert encryptor.encrypt("") == ""
            assert encryptor.decrypt("") == ""

        finally:
            if key_file.exists():
                key_file.unlink()

    def test_selective_encryption(self):
        """Test selective field encryption"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as f:
            key_file = Path(f.name)

        try:
            encryptor = DataEncryption(key_file=key_file)

            # Test data with mix of sensitive and non-sensitive fields
            data = {
                'emotion': 'joy',
                'sentiment': 'positive',
                'sentiment_score': '0.85',
                'timestamp': '2025-12-12T10:30:00',
                'user_input': 'Hello, how are you?'
            }

            # Encrypt only sensitive fields
            encrypted_data = encryptor.encrypt_selective(
                data,
                ['emotion', 'sentiment', 'sentiment_score']
            )

            # Check sensitive fields are encrypted
            assert encrypted_data['emotion'] != 'joy'
            assert encrypted_data['sentiment'] != 'positive'
            assert encrypted_data['sentiment_score'] != '0.85'

            # Check non-sensitive fields unchanged
            assert encrypted_data['timestamp'] == '2025-12-12T10:30:00'
            assert encrypted_data['user_input'] == 'Hello, how are you?'

            # Decrypt selective fields
            decrypted_data = encryptor.decrypt_selective(
                encrypted_data,
                ['emotion', 'sentiment', 'sentiment_score']
            )

            # Verify decryption
            assert decrypted_data['emotion'] == 'joy'
            assert decrypted_data['sentiment'] == 'positive'
            assert decrypted_data['sentiment_score'] == '0.85'

        finally:
            if key_file.exists():
                key_file.unlink()

    def test_key_persistence(self):
        """Test that encryption key persists across instances"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as f:
            key_file = Path(f.name)

        try:
            # Create first encryptor and encrypt
            encryptor1 = DataEncryption(key_file=key_file)
            encrypted = encryptor1.encrypt("test_value")

            # Create second encryptor with same key file
            encryptor2 = DataEncryption(key_file=key_file)
            decrypted = encryptor2.decrypt(encrypted)

            # Verify decryption works with different instance
            assert decrypted == "test_value"

        finally:
            if key_file.exists():
                key_file.unlink()

    def test_singleton_get_encryption(self):
        """Test singleton pattern for get_encryption()"""
        enc1 = get_encryption()
        enc2 = get_encryption()

        # Should return same instance
        assert enc1 is enc2


class TestPIIDetector:
    """Test PII detection functionality"""

    def test_email_detection(self):
        """Test email address detection"""
        detector = PIIDetector()

        # Positive cases
        assert detector.contains_pii("Contact me at john@example.com")
        assert detector.contains_pii("Email: alice.smith@company.org")

        # Negative cases
        assert not detector.contains_pii("No email here")
        assert not detector.contains_pii("Just some text")

    def test_phone_detection(self):
        """Test phone number detection"""
        detector = PIIDetector()

        # Positive cases
        assert detector.contains_pii("Call me at 555-123-4567")
        assert detector.contains_pii("Phone: (555) 123-4567")
        assert detector.contains_pii("My number is 5551234567")

        # Negative cases
        assert not detector.contains_pii("No phone number here")

    def test_ssn_detection(self):
        """Test SSN detection"""
        detector = PIIDetector()

        # Positive cases
        assert detector.contains_pii("SSN: 123-45-6789")
        assert detector.contains_pii("My SSN is 123 45 6789")

        # Negative cases
        assert not detector.contains_pii("No SSN here")

    def test_company_name_detection(self):
        """Test company name detection"""
        detector = PIIDetector()

        # Positive cases
        assert detector.contains_pii("I work at Google")
        assert detector.contains_pii("Applying to Microsoft")
        assert detector.contains_pii("Interview with Anthropic")

        # Negative cases
        assert not detector.contains_pii("I work remotely")
        assert not detector.contains_pii("Looking for a job")

    def test_personal_name_detection(self):
        """Test personal name detection"""
        detector = PIIDetector()

        # Positive cases (common first names)
        assert detector.contains_pii("My friend Sarah said")
        assert detector.contains_pii("I talked to Michael yesterday")

        # Negative cases
        assert not detector.contains_pii("I talked to someone yesterday")

    def test_filter_pii_phrases(self):
        """Test filtering PII from phrase list"""
        detector = PIIDetector()

        phrases = [
            "that's fire",
            "I work at Google",
            "let's gooo",
            "Contact me at john@example.com",
            "super cool",
            "My friend Sarah said"
        ]

        safe, blocked = detector.filter_pii_phrases(phrases)

        # Check safe phrases
        assert "that's fire" in safe
        assert "let's gooo" in safe
        assert "super cool" in safe

        # Check blocked phrases
        assert "I work at Google" in blocked
        assert "Contact me at john@example.com" in blocked
        assert "My friend Sarah said" in blocked

    def test_redact_pii(self):
        """Test PII redaction"""
        detector = PIIDetector()

        # Test email redaction
        text = "Contact me at john@example.com or call 555-123-4567"
        redacted = detector.redact_pii(text)

        assert "[EMAIL]" in redacted
        assert "[PHONE]" in redacted
        assert "john@example.com" not in redacted
        assert "555-123-4567" not in redacted

    def test_get_pii_types(self):
        """Test identifying specific PII types"""
        detector = PIIDetector()

        text = "Email john@example.com, phone 555-123-4567, I work at Google"
        pii_types = detector.get_pii_types(text)

        assert 'email' in pii_types
        assert 'phone' in pii_types
        assert 'company_name' in pii_types

    def test_singleton_get_pii_detector(self):
        """Test singleton pattern for get_pii_detector()"""
        det1 = get_pii_detector()
        det2 = get_pii_detector()

        # Should return same instance
        assert det1 is det2


class TestSemanticMemoryEncryption:
    """Test semantic memory integration with encryption"""

    def test_semantic_memory_encrypts_sensitive_fields(self):
        """Test that semantic memory encrypts emotions and sentiment"""
        # Create temporary semantic memory
        semantic_memory = SemanticMemory(encrypt_sensitive=True)

        # Add conversation with emotional metadata
        turn_id = semantic_memory.add_conversation_turn(
            user_input="I'm feeling great today!",
            assistant_response="That's wonderful to hear!",
            context={
                'emotion': 'joy',
                'sentiment': 'positive',
                'sentiment_score': 0.95,
                'research_used': False
            }
        )

        # Verify turn was added
        assert turn_id is not None

        # Search should decrypt automatically
        results = semantic_memory.semantic_search("feeling great", k=1)

        assert len(results) > 0
        result = results[0]

        # Check context is decrypted
        context = result.get('context', {})
        assert context.get('emotion') == 'joy'
        assert context.get('sentiment') == 'positive'
        assert context.get('sentiment_score') == 0.95

    def test_semantic_memory_without_encryption(self):
        """Test semantic memory can run without encryption"""
        # Create semantic memory with encryption disabled
        semantic_memory = SemanticMemory(encrypt_sensitive=False)

        # Add conversation
        turn_id = semantic_memory.add_conversation_turn(
            user_input="Test message",
            assistant_response="Test response",
            context={
                'emotion': 'neutral',
                'sentiment': 'neutral'
            }
        )

        # Verify works without encryption
        assert turn_id is not None

        # Search should work
        results = semantic_memory.semantic_search("test", k=1)
        assert len(results) > 0

    def test_semantic_memory_handles_missing_sensitive_fields(self):
        """Test semantic memory handles conversations without emotional data"""
        semantic_memory = SemanticMemory(encrypt_sensitive=True)

        # Add conversation without emotion/sentiment
        turn_id = semantic_memory.add_conversation_turn(
            user_input="What's the weather?",
            assistant_response="I don't have weather data.",
            context={
                'research_used': False
            }
        )

        # Should not crash
        assert turn_id is not None

        # Search should work
        results = semantic_memory.semantic_search("weather", k=1)
        assert len(results) > 0


class TestWeek7Integration:
    """Integration tests for Week 7 architecture"""

    def test_full_encryption_pipeline(self):
        """Test end-to-end encryption in semantic memory"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as f:
            key_file = Path(f.name)

        try:
            # Initialize encryption and semantic memory
            encryptor = DataEncryption(key_file=key_file)
            semantic_memory = SemanticMemory(encrypt_sensitive=True)

            # Add multiple conversations
            conversations = [
                ("I'm so happy today!", "That's great!", {'emotion': 'joy', 'sentiment': 'positive', 'sentiment_score': 0.9}),
                ("Feeling a bit sad", "I understand", {'emotion': 'sadness', 'sentiment': 'negative', 'sentiment_score': -0.6}),
                ("Just a normal day", "Okay", {'emotion': 'neutral', 'sentiment': 'neutral', 'sentiment_score': 0.0}),
            ]

            for user, assistant, context in conversations:
                semantic_memory.add_conversation_turn(
                    user_input=user,
                    assistant_response=assistant,
                    context=context
                )

            # Search and verify decryption works
            results = semantic_memory.semantic_search("happy", k=1)
            assert len(results) > 0

            # Check first result has decrypted emotion
            context = results[0].get('context', {})
            assert context.get('emotion') in ['joy', 'sadness', 'neutral']

        finally:
            if key_file.exists():
                key_file.unlink()

    def test_pii_filtering_for_culture_learning(self):
        """Test PII filtering prevents learning sensitive phrases"""
        detector = PIIDetector()

        # Simulate culture learning phrase candidates
        learned_phrases = [
            "that's fire",  # Safe
            "no cap",  # Safe
            "let's gooo",  # Safe
            "I work at Google",  # PII - company
            "My friend Sarah loves this",  # PII - personal name
            "Email me at test@example.com",  # PII - email
            "super dope",  # Safe
        ]

        safe, blocked = detector.filter_pii_phrases(learned_phrases)

        # Verify safe phrases
        assert "that's fire" in safe
        assert "no cap" in safe
        assert "super dope" in safe

        # Verify blocked phrases
        assert "I work at Google" in blocked
        assert "My friend Sarah loves this" in blocked
        assert "Email me at test@example.com" in blocked

        # Verify we're not blocking everything
        assert len(safe) > 0
        assert len(blocked) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
