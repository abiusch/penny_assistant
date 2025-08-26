"""Conversation memory management for Penny Assistant."""

class ConversationMemory:
    def __init__(self, max_exchanges=5):
        """
        Initialize conversation memory.
        
        Args:
            max_exchanges: Maximum number of exchanges to keep in memory
        """
        self.history = []
        self.max_exchanges = max_exchanges
    
    def add_exchange(self, user_input, assistant_response):
        """
        Add a conversation exchange to memory.
        
        Args:
            user_input: What the user said
            assistant_response: What the assistant responded
        """
        self.history.append({
            "user": user_input, 
            "assistant": assistant_response
        })
        
        # Keep only the most recent exchanges
        if len(self.history) > self.max_exchanges:
            self.history.pop(0)
    
    def get_context(self):
        """
        Get formatted context for LLM.
        
        Returns:
            String representation of conversation history
        """
        if not self.history:
            return ""
        
        context_lines = []
        for exchange in self.history:
            context_lines.append(f"User: {exchange['user']}")
            context_lines.append(f"Assistant: {exchange['assistant']}")
        
        return "\n".join(context_lines)
    
    def clear(self):
        """Clear conversation history."""
        self.history = []
    
    def get_last_exchange(self):
        """Get the most recent exchange."""
        if self.history:
            return self.history[-1]
        return None
