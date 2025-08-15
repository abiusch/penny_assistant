"""Input feeder for testing Penny Assistant pipeline."""

import time
from typing import List, Iterator

class InputFeeder:
    """Feeds test inputs to the pipeline for testing."""
    
    def __init__(self, test_inputs: List[str]):
        self.test_inputs = test_inputs
        self.current_index = 0
    
    def get_next_input(self) -> str:
        """Get the next test input."""
        if self.current_index >= len(self.test_inputs):
            return None
        
        input_text = self.test_inputs[self.current_index]
        self.current_index += 1
        return input_text
    
    def reset(self):
        """Reset to the beginning of test inputs."""
        self.current_index = 0
    
    def feed_inputs(self, delay: float = 1.0) -> Iterator[str]:
        """Generator that yields inputs with delay."""
        for input_text in self.test_inputs:
            yield input_text
            time.sleep(delay)
    
    def has_more_inputs(self) -> bool:
        """Check if there are more inputs to feed."""
        return self.current_index < len(self.test_inputs)

# Example test inputs
DEFAULT_TEST_INPUTS = [
    "Hello Penny, what's the weather like?",
    "Tell me a joke",
    "What time is it?", 
    "Help me with math: what's 25 times 4?",
    "Thank you Penny"
]

def create_test_feeder(inputs: List[str] = None) -> InputFeeder:
    """Create a test input feeder."""
    return InputFeeder(inputs or DEFAULT_TEST_INPUTS)
