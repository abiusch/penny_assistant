"""
PII Detection Module
Detects and filters personally identifiable information

WEEK 7: Security Foundation (prep for Week 8-9 Culture Learning)
- Prevents learning company names, project names, personal names
- Blocks emails, phone numbers, SSNs, credit cards from phrase learning
- Protects against data leaks in logs or compromised databases
"""

import re
from typing import List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class PIIDetector:
    """
    Detect and filter personally identifiable information.

    This protects users from accidentally leaking:
    - Email addresses
    - Phone numbers
    - SSNs, credit card numbers
    - Company names ("I work at Google")
    - Project names ("working on Project Phoenix")
    - Personal names (first/last names)
    - Street addresses

    Used by Culture Learning (Week 8-9) to prevent adopting PII-containing phrases.
    """

    def __init__(self):
        """Initialize PII detector with regex patterns and known entity lists"""

        # Compile regex patterns for common PII
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        self.phone_pattern = re.compile(
            r'\b(?:\+?1[-.]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        )

        self.ssn_pattern = re.compile(
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b'
        )

        self.credit_card_pattern = re.compile(
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        )

        # Street address patterns (basic)
        self.address_pattern = re.compile(
            r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)\b',
            re.IGNORECASE
        )

        # Company indicators (Inc, LLC, Corp, etc.)
        self.company_indicators = {
            'Inc', 'LLC', 'Corp', 'Corporation', 'Ltd', 'Limited',
            'Company', 'Co.', 'Incorporated', 'L.L.C.', 'L.P.',
            'Technologies', 'Systems', 'Solutions', 'Group', 'Holdings'
        }

        # Load known company names (top tech companies, banks, etc.)
        self.known_companies = self._load_company_names()

        # Common first names (subset for detection)
        self.common_first_names = self._load_common_names()

    def _load_company_names(self) -> Set[str]:
        """
        Load list of known company names.

        TODO: Could load from external file for comprehensive coverage
        """
        return {
            # Big Tech
            'Google', 'Microsoft', 'Apple', 'Amazon', 'Facebook', 'Meta',
            'Netflix', 'Tesla', 'SpaceX', 'Twitter', 'X', 'LinkedIn',
            'Uber', 'Lyft', 'Airbnb', 'Stripe', 'Square', 'PayPal',

            # AI Companies
            'Anthropic', 'OpenAI', 'DeepMind', 'Cohere', 'Hugging Face',
            'Stability AI', 'Midjourney', 'Character.AI',

            # Banks/Finance
            'Goldman Sachs', 'Morgan Stanley', 'JPMorgan', 'Chase',
            'Bank of America', 'Wells Fargo', 'Citigroup', 'Citi',

            # Consulting/Services
            'McKinsey', 'Bain', 'BCG', 'Deloitte', 'PwC', 'EY', 'KPMG',
            'Accenture', 'IBM', 'Oracle', 'SAP', 'Salesforce',

            # Add more as needed
        }

    def _load_common_names(self) -> Set[str]:
        """
        Load common first names for detection.

        TODO: Could load from census data or external file
        """
        return {
            # Top 100 US first names (subset)
            'James', 'John', 'Robert', 'Michael', 'William', 'David',
            'Richard', 'Joseph', 'Thomas', 'Charles', 'Christopher',
            'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven',
            'Paul', 'Andrew', 'Joshua', 'Kenneth', 'Kevin', 'Brian',
            'George', 'Edward', 'Ronald', 'Timothy', 'Jason', 'Jeffrey',
            'Ryan', 'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan',
            'Stephen', 'Larry', 'Justin', 'Scott', 'Brandon', 'Benjamin',
            'Samuel', 'Raymond', 'Gregory', 'Frank', 'Alexander', 'Patrick',
            'Mary', 'Patricia', 'Jennifer', 'Linda', 'Barbara', 'Elizabeth',
            'Susan', 'Jessica', 'Sarah', 'Karen', 'Nancy', 'Lisa', 'Betty',
            'Margaret', 'Sandra', 'Ashley', 'Kimberly', 'Emily', 'Donna',
            'Michelle', 'Dorothy', 'Carol', 'Amanda', 'Melissa', 'Deborah',
            'Stephanie', 'Rebecca', 'Sharon', 'Laura', 'Cynthia', 'Kathleen',
            'Amy', 'Angela', 'Shirley', 'Anna', 'Brenda', 'Pamela', 'Emma',
            'Nicole', 'Helen', 'Samantha', 'Katherine', 'Christine', 'Debra',
            'Rachel', 'Carolyn', 'Janet', 'Catherine', 'Maria', 'Heather',
        }

    def contains_pii(self, text: str) -> bool:
        """
        Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected, False otherwise
        """
        # Quick checks with regex
        if self.email_pattern.search(text):
            return True
        if self.phone_pattern.search(text):
            return True
        if self.ssn_pattern.search(text):
            return True
        if self.credit_card_pattern.search(text):
            return True
        if self.address_pattern.search(text):
            return True

        # Check for company names (case-insensitive)
        words = text.split()
        for word in words:
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:()"\'')

            # Check exact match with known companies
            if clean_word in self.known_companies:
                return True

            # Check for company indicators
            if any(indicator in clean_word for indicator in self.company_indicators):
                return True

        # Check for common first names (potential personal names)
        # Only flag if capitalized (proper noun)
        for word in words:
            clean_word = word.strip('.,!?;:()"\'')
            if clean_word in self.common_first_names:
                return True

        return False

    def get_pii_types(self, text: str) -> List[str]:
        """
        Return list of PII types found in text.

        Args:
            text: Text to analyze

        Returns:
            List of PII type strings (e.g., ['email', 'phone', 'company_name'])
        """
        pii_types = []

        if self.email_pattern.search(text):
            pii_types.append('email')

        if self.phone_pattern.search(text):
            pii_types.append('phone')

        if self.ssn_pattern.search(text):
            pii_types.append('ssn')

        if self.credit_card_pattern.search(text):
            pii_types.append('credit_card')

        if self.address_pattern.search(text):
            pii_types.append('street_address')

        # Check for companies
        words = text.split()
        for word in words:
            clean_word = word.strip('.,!?;:()"\'')
            if clean_word in self.known_companies:
                pii_types.append('company_name')
                break

        # Check for personal names
        for word in words:
            clean_word = word.strip('.,!?;:()"\'')
            if clean_word in self.common_first_names:
                pii_types.append('personal_name')
                break

        # Check for company indicators
        for word in words:
            if any(indicator in word for indicator in self.company_indicators):
                pii_types.append('company_indicator')
                break

        return list(set(pii_types))  # Remove duplicates

    def filter_pii_phrases(self, phrases: List[str], min_frequency: int = 10) -> Tuple[List[str], List[str]]:
        """
        Filter out phrases containing PII.

        Used by Culture Learning (Week 8-9) to prevent learning sensitive phrases.

        Args:
            phrases: List of candidate phrases to learn
            min_frequency: Minimum frequency threshold (default: 10)

        Returns:
            Tuple of (safe_phrases, blocked_phrases)

        Example:
            >>> detector = PIIDetector()
            >>> phrases = ["that's fire", "I work at Google", "let's gooo"]
            >>> safe, blocked = detector.filter_pii_phrases(phrases)
            >>> safe
            ["that's fire", "let's gooo"]
            >>> blocked
            ["I work at Google"]
        """
        safe_phrases = []
        blocked_phrases = []

        for phrase in phrases:
            if self.contains_pii(phrase):
                blocked_phrases.append(phrase)
                logger.warning(f"🚫 PII detected, blocked phrase learning: '{phrase[:30]}...'")
            else:
                safe_phrases.append(phrase)

        return safe_phrases, blocked_phrases

    def redact_pii(self, text: str) -> str:
        """
        Redact PII from text (replace with [REDACTED]).

        Args:
            text: Text containing PII

        Returns:
            Text with PII redacted

        Example:
            >>> detector = PIIDetector()
            >>> detector.redact_pii("Contact me at john@example.com or 555-123-4567")
            "Contact me at [EMAIL] or [PHONE]"
        """
        result = text

        # Redact emails
        result = self.email_pattern.sub('[EMAIL]', result)

        # Redact phone numbers
        result = self.phone_pattern.sub('[PHONE]', result)

        # Redact SSNs
        result = self.ssn_pattern.sub('[SSN]', result)

        # Redact credit cards
        result = self.credit_card_pattern.sub('[CREDIT_CARD]', result)

        # Redact addresses
        result = self.address_pattern.sub('[ADDRESS]', result)

        return result


# Singleton instance for module-level access
_pii_detector_instance = None


def get_pii_detector() -> PIIDetector:
    """
    Get singleton PII detector instance.

    Returns:
        PIIDetector instance
    """
    global _pii_detector_instance
    if _pii_detector_instance is None:
        _pii_detector_instance = PIIDetector()
    return _pii_detector_instance


__all__ = ['PIIDetector', 'get_pii_detector']
