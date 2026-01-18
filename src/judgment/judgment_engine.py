"""
Judgment Engine - Detects when to clarify vs answer immediately.

Prevents learning systems from reinforcing patterns based on ambiguous inputs.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum

class StakesLevel(Enum):
    """Risk level of the request"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ResponseStrategy(Enum):
    """How Penny should respond"""
    ANSWER = "answer"      # Proceed with normal answer
    CLARIFY = "clarify"    # Ask clarifying question first
    TOOL = "tool"          # Use tool first
    ESCALATE = "escalate"  # Defer to user

@dataclass
class Decision:
    """
    Structured decision about how to respond to user input.

    Attributes:
        intent: What the user wants (extracted from input)
        stakes_level: Risk level of the request
        clarify_needed: Whether clarification is needed
        clarify_question: The raw question to ask (if needed)
        response_strategy: How Penny should respond
        confidence: Confidence in understanding (0.0-1.0)
        reasoning: Why this decision was made
    """
    intent: str
    stakes_level: StakesLevel
    clarify_needed: bool
    clarify_question: Optional[str]
    response_strategy: ResponseStrategy
    confidence: float  # 0.0-1.0
    reasoning: str


class JudgmentEngine:
    """
    Detects when Penny should clarify vs answer immediately.

    Purpose:
        Prevents drift by ensuring learning systems only learn from
        clear, unambiguous inputs.

    Detection Methods (Phase 1A - implement vague referent detection):
        - Vague referents: "that", "it", "the thing" without clear antecedent
        - Missing parameters: TBD in Phase 1B
        - High stakes: TBD in Phase 1B
        - Contradictions: TBD in Phase 1C
        - Low confidence: TBD in Phase 1C
    """

    def __init__(self):
        """Initialize judgment engine with detection patterns."""
        # Patterns that indicate vague/ambiguous references
        self.vague_referents = [
            "that", "it", "this", "these",
            "those", "them", "one", "stuff", "issue"
        ]

        # Vague nouns that don't clarify anything
        self.vague_nouns = [
            "thing", "things", "stuff", "one", "ones"
        ]

        # Common action verbs that aren't nouns
        self.action_verbs = [
            'fix', 'delete', 'create', 'update', 'build',
            'remove', 'add', 'change', 'modify', 'debug',
            'make', 'do', 'get', 'set', 'run', 'start',
            'stop', 'restart', 'install', 'uninstall',
            'schedule', 'meeting', 'send', 'email', 'deploy',
            'move', 'copy'
        ]

        # Phase 1B: High-stakes keywords
        self.high_stakes_keywords = {
            'financial': ['invest', 'buy', 'sell', 'transfer', 'payment',
                         'money', 'pay', 'purchase', 'transaction'],
            'destructive': ['delete', 'remove', 'drop', 'destroy', 'erase',
                           'wipe', 'clear', 'purge', 'truncate'],
            'medical': ['medical', 'health', 'diagnosis', 'prescription',
                       'treatment', 'surgery', 'medicine', 'drug'],
            'legal': ['legal', 'contract', 'sign', 'agreement',
                     'lawsuit', 'sue', 'liability']
        }

        # Phase 1B: Action verbs that require parameters
        self.actions_requiring_params = {
            'schedule': ['date', 'time'],
            'meeting': ['date', 'time', 'attendees'],
            'send': ['recipient', 'content'],
            'email': ['recipient', 'subject'],
            'deploy': ['environment', 'version'],
            'create': ['name', 'type'],
            'move': ['source', 'destination'],
            'copy': ['source', 'destination']
        }

        # Context window size for checking antecedents
        self.context_window = 50  # characters to look back

        # Phase 1C: Preference/decision keywords
        self.preference_keywords = [
            'prefer', 'like', 'want', 'should', 'use',
            'choose', 'go with', 'decided', 'planning'
        ]

        # Phase 1C: Contradiction indicators
        self.contradiction_phrases = [
            'actually', 'instead', 'rather', 'change my mind',
            'on second thought', 'wait', 'no', 'not'
        ]

        # Phase 1C: Confidence thresholds
        self.high_confidence_threshold = 0.8
        self.low_confidence_threshold = 0.4

    def analyze_request(
        self,
        user_input: str,
        context: dict
    ) -> Decision:
        """
        Analyze user request and decide whether to clarify or answer.

        Args:
            user_input: Current user message
            context: Dictionary with:
                - 'conversation_history': List of recent message dicts
                    Each dict has: {'role': 'user'/'assistant', 'content': str}
                - 'semantic_memory': List of relevant past conversations
                - 'emotional_state': Current emotion detection result
                - 'personality_state': Current personality dimensions

        Returns:
            Decision object with structured response strategy

        Example:
            >>> engine = JudgmentEngine()
            >>> decision = engine.analyze_request(
            ...     "Fix that thing",
            ...     {'conversation_history': []}
            ... )
            >>> decision.clarify_needed
            True
        """
        # Phase 1A: Check vague referents
        has_vague_referent = self._detect_vague_referents(user_input, context)

        # Phase 1B: Check stakes level
        stakes = self._assess_stakes(user_input, context)

        # Phase 1B: Check for missing parameters
        missing_param = self._detect_missing_params(user_input, context)

        # Phase 1C: Check for contradictions
        has_contradiction = self._detect_contradiction(user_input, context)

        # Phase 1C: Assess confidence
        confidence = self._assess_confidence(user_input, context)

        # Extract intent
        intent = self._extract_intent(user_input)

        # Decide whether to clarify
        clarify_needed = (
            has_vague_referent or
            missing_param or
            stakes in [StakesLevel.MEDIUM, StakesLevel.HIGH] or  # MEDIUM and HIGH both trigger
            has_contradiction
        )

        if clarify_needed:
            # Generate appropriate question based on trigger priority
            if has_contradiction:
                question = self._generate_clarifying_question_for_contradiction(
                    user_input, context
                )
                reasoning = "Contradiction detected with past context"
                strategy = ResponseStrategy.CLARIFY
            elif has_vague_referent:
                question = self._generate_clarifying_question_for_vague_referent(
                    user_input, context
                )
                reasoning = "Vague referent detected without clear antecedent"
                strategy = ResponseStrategy.CLARIFY
            elif missing_param:
                question = self._generate_clarifying_question_for_missing_param(
                    user_input, context
                )
                reasoning = "Missing required parameter for this action"
                strategy = ResponseStrategy.CLARIFY
            elif stakes in [StakesLevel.MEDIUM, StakesLevel.HIGH]:
                question = self._generate_clarifying_question_for_high_stakes(
                    user_input, context
                )
                reasoning = f"{stakes.value.upper()} stakes detected, confirming before proceeding"
                strategy = ResponseStrategy.ESCALATE if stakes == StakesLevel.HIGH else ResponseStrategy.CLARIFY
            else:  # Low confidence (not currently used since we removed low confidence trigger)
                question = self._generate_clarifying_question_for_low_confidence(
                    user_input, context
                )
                reasoning = f"Low confidence ({confidence:.2f}) in understanding request"
                strategy = ResponseStrategy.CLARIFY

            return Decision(
                intent=intent,
                stakes_level=stakes,
                clarify_needed=True,
                clarify_question=question,
                response_strategy=strategy,
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

    def _detect_vague_referents(self, user_input: str, context: dict) -> bool:
        """
        Detect vague referents like "that", "it", "the thing".

        Algorithm:
        1. Check if input contains vague referent words
        2. Look for clear noun nearby (within context_window)
        3. If no clear noun, return True (vague)

        Examples:
            "Fix that thing" → True (vague)
            "Fix that authentication bug" → False (clear: "authentication bug")
            "Delete it" → True (vague)
            "Delete the test file" → False (clear: "test file")

        Args:
            user_input: The user's message
            context: Context dictionary (may contain recent messages)

        Returns:
            True if vague referent detected without clear antecedent
        """
        input_lower = user_input.lower()
        words = input_lower.split()

        # Check each word to see if it's a vague referent
        for i, word in enumerate(words):
            # Remove punctuation for matching
            clean_word = word.strip('.,!?;:')

            if clean_word in self.vague_referents:
                # Found a vague referent - now check for clear noun nearby
                # Look at words around this vague referent (2 before, 2 after)
                window_start = max(0, i - 2)
                window_end = min(len(words), i + 3)
                window = words[window_start:window_end]

                # Check if there's a specific noun (longer than 3 chars, not vague)
                # Exclude:
                # - Vague referents
                # - Vague nouns (thing, stuff)
                # - Action verbs (fix, delete, etc.)
                # - Common articles
                # - The vague word itself
                has_clear_noun = any(
                    len(w.strip('.,!?;:')) > 3 and
                    w.strip('.,!?;:') not in self.vague_referents and
                    w.strip('.,!?;:') not in self.vague_nouns and
                    w.strip('.,!?;:') not in self.action_verbs and
                    w.strip('.,!?;:') not in ['the', 'a', 'an', 'with', 'from', 'into']
                    for w in window if w.strip('.,!?;:') != clean_word
                )

                if not has_clear_noun:
                    return True  # Vague referent without clear noun nearby

        return False  # No vague referents found or all have clear context

    def _generate_clarifying_question_for_vague_referent(
        self,
        user_input: str,
        context: dict
    ) -> str:
        """
        Generate a clarifying question for vague referent.

        This returns a RAW question. The personality layer (Phase 2) will
        format it in Penny's voice.

        Args:
            user_input: The user's message
            context: Context dictionary

        Returns:
            Raw clarifying question (will be styled later)

        Example:
            "Fix that thing" → "which_thing: auth_bug OR tts_latency"
        """
        # For Phase 1A: Simple generic question
        # In Phase 2, this will be formatted as:
        # "Quick check—you mean the auth bug or the TTS latency?"

        # Try to extract action verb
        action = self._extract_action_verb(user_input)

        # Return structured question data
        return f"clarify_referent: action={action}"

    def _extract_intent(self, user_input: str) -> str:
        """
        Extract user's likely intent from input.

        Simple keyword-based extraction for Phase 1A.

        Args:
            user_input: The user's message

        Returns:
            Intent string (e.g., "fix_bug", "create_file", "explain_concept")
        """
        input_lower = user_input.lower()

        # Simple intent keywords
        if any(word in input_lower for word in ['fix', 'debug', 'repair']):
            return 'fix_issue'
        elif any(word in input_lower for word in ['create', 'make', 'build']):
            return 'create_something'
        elif any(word in input_lower for word in ['delete', 'remove', 'erase']):
            return 'delete_something'
        elif any(word in input_lower for word in ['explain', 'what', 'how', 'why']):
            return 'get_explanation'
        else:
            return 'general_request'

    def _extract_action_verb(self, user_input: str) -> str:
        """
        Extract the main action verb from input.

        Args:
            user_input: The user's message

        Returns:
            Action verb (e.g., "fix", "delete", "create")
        """
        input_lower = user_input.lower()

        # Common action verbs
        action_verbs = ['fix', 'delete', 'create', 'update', 'build',
                       'remove', 'add', 'change', 'modify', 'debug']

        for verb in action_verbs:
            if verb in input_lower:
                return verb

        return 'do'  # Default

    def _assess_stakes(self, user_input: str, context: dict) -> StakesLevel:
        """
        Assess the stakes/risk level of the user's request.

        Phase 1B Algorithm:
        1. Check for HIGH stakes keywords (medical, legal, financial destructive)
        2. If multiple HIGH stakes categories found → HIGH
        3. If 1 HIGH stakes category found → MEDIUM
        4. Otherwise → LOW

        Args:
            user_input: The user's message
            context: Context dictionary (unused in Phase 1B)

        Returns:
            StakesLevel (LOW, MEDIUM, HIGH)

        Examples:
            "Delete all production data" → MEDIUM (destructive)
            "Buy stocks and delete my account" → HIGH (financial + destructive)
            "Fix the bug" → LOW (no high-stakes keywords)
        """
        input_lower = user_input.lower()

        # Count how many HIGH stakes categories are triggered
        categories_triggered = []

        for category, keywords in self.high_stakes_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                categories_triggered.append(category)

        # Assess stakes level based on number of categories
        if len(categories_triggered) >= 2:
            return StakesLevel.HIGH  # Multiple high-stakes categories
        elif len(categories_triggered) == 1:
            return StakesLevel.MEDIUM  # Single high-stakes category
        else:
            return StakesLevel.LOW  # No high-stakes keywords

    def _detect_missing_params(self, user_input: str, context: dict) -> bool:
        """
        Detect if an action requires parameters that weren't provided.

        Phase 1B Algorithm:
        1. Check if input contains an action that requires parameters
        2. For each required parameter, check if it's present in the input
        3. If ANY required parameter is missing → True

        Args:
            user_input: The user's message
            context: Context dictionary (unused in Phase 1B)

        Returns:
            True if action requires missing parameters, False otherwise

        Examples:
            "Schedule a meeting" → True (missing date, time, attendees)
            "Schedule a meeting tomorrow at 3pm with John" → False (all params present)
            "Send an email" → True (missing recipient, subject)
            "Fix the bug" → False (fix doesn't require specific params)
        """
        input_lower = user_input.lower()

        # Check each action that requires parameters
        for action, required_params in self.actions_requiring_params.items():
            if action in input_lower:
                # This action requires parameters - check if they're present
                for param in required_params:
                    # Simple heuristic: check for param-related keywords
                    param_indicators = self._get_param_indicators(param)

                    # If none of the indicators are present, param is missing
                    if not any(indicator in input_lower for indicator in param_indicators):
                        return True  # Missing at least one parameter

        return False  # No missing parameters detected

    def _get_param_indicators(self, param: str) -> list:
        """
        Get indicator keywords that suggest a parameter is present.

        Args:
            param: Parameter name (e.g., 'date', 'time', 'recipient')

        Returns:
            List of indicator keywords

        Examples:
            'date' → ['tomorrow', 'today', 'monday', 'january', '2025', 'on']
            'time' → ['at', '3pm', 'noon', 'morning', 'evening', ':']
            'recipient' → ['to', '@', 'john', 'with']
        """
        indicators = {
            'date': ['tomorrow', 'today', 'monday', 'tuesday', 'wednesday',
                    'thursday', 'friday', 'saturday', 'sunday', 'january',
                    'february', 'march', 'april', 'may', 'june', 'july',
                    'august', 'september', 'october', 'november', 'december',
                    '2025', '2026', 'on ', 'next week', 'next month'],
            'time': ['at ', ':', 'am', 'pm', 'noon', 'morning', 'afternoon',
                    'evening', 'night', 'o\'clock'],
            'attendees': ['with ', 'and ', '@', 'john', 'jane', 'team'],
            'recipient': ['to ', '@', 'john', 'jane', 'customer', 'client'],
            'content': ['about ', 'regarding ', 'message:', 'body:', 'text:'],
            'subject': ['subject:', 're:', 'about ', 'regarding '],
            'environment': ['prod', 'dev', 'staging', 'production', 'development', 'test'],
            'version': ['v1', 'v2', 'version ', '1.0', '2.0', 'latest'],
            'name': ['called ', 'named ', 'name:', 'label:'],
            'type': ['type:', 'kind:', 'as a ', 'as an '],
            'source': ['from ', 'source:', 'origin:'],
            'destination': ['to ', 'dest:', 'target:', 'into ']
        }

        return indicators.get(param, [])

    def _generate_clarifying_question_for_missing_param(
        self,
        user_input: str,
        context: dict
    ) -> str:
        """
        Generate clarifying question for missing parameter.

        This returns a RAW question. The personality layer (Phase 2) will
        format it in Penny's voice.

        Args:
            user_input: The user's message
            context: Context dictionary

        Returns:
            Raw clarifying question (will be styled later)

        Example:
            "Schedule a meeting" → "missing_params: date, time, attendees"
        """
        input_lower = user_input.lower()

        # Find which action and which params are missing
        for action, required_params in self.actions_requiring_params.items():
            if action in input_lower:
                missing = []
                for param in required_params:
                    param_indicators = self._get_param_indicators(param)
                    if not any(indicator in input_lower for indicator in param_indicators):
                        missing.append(param)

                if missing:
                    return f"missing_params: action={action}, params={', '.join(missing)}"

        return "missing_params: unspecified"

    def _generate_clarifying_question_for_high_stakes(
        self,
        user_input: str,
        context: dict
    ) -> str:
        """
        Generate clarifying question for high-stakes action.

        This returns a RAW question. The personality layer (Phase 2) will
        format it in Penny's voice.

        Args:
            user_input: The user's message
            context: Context dictionary

        Returns:
            Raw clarifying question (will be styled later)

        Example:
            "Delete all production data" → "confirm_high_stakes: category=destructive"
        """
        input_lower = user_input.lower()

        # Find which high-stakes categories are triggered
        categories_triggered = []
        for category, keywords in self.high_stakes_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                categories_triggered.append(category)

        if categories_triggered:
            return f"confirm_high_stakes: categories={', '.join(categories_triggered)}"

        return "confirm_high_stakes: unspecified"

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
