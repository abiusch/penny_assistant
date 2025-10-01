import json
from typing import Any, Dict
import requests

class OpenAICompatLLM:
    def __init__(self, config: dict):
        self.cfg = config or {}
        llm = self.cfg.get("llm") or {}
        # accept with/without trailing slash and with/without /v1
        self.base_url = (llm.get("base_url", "http://localhost:1234/v1") or "").rstrip("/")
        self.api_key = llm.get("api_key", "lm-studio")  # LM Studio ignores value but header must exist
        self.model = llm.get("model", "openai/gpt-oss-20b")
        self.temperature = float(llm.get("temperature", 0.6))
        self.max_tokens = int(llm.get("max_tokens", 512))
        self.timeout = float(llm.get("timeout", 60))
        self._session = requests.Session()

    def _chat_url(self) -> str:
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def complete(self, prompt: str, tone: str = "", system_prompt: str = None) -> str:
        """
        Generate completion with optional personality-aware system prompt

        Args:
            prompt: User message or full conversation prompt
            tone: Optional tone hint (legacy)
            system_prompt: Custom system prompt (if None, uses default)
        """
        try:
            # Try to import personality prompt builder
            try:
                from personality_prompt_builder import get_personality_prompt
                has_personality = True
            except ImportError:
                has_personality = False

            url = self._chat_url()
            headers = {"Authorization": f"Bearer {self.api_key}"}

            # Build system prompt with personality if available
            if system_prompt:
                # Use provided system prompt
                final_system_prompt = system_prompt
            elif has_personality:
                # Use personality-aware prompt
                try:
                    base = "You are Penny, an AI assistant"
                    if tone:
                        base += f" with {tone} tone"
                    final_system_prompt = get_personality_prompt(base, context=None)
                    print(f"🎭 Personality-enhanced prompt applied (length: {len(final_system_prompt)} chars)")
                except Exception as e:
                    print(f"⚠️ Personality prompt failed: {e}, using fallback")
                    final_system_prompt = f"You are Penny, a sassy and helpful AI assistant. Tone: {tone}".strip()
            else:
                # Fallback to basic prompt
                final_system_prompt = f"You are Penny, a sassy and helpful AI assistant. Tone: {tone}".strip()

            body: Dict[str, Any] = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [
                    {"role": "system", "content": final_system_prompt},
                    {"role": "user", "content": prompt},
                ],
            }
            r = self._session.post(url, headers=headers, json=body, timeout=self.timeout)
            r.raise_for_status()
            data = r.json() if r.content else {}
            choices = data.get("choices") or []
            if not choices:
                return ""
            msg = choices[0].get("message")
            if isinstance(msg, dict) and "content" in msg:
                return (msg["content"] or "").strip()
            return (choices[0].get("text", "") or "").strip()
        except Exception as e:
            return f"[llm error] {e}\n{prompt}"

    def health(self) -> bool:
        try:
            models_url = f"{self.base_url}/models" if self.base_url.endswith("/v1") else f"{self.base_url}/v1/models"
            r = self._session.get(models_url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=5)
            r.raise_for_status()
            return True
        except Exception:
            return False
