import json
import os
from typing import Any

from src.adapters.llm.local_ollama_adapter import LocalLLM
from src.adapters.llm.cloud_openai_adapter import CloudLLM

_CONFIG_CACHE: dict | None = None
_LLM_INSTANCE: Any | None = None


def _config_path() -> str:
    # 1) Optional override via env
    env_path = os.getenv("PENNY_CONFIG")
    if env_path and os.path.exists(env_path):
        return os.path.abspath(env_path)

    here = os.path.dirname(__file__)
    repo_root = os.path.abspath(os.path.join(here, "..", ".."))  # Updated for src/ layout

    candidates = [
        os.path.join(repo_root, "penny_config.json"),             # root
        os.path.join(repo_root, "config", "penny_config.json"),   # config/
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)

    raise FileNotFoundError("penny_config.json not found in repo root or config/ (and PENNY_CONFIG not set)")


def _load_config() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        with open(_config_path(), "r", encoding="utf-8") as f:
            _CONFIG_CACHE = json.load(f)
    return _CONFIG_CACHE


def load_config() -> dict:
    """Public helper to access penny_config.json contents."""
    return _load_config()


def get_llm() -> Any:
    global _LLM_INSTANCE
    if _LLM_INSTANCE is not None:
        return _LLM_INSTANCE

    cfg = _load_config()
    llm_cfg = cfg.get("llm", {})
    mode = llm_cfg.get("mode", "local_first").lower()
    local_id = llm_cfg.get("local", "ollama:llama3")
    cloud_id = llm_cfg.get("cloud", "gpt-4o")

    if mode in ("local_first", "local", "local-only"):
        _LLM_INSTANCE = LocalLLM(local_id)
    elif mode in ("cloud_first", "cloud", "cloud-only"):
        _LLM_INSTANCE = CloudLLM(cloud_id)
    else:
        _LLM_INSTANCE = LocalLLM(local_id)

    return _LLM_INSTANCE


def reset_llm() -> None:
    global _LLM_INSTANCE
    _LLM_INSTANCE = None
