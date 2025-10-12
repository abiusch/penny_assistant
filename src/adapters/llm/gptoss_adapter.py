try:
    import gpt_oss
    GPTOSS_AVAILABLE = True
except Exception:
    gpt_oss = None
    GPTOSS_AVAILABLE = False

class GPTOSS:
    def __init__(self, config):
        self.config = config or {}
        llm_config = self.config.get("llm") or {}
        self.model = llm_config.get("model", "gpt-oss-20b")
        self.temperature = llm_config.get("temperature", 0.6)
        self.presence_penalty = llm_config.get("presence_penalty", 0.5)
        self.frequency_penalty = llm_config.get("frequency_penalty", 0.3)
        self.max_tokens = llm_config.get("max_tokens", 512)
        self.available = GPTOSS_AVAILABLE

        # Log availability status
        if not self.available:
            print("[LLM] WARNING: gpt-oss not available, will use fallback responses")

    def complete(self, prompt: str, tone: str = "") -> str:
        if not self.available:
            # Provide helpful fallback instead of echo
            fallback_responses = [
                "I'd be happy to help, but I need my language model to be properly configured.",
                "My AI brain isn't fully connected right now. Please check my configuration.",
                "I'm having trouble accessing my language model. Let me know if you need help setting it up.",
                "My thinking capabilities are limited right now - the LLM service isn't available."
            ]
            import random
            return random.choice(fallback_responses)
            
        try:
            # Call with temperature, penalties, and max_tokens from config
            result = gpt_oss.generate(
                self.model,
                prompt,
                temperature=self.temperature,
                presence_penalty=self.presence_penalty,
                frequency_penalty=self.frequency_penalty,
                max_tokens=self.max_tokens
            )
            if isinstance(result, dict):
                return result.get("text", prompt)
            return str(result)
        except Exception as e:
            print(f"[LLM] gpt-oss error: {e}")
            return f"I encountered an issue processing that request. Error: {str(e)[:50]}..."
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Alias for complete to match expected interface."""
        tone = kwargs.get('tone', '')
        return self.complete(prompt, tone)
    
    def is_available(self) -> bool:
        """Check if the LLM is available"""
        return self.available

    def get_status(self) -> dict:
        """Get detailed status information"""
        return {
            "provider": "gpt-oss",
            "available": self.available,
            "model": self.model,
            "fallback_active": not self.available
        }
