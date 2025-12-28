"""
Nemotron-3 Nano LLM Client
Local inference using Ollama with intelligent reasoning mode detection
"""

import logging
from typing import Dict, Any, Optional, List
import subprocess
import json

logger = logging.getLogger(__name__)

# Import reasoning detector
try:
    from src.llm.reasoning_detector import should_use_reasoning
    REASONING_DETECTOR_AVAILABLE = True
except ImportError:
    REASONING_DETECTOR_AVAILABLE = False
    logger.warning("Reasoning detector not available, using static mode")


class NemotronClient:
    """Client for NVIDIA Nemotron-3 Nano via Ollama"""

    def __init__(
        self,
        model_name: str = "nemotron-3-nano:latest",
        reasoning_mode: bool = "auto",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize Nemotron client.

        Args:
            model_name: Ollama model name (default: nemotron-3-nano:latest)
            reasoning_mode: Enable reasoning traces - True/False or "auto" for intelligent detection (default: "auto")
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Max tokens to generate (default: 2048)
        """
        self.model_name = model_name
        self.reasoning_mode = reasoning_mode  # Can be True, False, or "auto"
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Verify model is available
        self._verify_model()

        mode_desc = "auto (intelligent)" if reasoning_mode == "auto" else str(reasoning_mode)
        logger.info(f"NemotronClient initialized: {model_name}, reasoning={mode_desc}")

    def _verify_model(self):
        """Verify Nemotron model is available"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if self.model_name not in result.stdout and "nemotron-3-nano" not in result.stdout:
                raise RuntimeError(
                    f"Model {self.model_name} not found. "
                    f"Run: ollama pull nemotron-3-nano:latest"
                )

            logger.info(f"Model {self.model_name} is available")
        except FileNotFoundError:
            raise RuntimeError(
                "Ollama not found. Install: curl -fsSL https://ollama.com/install.sh | sh"
            )
        except Exception as e:
            logger.error(f"Failed to verify model: {e}")
            raise

    def complete(
        self,
        prompt: str,
        tone: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Complete a prompt (compatible with LLMFactory interface).

        Args:
            prompt: Text prompt to complete
            tone: Optional tone (ignored, for compatibility)
            temperature: Override default temperature

        Returns:
            Generated response text
        """
        return self.generate(prompt, temperature=temperature)

    def generate(
        self,
        prompt_or_messages,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate response using Nemotron-3 Nano.

        Args:
            prompt_or_messages: Either a string prompt or list of message dicts
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens

        Returns:
            Generated response text
        """
        # Handle both string prompts and message lists
        if isinstance(prompt_or_messages, str):
            prompt = prompt_or_messages
            user_query = prompt_or_messages  # For reasoning detection
        else:
            # Build prompt from messages
            prompt = self._build_prompt(prompt_or_messages, system_prompt)
            # Extract user query for reasoning detection
            user_query = next((msg.get("content", "") for msg in reversed(prompt_or_messages) if msg.get("role") == "user"), "")

        # Determine if we should use reasoning for this specific query
        use_reasoning = self._should_use_reasoning_for_query(user_query)

        # Use provided values or defaults
        temp = temperature if temperature is not None else self.temperature

        # Call Ollama via subprocess
        try:
            # Build command with options
            cmd = ["ollama", "run", self.model_name]

            # Run with timeout (increased for long prompts)
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=180  # 3 minute timeout for long complex prompts
            )

            if result.returncode == 0:
                response = result.stdout.strip()

                # ALWAYS strip reasoning traces for clean output
                # Nemotron outputs thinking in various formats - remove all of them
                response = self._clean_reasoning_traces(response)

                logger.debug(f"Generated {len(response)} chars (reasoning={use_reasoning})")
                return response
            else:
                error_msg = result.stderr.strip()
                logger.error(f"Ollama error: {error_msg}")
                raise RuntimeError(f"Generation failed: {error_msg}")

        except subprocess.TimeoutExpired:
            logger.error("Generation timed out (>180s)")
            raise RuntimeError("Generation timed out after 180 seconds")
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _clean_reasoning_traces(self, response: str) -> str:
        """
        Remove reasoning traces from Nemotron output.
        Nemotron can output thinking in various formats - strip them all.
        
        Args:
            response: Raw response from model
            
        Returns:
            Cleaned response with only the final answer
        """
        import re
        
        # Remove <think>...</think> tags and content
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
        
        # If response starts with "Thinking." - remove EVERYTHING until we hit the actual answer
        # Look for the pattern: "Thinking...done thinking." followed by actual response
        if response.strip().startswith('Thinking'):
            # Find "done thinking" and take everything after it
            match = re.search(r'done thinking\.\s*(.+)', response, flags=re.DOTALL)
            if match:
                response = match.group(1)
            else:
                # No "done thinking" found, try to find first sentence that looks like a real response
                # Look for first sentence after "Thinking" that starts with capital letter
                lines = response.split('\n')
                for i, line in enumerate(lines):
                    # Skip empty lines and lines that are clearly reasoning
                    if line.strip() and not any(marker in line.lower() for marker in ['thinking', 'we need', 'must', 'should']):
                        # Found potential start of real response
                        response = '\n'.join(lines[i:])
                        break
        
        # Remove other common reasoning markers at start
        reasoning_prefixes = [
            r'^Let me think.*?\n',
            r'^I need to.*?\n',
            r'^We need to.*?\n',
        ]
        
        for prefix in reasoning_prefixes:
            response = re.sub(prefix, '', response, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        response = '\n'.join(line.strip() for line in response.split('\n') if line.strip())
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        return response.strip()
    
    def _should_use_reasoning_for_query(self, query: str) -> bool:
        """
        Determine if reasoning should be used for this specific query.
        
        Args:
            query: The user's query
            
        Returns:
            True if reasoning should be enabled, False otherwise
        """
        # If reasoning mode is explicitly set (not "auto"), use that
        if self.reasoning_mode is True:
            return True
        elif self.reasoning_mode is False:
            return False
        
        # If mode is "auto", use intelligent detection
        if REASONING_DETECTOR_AVAILABLE:
            should_reason = should_use_reasoning(query)
            if should_reason:
                logger.info(f"🧠 Enabling reasoning for complex query: {query[:50]}...")
            return should_reason
        else:
            # Fall back to no reasoning if detector not available
            return False

    def _build_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Build prompt from messages"""
        prompt_parts = []

        # Add system prompt if provided
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")

        # Add messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")

        # Add final assistant prompt
        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completion interface.

        Args:
            messages: List of message dicts
            **kwargs: Additional generation parameters

        Returns:
            OpenAI-style completion dict
        """
        response_text = self.generate(messages, **kwargs)

        # Return OpenAI-compatible format
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "model": self.model_name,
            "usage": {
                "prompt_tokens": 0,  # Ollama doesn't report this
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }


# Factory function
def create_nemotron_client(
    reasoning_mode: bool = True,
    temperature: float = 0.7
) -> NemotronClient:
    """Create and return a NemotronClient instance"""
    return NemotronClient(
        model_name="nemotron-3-nano:latest",
        reasoning_mode=reasoning_mode,
        temperature=temperature
    )
