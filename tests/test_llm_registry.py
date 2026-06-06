"""
Tests for the config-driven LLM registry (src/llm/registry.py).

These exercise model resolution and client construction without contacting any
live endpoint (OpenAICompatLLM only stores config in __init__).
"""

import json
import os
import tempfile

import pytest

from src.llm.registry import (
    available_models,
    create_llm,
    load_llm_config,
    resolve_model_config,
)


def _cfg():
    return {
        "llm": {
            "provider": "openai_compatible",
            "base_url": "http://localhost:1234/v1",
            "api_key": "x",
            "model": "openai/gpt-oss-20b",
            "temperature": 0.6,
            "active_model": "gpt-oss-20b",
            "models": {
                "gpt-oss-20b": {"model": "openai/gpt-oss-20b"},
                "qwen3-8b": {"model": "qwen3-8b", "temperature": 0.7},
                "llama-3.1-8b": {"model": "llama-3.1-8b-instruct"},
            },
        }
    }


class TestModelResolution:
    def test_active_model_selected_by_default(self):
        r = resolve_model_config(_cfg())
        assert r["llm"]["model"] == "openai/gpt-oss-20b"
        # registry stripped from resolved block
        assert "models" not in r["llm"]

    def test_explicit_model_name_overrides(self):
        r = resolve_model_config(_cfg(), "qwen3-8b")
        assert r["llm"]["model"] == "qwen3-8b"
        assert r["llm"]["temperature"] == 0.7  # per-model override
        # base fields preserved
        assert r["llm"]["base_url"] == "http://localhost:1234/v1"

    def test_unknown_explicit_model_raises(self):
        with pytest.raises(KeyError):
            resolve_model_config(_cfg(), "does-not-exist")

    def test_flat_config_without_registry(self):
        flat = {"llm": {"provider": "openai_compatible", "model": "flat-model"}}
        r = resolve_model_config(flat)
        assert r["llm"]["model"] == "flat-model"

    def test_available_models_lists_registry(self):
        assert set(available_models(_cfg())) == {"gpt-oss-20b", "qwen3-8b", "llama-3.1-8b"}

    def test_available_models_flat(self):
        flat = {"llm": {"model": "flat-model"}}
        assert available_models(flat) == ["flat-model"]


class TestClientConstruction:
    def test_create_llm_default_active(self):
        client = create_llm(_cfg())
        assert client.model == "openai/gpt-oss-20b"
        assert client.base_url == "http://localhost:1234/v1"

    def test_create_llm_named_model(self):
        client = create_llm(_cfg(), "qwen3-8b")
        assert client.model == "qwen3-8b"
        assert client.temperature == 0.7

    def test_create_llm_unknown_provider_raises(self):
        with pytest.raises(ValueError):
            create_llm({"llm": {"provider": "made_up_provider", "model": "x"}})


class TestConfigLoading:
    def test_load_roundtrip(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        try:
            with open(path, "w") as f:
                json.dump(_cfg(), f)
            loaded = load_llm_config(path)
            assert loaded["llm"]["active_model"] == "gpt-oss-20b"
        finally:
            os.unlink(path)

    def test_load_missing_file_returns_default(self):
        loaded = load_llm_config("/nonexistent/path/penny_config.json")
        assert loaded == {"llm": {}}

    def test_real_config_is_resolvable(self):
        """The committed penny_config.json must resolve to a concrete model."""
        cfg = load_llm_config("penny_config.json")
        r = resolve_model_config(cfg)
        assert r["llm"].get("model")  # non-empty
