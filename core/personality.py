import json
import os
from typing import Dict

_CONFIG_CACHE: Dict | None = None


def _config_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "penny_config.json"))


def _load_config() -> Dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        with open(_config_path(), "r", encoding="utf-8") as f:
            _CONFIG_CACHE = json.load(f)
    return _CONFIG_CACHE


def apply(text: str, settings: dict | None = None) -> str:
    cfg = settings or _load_config().get("personality", {})
    sarcasm = cfg.get("sarcasm", "low")
    level = cfg.get("cursing_level", 0)

    out = text
    if sarcasm == "high":
        out = f"Oh, really? {out}"
    elif sarcasm == "medium":
        out = f"Sure... {out}"

    if isinstance(level, int) and level >= 3:
        out += " 🤬"

    return out
