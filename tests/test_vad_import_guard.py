"""Import-guard tests for the WebRTC VAD adapter (Phase 5 Week 14, slice 2).

Previously ``import webrtcvad`` sat unguarded at module top, so a missing or
broken webrtcvad crashed the whole module on import — unlike the rest of the
codebase, which degrades gracefully behind an ``*_AVAILABLE`` flag. These tests
lock the graceful-degradation contract.

Each case loads a FRESH copy of the adapter from source under a throwaway module
name, so the shared cached ``adapters.vad.webrtc_vad_adapter`` is never mutated
and other tests are unaffected. The "unavailable" cases simulate the missing
dependency via ``sys.modules[{"webrtcvad": None}]`` (which makes
``import webrtcvad`` raise ImportError) and need no real webrtcvad installed.
"""
import importlib.util
import sys
from unittest import mock

import pytest

import adapters.vad.webrtc_vad_adapter as _real_adapter

ADAPTER_PATH = _real_adapter.__file__


def _load_fresh(name: str, webrtcvad_present: bool):
    spec = importlib.util.spec_from_file_location(name, ADAPTER_PATH)
    mod = importlib.util.module_from_spec(spec)
    if webrtcvad_present:
        spec.loader.exec_module(mod)
    else:
        # None in sys.modules makes `import webrtcvad` raise ImportError.
        with mock.patch.dict(sys.modules, {"webrtcvad": None}):
            spec.loader.exec_module(mod)
    return mod


class TestWebrtcvadUnavailable:
    """The dependency is missing/broken — must degrade, never crash."""

    def test_module_imports_without_crashing(self):
        mod = _load_fresh("vad_adapter_missing_import", webrtcvad_present=False)
        assert mod.VAD_AVAILABLE is False

    def test_adapter_instantiates_and_reports_unavailable(self):
        mod = _load_fresh("vad_adapter_missing_init", webrtcvad_present=False)
        vad = mod.WebRTCVAD()          # must NOT raise
        assert vad.available is False  # reports itself unavailable
        assert vad.vad is None         # no backend object built

    def test_is_speech_does_not_crash_when_unavailable(self):
        # is_speech is a pre-existing stub (flagged separately) that doesn't use
        # self.vad; assert only that the degraded adapter doesn't crash calling it.
        mod = _load_fresh("vad_adapter_missing_isspeech", webrtcvad_present=False)
        vad = mod.WebRTCVAD()
        assert vad.is_speech(b"") is False


class TestWebrtcvadAvailable:
    """Normal path — no regression when the dependency is installed."""

    def test_available_path_builds_backend(self):
        pytest.importorskip("webrtcvad")
        mod = _load_fresh("vad_adapter_present", webrtcvad_present=True)
        assert mod.VAD_AVAILABLE is True
        vad = mod.WebRTCVAD()
        assert vad.available is True
        assert vad.vad is not None      # real webrtcvad.Vad constructed
