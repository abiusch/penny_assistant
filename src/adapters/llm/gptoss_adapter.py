try:
    import gpt_oss
except Exception:
    gpt_oss = None

class GPTOSS:
    def __init__(self, config):
        self.config = config or {}
        self.model = (self.config.get("llm") or {}).get("model", "gpt-oss-20b")

    def complete(self, prompt: str, tone: str = "") -> str:
        if not gpt_oss:
            return f"[gpt-oss missing] {prompt}"
        try:
            # basic call, you can expand with params (max_tokens, temperature)
            result = gpt_oss.generate(self.model, prompt)
            if isinstance(result, dict):
                return result.get("text", prompt)
            return str(result)
        except Exception as e:
            return f"[gpt-oss error: {e}] {prompt}"
