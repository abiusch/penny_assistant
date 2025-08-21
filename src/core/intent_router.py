# intent_router.py

def is_agent_mode_trigger(text):
    """Return True if the input text looks like a task that needs Agent Mode."""
    keywords = ["plan", "schedule", "set a reminder", "book", "make a reservation", "text", "call", "order", "find me"]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in keywords)

def route_intent(text):
    """Route user input to appropriate intent and extract payload.

    Returns:
        tuple: (intent, payload) where intent is a string and payload is a dict
    """
    text_lower = text.lower().strip()

    # Check for agent mode triggers
    if is_agent_mode_trigger(text):
        return "agent_task", {"text": text, "requires_planning": True}

    # Check for common intents
    if any(word in text_lower for word in ["weather", "temperature", "forecast"]):
        return "weather", {"query": text}

    if any(word in text_lower for word in ["time", "clock", "what time"]):
        return "time", {"query": text}

    if any(word in text_lower for word in ["joke", "funny", "laugh", "humor"]):
        return "entertainment", {"type": "joke", "query": text}

    if any(word in text_lower for word in ["help", "assist", "support"]):
        return "help", {"query": text}

    # Default to general conversation
    return "conversation", {"text": text}
