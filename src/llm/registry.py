"""
Config-driven LLM registry.

One seam for selecting and constructing the active language model, so adding a
model is a config change (penny_config.json) rather than code. Standardized on
OpenAI-compatible local serving (LM Studio / Ollama /v1 / vLLM / llama.cpp),
with the legacy Ollama-subprocess (Nemotron) client kept as a fallback provider.

Config shape (penny_config.json -> "llm"):

    "llm": {
        "provider": "openai_compatible",
        "base_url": "http://localhost:1234/v1",
        "api_key": "lm-studio",
        "temperature": 0.6,
        "max_tokens": 512,
        "active_model": "gpt-oss-20b",
        "models": {
            "gpt-oss-20b":  {"model": "openai/gpt-oss-20b"},
            "qwen3-8b":     {"model": "qwen3-8b", "temperature": 0.7},
            "llama-3.1-8b": {"model": "llama-3.1-8b-instruct"}
        }
    }

If "models"/"active_model" are absent, the flat "model" field is used
(backward compatible). Per-model entries override the base llm settings.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "penny_config.json"

# Providers that speak the OpenAI HTTP API (chat/completions).
_OPENAI_COMPATIBLE = {"openai_compatible", "openai-compatible", "lmstudio", "lm_studio", "vllm", "openai"}


def load_llm_config(path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load the full config dict from penny_config.json (empty dict if missing)."""
    if not os.path.exists(path):
        logger.warning(f"LLM config not found at {path}; using defaults")
        return {"llm": {}}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read {path}: {e}; using defaults")
        return {"llm": {}}


def available_models(config: Dict[str, Any]) -> List[str]:
    """Names of all models defined in the registry (for switching / benchmarking)."""
    llm = (config or {}).get("llm") or {}
    models = llm.get("models") or {}
    if models:
        return list(models.keys())
    # Flat config → single model identified by its model id
    return [llm["model"]] if llm.get("model") else []


def resolve_model_config(
    config: Dict[str, Any], model_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Return a *full* config dict whose "llm" block is resolved to a single model.

    Selection order: explicit ``model_name`` arg → ``llm.active_model`` →
    flat ``llm`` block. Per-model entries override base llm settings.
    """
    config = config or {}
    llm = dict(config.get("llm") or {})
    models = llm.get("models") or {}

    name = model_name or llm.get("active_model")
    if name and name in models:
        merged = {**llm, **(models[name] or {})}
    elif name and model_name and name not in models:
        raise KeyError(
            f"Model '{name}' not in registry. Available: {list(models.keys())}"
        )
    else:
        merged = dict(llm)

    # Keep the resolved block clean: drop the registry from the active config.
    merged.pop("models", None)
    merged["active_model"] = name or merged.get("model")

    resolved = dict(config)
    resolved["llm"] = merged
    return resolved


def create_llm(config: Optional[Dict[str, Any]] = None, model_name: Optional[str] = None):
    """
    Construct the active LLM client from config.

    Standardized on OpenAI-compatible serving; ``provider: ollama``/``nemotron``
    falls back to the legacy subprocess client.
    """
    if config is None:
        config = load_llm_config()

    resolved = resolve_model_config(config, model_name)
    llm = resolved.get("llm") or {}
    provider = str(llm.get("provider", "openai_compatible")).lower()

    if provider in _OPENAI_COMPATIBLE:
        try:
            from src.adapters.llm.openai_compat import OpenAICompatLLM
        except ImportError:
            from adapters.llm.openai_compat import OpenAICompatLLM
        client = OpenAICompatLLM(resolved)
        logger.info(f"LLM: {llm.get('model')} via {provider} @ {llm.get('base_url')}")
        return client

    if provider in ("ollama", "nemotron"):
        from src.llm.nemotron_client import create_nemotron_client
        return create_nemotron_client(
            model_name=llm.get("model", "nemotron-3-nano:latest"),
            reasoning_mode=llm.get("reasoning_mode", "auto"),
            temperature=float(llm.get("temperature", 0.7)),
        )

    raise ValueError(f"Unknown LLM provider: {provider!r}")
