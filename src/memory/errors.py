"""Storage failures exposed without private filesystem or record details."""


class MemoryStorageError(RuntimeError):
    """The persistent memory store cannot be safely used or saved."""


MEMORY_SAVE_WARNING = "I couldn't confirm this conversation was saved. Please check the memory storage before continuing."
MEMORY_UNAVAILABLE_REPLY = "I can't access conversation memory right now. Please check the memory storage before continuing."
