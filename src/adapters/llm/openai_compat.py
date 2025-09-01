import json, os, time
import requests

class OpenAICompatLLM:
    def __init__(self, config: dict):
        self.cfg = config or {}
        llm = (self.cfg.get("llm") or {})
        self.base_url = llm.get("base_url", "http://localhost:1234/v1")
        self.api_key  = llm.get("api_key", "lm-studio")  # LM Studio ignores value but header must exist
        self.model    = llm.get("model", "openai/gpt-oss-20b")
        self.temperature = float(llm.get("temperature", 0.6))
        self.max_tokens  = int(llm.get("max_tokens", 512))

    def complete(self, prompt: str, tone: str = "") -> str:
        try:
            # Fix URL construction - base_url already includes /v1
            url = f"{self.base_url}/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            body = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "messages": [
                    {"role": "system", "content": f"You are PennyGPT. Tone: {tone}".strip()},
                    {"role": "user", "content": prompt}
                ]
            }
            r = requests.post(url, headers=headers, data=json.dumps(body), timeout=15)
            r.raise_for_status()
            data = r.json()
            return (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        except Exception as e:
            return f"[llm error] {e}\n{prompt}"
