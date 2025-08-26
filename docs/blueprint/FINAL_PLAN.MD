PennyGPT — Final Plan (Local, Voice-Interactive AI Assistant)

Vision

PennyGPT is a privacy-first, local-first voice assistant that listens, understands, executes tasks, and replies naturally. It’s modular, extensible, and keeps the user in control.

⸻

Architecture Overview

Layers
	1.	Core Engine — intent routing, session & memory, orchestration
	2.	LLM Engine — adapters for local/cloud models, prompt & persona handling
	3.	Audio Stack — STT (Whisper), VAD, TTS (gTTS initially), I/O plumbing
	4.	Plugin System — skills & integrations (weather, calendar, shell, etc.)
	5.	UI — CLI now; desktop/web later
	6.	Data Layer — local config, logs, short-term memory; privacy controls

Data Flow
	•	Voice: Mic → VAD → STT → Intent Router → (LLM/Plugin) → TTS → Speaker
	•	Text: CLI text → Intent Router → (LLM/Plugin) → Text/TTS

⸻

Repository Layout (authoritative)
penny_assistant/
├── penny.py                        # Main app (CLI + orchestration)
├── penny_simple_fixed.py           # Simple loop runner (voice demo)
├── penny_config.json               # Runtime config (devices, thresholds, etc.)
├── src/
│   ├── core/
│   │   ├── pipeline.py             # Main execution flow
│   │   ├── llm_router.py           # Select local/cloud LLM
│   │   ├── intent_router.py        # Intent classification
│   │   ├── personality.py          # Tone/style application
│   │   └── audio_pipeline.py       # STT→LLM→TTS glue (if split from pipeline)
│   ├── adapters/
│   │   ├── llm/
│   │   │   ├── local_ollama_adapter.py
│   │   │   └── factory.py
│   │   ├── stt/
│   │   │   └── whisper_adapter.py
│   │   ├── tts/
│   │   │   └── google_tts_adapter.py
│   │   └── vad/
│   │       └── webrtc_vad_adapter.py
│   └── plugins/                    # (future) built-in skills
├── tests/                          # Pytest suite (all tests pass)
├── scripts/
│   └── check-nested-repos.sh
├── requirements.in / requirements.txt
├── pytest.ini
└── .pre-commit-config.yaml

mports: run with PYTHONPATH=src so modules resolve to src/....

⸻

Major Components (paths & responsibilities)
	•	src/core/pipeline.py
Orchestrates a single interaction (voice or text). Calls STT → intent → LLM/plugin → TTS.
	•	src/core/intent_router.py
Lightweight rules to classify queries (conversation, tasking, weather, etc.).
	•	src/core/llm_router.py
Chooses which LLM adapter to use. Default: local Ollama (llama3).
	•	src/core/personality.py
Applies persona/tone. Loads penny_config.json.
	•	src/adapters/stt/whisper_adapter.py
Transcription via Whisper; temp-file cleanup included.
	•	src/adapters/tts/google_tts_adapter.py
gTTS synthesis; uses subprocess.run (no os.system).
	•	src/adapters/llm/local_ollama_adapter.py
Calls Ollama (llama3) via subprocess; fast local inference.
	•	src/adapters/vad/webrtc_vad_adapter.py
Voice activity detection, byte-safe signatures.
	•	penny.py / penny_simple_fixed.py
Entrypoints. penny_simple_fixed.py is the simplest voice loop.

⸻

Current Status
	•	✅ Wake word (“Hey Penny”) and live voice loop verified
	•	✅ Whisper STT working against MacBook mic (device configured)
	•	✅ Local LLM via Ollama/llama3 (1–2s round-trip typical)
	•	✅ gTTS integrated for audible replies
	•	✅ Conversation memory (short context window)
	•	✅ All tests passing; CI enforces pytest + pre-commit; nested-repo guard in place

⸻

Runbook
# 1) Activate environment
source .venv/bin/activate

# 2) Install deps
pip install -r requirements.txt

# 3) Run tests
PYTHONPATH=src pytest -q tests --ignore=whisper --tb=short

# 4) Start voice assistant (simple loop)
PYTHONPATH=src python penny_simple_fixed.py

# Debug audio and devices
PYTHONPATH=src python -c "import sounddevice as sd; print(sd.query_devices())"
Note: Python 3.11 recommended for audio libs. 3.13 works with warnings.

⸻

Configuration
	•	penny_config.json (repo root)
	•	audio.input_device (e.g., MacBook microphone index)
	•	audio.silence_threshold (e.g., 0.005)
	•	llm.default (“local”)
	•	persona (tone settings)
	•	(future) wake_word, routing_rules, plugin settings

⸻

Security & Privacy
	•	Local by default; cloud optional with explicit opt-in
	•	No shell injection (subprocess.run, validated inputs)
	•	Temp files removed; resource cleanup wrapped in try/finally
	•	API keys (if used) read from env/secure storage (never committed)

⸻

Testing & CI
	•	Pytest: tests/ (unit + smoke)
	•	Pre-commit: formatting, linting, safety checks
	•	GitHub Actions:
	•	Install deps → nested-repo check → pre-commit → pytest
	•	Nightly optional job for nested-repo scan

⸻

Roadmap

Phase 1 — Core MVP (✅ most complete)
	•	CLI loop, Whisper STT, gTTS, local LLM (Ollama)
	•	Intent router, short memory, basic persona
	•	Tests, CI, pre-commit, repo hygiene

Phase 2 — Plugins & UX
	•	Plugin loader + 2–3 example plugins (weather, calendar, shell)
	•	Configurable hotkeys / macOS accessibility fix (spacebar trigger)
	•	Desktop UI stub (minimal tray or hotkey listener)

Phase 3 — Routing & Scale
	•	LLM routing (simple first): stay on Ollama by default; add rules for heavier model (LM Studio 20B) only when needed; cloud fallback optional
	•	Persisted memory & summaries (longer context)
	•	Configurable wake-word sensitivity & device profiles

Stretch
	•	Vision input, web UI, mobile companion
	•	Plugin marketplace; remote plugin execution
	•	Local fine-tuning / federated learning experiments

⸻

Coding Guidelines
	•	Keep adapters stateless and swappable
	•	No long-running blocking calls in the UI loop
	•	Strict imports from src/... (enforce PYTHONPATH=src)
	•	Small, focused tests per module; fast by default

⸻

Troubleshooting
	•	Wrong mic/device → check sounddevice.query_devices() and update penny_config.json
	•	Silence not detected → tune silence_threshold (start at 0.005)
	•	Ollama errors → ensure ollama serve is running; ollama run llama3 "hi"
	•	macOS spacebar trigger → grant Accessibility permissions to Terminal/VS Code/App

⸻

Appendix — Key Files Map
	•	penny.py, penny_simple_fixed.py — entrypoints
	•	penny_config.json — config (root)
	•	src/core/{pipeline.py,intent_router.py,llm_router.py,personality.py,audio_pipeline.py}
	•	src/adapters/{llm,stt,tts,vad}/...
	•	tests/ — pytest suite
	•	.pre-commit-config.yaml, pytest.ini, requirements.*
	•	.github/workflows/ci.yml, scripts/check-nested-repos.sh

⸻

Status: Working end-to-end on macOS with local Whisper + Ollama + gTTS.
Next Up: TTS polish, macOS hotkey permissions, plugin starter set, and simple LLM routing when real bottlenecks appear.
