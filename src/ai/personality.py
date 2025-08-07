from pathlib import Path
import re

PROMPT_PATHS = [
    Path("penny_prompt (1).txt"),
    Path("penny_prompt.txt"),
    Path("config/penny_prompt.txt"),
]

DEFAULT_MODE = "Penny"
VALID_MODES = {"Penny", "Justine", "Coach", "Erin"}

class Personality:
    def __init__(self):
        self.mode = DEFAULT_MODE
        self.system_prompt = self._load_prompt_text()

    def _load_prompt_text(self) -> str:
        for p in PROMPT_PATHS:
            if p.exists():
                return p.read_text(encoding="utf-8")
        # Minimal fallback if file not present
        return "You are PennyGPT. Be helpful, witty, and a little sassy. [PENNY_PHASE_1_OK]"

    def _maybe_switch_mode(self, text: str) -> None:
        lower = text.lower()
        if "act like justine" in lower or "be justine" in lower:
            self.mode = "Justine"
        elif "act like coach" in lower or "be coach" in lower:
            self.mode = "Coach"
        elif "act like erin" in lower or "be erin" in lower:
            self.mode = "Erin"
        elif "act like penny" in lower or "be penny" in lower:
            self.mode = "Penny"

    def get_prompt(self, user_input: str) -> str:
        self._maybe_switch_mode(user_input)
        header = f"[MODE: {self.mode}]\n"
        return f"{self.system_prompt}\n\n{header}\nUser: {user_input.strip()}"
