class CloudLLM:
    def __init__(self, model_id: str):
        self.model_id = model_id
    def generate(self, prompt: str) -> str:
        return f"[cloud:{self.model_id}] {prompt}"
