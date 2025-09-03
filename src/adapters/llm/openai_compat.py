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

    def complete(self, prompt: str, tone: str = "") -> str:
        try:
            url = self._chat_url()
            headers = {"Authorization": f"Bearer {self.api_key}"}
            body: Dict[str, Any] = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [
                    {"role": "system", "content": f"You are PennyGPT. Tone: {tone}".strip()},
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
