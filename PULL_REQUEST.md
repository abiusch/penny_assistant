# Pull Request: LM Studio LLM, TTS reliability, wake-word gating, docs & tests

## Summary

This PR finishes the "make it solid" pass on PennyGPT's voice loop and local LLM setup.

* **LLM (LM Studio)**: fixed OpenAI-compat URL bug (/v1/v1 → /v1) and set a sane **15s** timeout. Factory now recognizes "openai_compatible" (also "openai-compatible", "lmstudio").
* **TTS reliability**: short-phrase **cache**, **background playbook** thread, **single-error logging**, graceful no-crash degrade.
* **STT / pipeline**: wake-word gating, empty-text short-circuit, cleaner state transitions.
* **Calendar**: verified fallback path (friendly timeout behavior).
* **Docs**: full **LM Studio setup guide** + refreshed README.
* **Tests**: 4 new suites; integration tests **skip** when services aren't available.

## What changed

* `src/adapters/llm/openai_compat.py` – OpenAI-compatible client for LM Studio.
* `src/adapters/llm/factory.py` – provider detection for openai_compatible / lmstudio.
* `src/core/pipeline.py` – wake-word gate, empty-text guard, TTS speak via background thread; no crashes on TTS errors.
* `src/adapters/tts/google_tts_adapter.py` – caching + error handling (no shape changes).
* `docs/SETUP_LM_STUDIO.md` – end-to-end setup with screenshots/commands.
* `README.md` – quick start updated.
* `tests/...` – 4 new suites covering LLM adapter, TTS cache, pipeline transitions, service-skip integration.
* `requirements.in/.txt` – ensure requests is pinned.

## Performance & reliability

* Faster perceived TTS via cache + async playback.
* LLM calls fail fast with clearer errors; no hanging on bad base URLs.
* Pipeline keeps barge-in behavior and returns to IDLE cleanly.

## Risks & mitigations

* **Background TTS**: ensured single-error logging & safe shutdown path; added tests.
* **LM Studio down**: adapter timeouts reduced; tests skip; user-facing error is friendly.

## Testing

### Quick Verification
```bash
# Verify LM Studio is accessible
curl -X GET http://localhost:1234/v1/models

# Test chat completion  
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer lm-studio" \
  -d '{
    "model": "openai/gpt-oss-20b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'

# Run new test suites
python -m pytest tests/test_openai_compat_llm.py -v
python -m pytest tests/test_tts_pipeline.py -v  
python -m pytest tests/test_wake_word.py -v
python -m pytest tests/test_calendar_fallback.py -v
```

### Integration Test
```bash
# Test basic LLM integration (requires LM Studio running)
python -c "from src.adapters.llm.openai_compat import OpenAICompatLLM; import json; config = json.load(open('penny_config.json')); llm = OpenAICompatLLM(config); print(llm.complete('Hello, how are you?'))"
```

## Checklist

- [x] Tests pass locally (pytest)
- [x] Pre-commit clean
- [x] Requests pinned  
- [x] Config documented
- [x] No nested repos under project root
- [x] URL construction bug fixed and tested
- [x] Timeout reduced to 15s with verification
- [x] TTS caching implemented with tests
- [x] Wake word detection integrated
- [x] Documentation comprehensive and accurate
- [x] Error handling prevents crashes
- [x] Integration tests skip gracefully when services unavailable

## Configuration

Ensure your `penny_config.json` has:

```json
{
  "llm": {
    "provider": "openai_compatible",
    "base_url": "http://localhost:1234/v1",
    "api_key": "lm-studio", 
    "model": "openai/gpt-oss-20b",
    "temperature": 0.6,
    "max_tokens": 512
  }
}
```

**Note**: Update `model` field to match your exact LM Studio model name.

---

## Release notes — v0.2.0

### Highlights

* **Local LLM via LM Studio**: OpenAI-compatible adapter; fixed base URL; 15s timeout.
* **Snappier TTS**: caching + background playbook; robust error handling (no crashes).
* **Smarter STT pipeline**: wake-word gating, empty-text early return.
* **Docs & DX**: comprehensive LM Studio setup guide; updated README.
* **Quality**: broader test coverage with graceful skips when services missing.

### How to use

1. Start LM Studio local server (OpenAI-compatible API) with openai/gpt-oss-20b.
2. Ensure penny_config.json matches the config above.
3. Run tests: `PYTHONPATH=src pytest -q tests --tb=short`.
4. Quick smoke with cURL (models + chat) as shown.

### Known notes

* If LM Studio isn't running, LLM calls time out fast with a friendly message; tests skip.
* macOS Calendar heavy queries can still be slow; fallback path remains friendly.

### Next

* Add `llm.healthcheck()` (1s GET /models) before first request.
* Log basic TTS metrics (cache_hit, synth_ms, play_ms).
* Unit test: barge-in interrupts playbook promptly.
* (Optional) Calendar "tiny window" single-calendar query with 1.5s hard timeout.

## Files Changed

### Core Implementation
- `src/adapters/llm/openai_compat.py` - Fixed URL bug, added timeout
- `src/adapters/llm/factory.py` - Added provider detection  
- `src/core/pipeline.py` - Wake word integration, empty text handling
- `src/adapters/tts/google_tts_adapter.py` - Caching and background playbook

### Testing
- `tests/test_openai_compat_llm.py` - LLM adapter tests with integration
- `tests/test_tts_pipeline.py` - TTS reliability and caching tests
- `tests/test_wake_word.py` - Wake word detection accuracy tests
- `tests/test_calendar_fallback.py` - Calendar plugin robustness tests

### Documentation
- `docs/SETUP_LM_STUDIO.md` - Comprehensive setup guide
- `README.md` - Updated with quick start and architecture
- `IMPROVEMENTS_SUMMARY.md` - Detailed changelog

### Dependencies
- `requirements.in` - Pinned requests dependency
- `requirements.txt` - Updated with pinned versions

## Breaking Changes

None. All changes are backwards compatible with existing configurations.

## Migration Guide

No migration needed. Existing `penny_config.json` files will work with the new implementation.

---

**Ready for review and merge!** 🚀
