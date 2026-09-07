"""Shared failure contract for model adapters and conversation entry points."""

MODEL_FAILURE_REPLY = "I couldn't generate a response right now. Please try again."


class ModelGenerationError(RuntimeError):
    """Generation failed; this must not be treated as an assistant answer."""

    def __init__(self):
        # Never carry provider exception text, response bodies, or prompts into
        # the user-facing exception. Providers may include request data in errors.
        super().__init__('Language model generation failed')


def require_response_text(value):
    """Reject unusable completions before conversation persistence."""
    if not isinstance(value, str) or not value.strip():
        raise ModelGenerationError()
    return value.strip()
