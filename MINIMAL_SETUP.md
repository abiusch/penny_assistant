# Minimal Setup Guide

Get Penny running with core functionality only.

## Requirements

- Python 3.11+
- 8GB RAM minimum
- macOS (primary support)

## Quick Start

### 1. Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements-core.txt
pip install -r requirements-macos.txt  # macOS only
```

### 3. Set Up LM Studio
1. Download: https://lmstudio.ai
2. Download model (nemotron-3-nano recommended)
3. Start local server on port 1234

### 4. Configure
```bash
cp .env.example .env
# Edit .env: LM_STUDIO_URL=http://localhost:1234
```

### 5. Test
```bash
python chat_penny.py
```

## What Works

✅ Text conversation
✅ Voice conversation
✅ Basic memory
✅ Personality system
✅ Local LLM

## What's Optional

❌ Premium TTS (ElevenLabs)
❌ Web search
❌ Calendar integration

## Troubleshooting

**Can't connect to LM Studio:**
- Verify running at http://localhost:1234

**Tests failing:**
```bash
pip install -r requirements-core.txt
pytest tests/ -v
```
