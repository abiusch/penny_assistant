from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLM(ABC):
    """Base interface for all LLM implementations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model_name = config.get('model_name', 'unknown')
        self.initialize()
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the LLM with its configuration."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt."""
        pass
    
    @abstractmethod
    def validate_response(self, response: str) -> bool:
        """Validate if the response is acceptable."""
        pass
