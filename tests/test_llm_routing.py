"""Tests for LLM routing functionality."""

import pytest
from core.llm_router import load_config, get_llm, reset_llm
from adapters.llm.factory import LLMFactory


def test_load_config():
    """Test that config loads successfully."""
    config = load_config()
    assert isinstance(config, dict)
    assert "llm" in config


def test_get_llm():
    """Test LLM instance creation."""
    # Reset to ensure clean state
    reset_llm()

    llm = get_llm()
    assert llm is not None
    assert hasattr(llm, 'generate')

    # Test that subsequent calls return same instance
    llm2 = get_llm()
    assert llm is llm2


def test_llm_factory():
    """Test LLM factory creation."""
    config = load_config()
    llm = LLMFactory.from_config(config)
    assert llm is not None
    assert hasattr(llm, 'generate')


def test_llm_generate():
    """Test LLM text generation."""
    llm = get_llm()
    result = llm.generate("Hello")
    assert isinstance(result, str)
    assert len(result) > 0