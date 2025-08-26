import subprocess
import json

class LocalLLM:
    def __init__(self, model_id: str):
        self.model_id = model_id
        # Extract model name from format like "ollama:llama3"
        if ":" in model_id:
            _, self.model_name = model_id.split(":", 1)
        else:
            self.model_name = model_id
    
    def generate(self, prompt: str, context: str = "") -> str:
        try:
            # Add context to prompt if provided
            if context:
                full_prompt = f"Previous conversation:\n{context}\n\nUser: {prompt}\nAssistant:"
            else:
                full_prompt = prompt
            
            # Call ollama via command line
            result = subprocess.run(
                ["ollama", "run", self.model_name, full_prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[Ollama error] {prompt}"
        except subprocess.TimeoutExpired:
            return f"[Ollama timeout] {prompt}"
        except FileNotFoundError:
            return f"[Ollama not found - install from ollama.com] {prompt}"
        except Exception as e:
            return f"[Error: {e}] {prompt}"
