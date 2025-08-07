# intent_router.py

def is_agent_mode_trigger(text):
    """Return True if the input text looks like a task that needs Agent Mode."""
    keywords = ["plan", "schedule", "set a reminder", "book", "make a reservation", "text", "call", "order", "find me"]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)
