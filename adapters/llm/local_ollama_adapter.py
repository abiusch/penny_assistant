class LocalLLM:
    def __init__(self, model_id: str):
        self.model_id = model_id
    def generate(self, prompt: str) -> str:
        return f"[local:{self.model_id}] {prompt}"
