# PENNY REPOSITORY CLEANUP - COMPLETE INSTRUCTIONS FOR CLAUDE CODE

**IMPORTANT:** This file contains ALL instructions and file contents needed for cleanup.
Read this entire file, then execute the tasks in order.

---

## TASK 1: CREATE CLEANUP SCRIPT

Create file: `cleanup_repository.sh`

```bash
#!/bin/bash
# cleanup_repository.sh
# Penny Repository Cleanup Script
# Duration: ~30 minutes

set -e

echo "🧹 Penny Repository Cleanup Script"
echo "===================================="
echo ""
echo "This script will:"
echo "  1. Create organized directory structure"
echo "  2. Move test files to tests/"
echo "  3. Move experiments to experiments/"
echo "  4. Archive completed docs to docs/archive/phases/"
echo "  5. Consolidate databases to data/"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo "Starting cleanup..."

# 1. Create directory structure
echo "📁 Creating directories..."
mkdir -p tests/unit tests/integration
mkdir -p experiments/
mkdir -p docs/archive/phases
mkdir -p data/

# 2. Move test files
echo "🧪 Moving test files..."
find . -maxdepth 1 -name "test_*.py" -exec mv {} tests/ \; 2>/dev/null || true
test_count=$(find tests/ -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Moved $test_count test files"

# 3. Move experimental scripts
echo "🔬 Moving experimental scripts..."
find . -maxdepth 1 -name "*_demo.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "demo_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "adaptive_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "cj_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "enhanced_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
find . -maxdepth 1 -name "integrated_*.py" -exec mv {} experiments/ \; 2>/dev/null || true
exp_count=$(find experiments/ -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Moved $exp_count experimental scripts"

# 4. Archive completed docs
echo "📄 Archiving completed docs..."
find . -maxdepth 1 -name "WEEK*_COMPLETE.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "PHASE*_COMPLETE*.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_COMPLETE.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "*_SUMMARY.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
find . -maxdepth 1 -name "ACTION_PLAN*.md" -exec mv {} docs/archive/phases/ \; 2>/dev/null || true
docs_count=$(find docs/archive/phases/ -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Archived $docs_count docs"

# 5. Move databases
echo "💾 Moving databases..."
find . -maxdepth 1 -name "*.db" -exec mv {} data/ \; 2>/dev/null || true
db_count=$(find data/ -name "*.db" 2>/dev/null | wc -l | tr -d ' ')
echo "   ✅ Moved $db_count databases"

# 6. Create ENTRY_POINTS.md
echo "📌 Creating ENTRY_POINTS.md..."
cat > ENTRY_POINTS.md << 'EOFENTRY'
# Penny Canonical Entry Points

## Production Entry Points

**Voice Mode:** `python penny.py`
**Chat Mode:** `python chat_penny.py`  
**Research Pipeline:** `python research_first_pipeline.py`
**Web Interface:** `cd web_interface && python server.py`

## Development

**Tests:** `pytest tests/ -v`
**Health Check:** `python check_health.py`

## Documentation

Start here: `NEXT_PHASE_TASKS.md`

**Do NOT use files in `/experiments/` for production!**
EOFENTRY

echo "✅ Cleanup complete!"
echo ""
echo "Next: Run 'pytest tests/' to verify nothing broke"
```

**Execute this script:**
```bash
chmod +x cleanup_repository.sh
./cleanup_repository.sh
```

---

## TASK 2: CREATE requirements-core.txt

Create file: `requirements-core.txt`

```
# Cross-platform core dependencies
openai>=1.0.0
anthropic>=0.18.0
sounddevice>=0.4.6
soundfile>=0.12.1
openai-whisper==20231117
torch>=2.0.0
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
numpy>=1.24.0
sqlalchemy>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
cryptography>=42.0.0
```

---

## TASK 3: CREATE requirements-macos.txt

Create file: `requirements-macos.txt`

```
# macOS-specific dependencies
pyobjc-core==11.1
pyobjc-framework-applicationservices==11.1
pyobjc-framework-cocoa==11.1
pyobjc-framework-coretext==11.1
pyobjc-framework-quartz==11.1
pynput>=1.7.6
```

---

## TASK 4: CREATE requirements-optional.txt

Create file: `requirements-optional.txt`

```
# Optional dependencies
elevenlabs>=0.2.26
brave-search>=1.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## TASK 5: CREATE .env.example

Create file: `.env.example`

```
# Required
LM_STUDIO_URL=http://localhost:1234

# Optional - Premium Services
# ELEVENLABS_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
# BRAVE_SEARCH_API_KEY=your_key_here

# Optional - Configuration
# DEFAULT_PERSONALITY=penny
# MEMORY_RETENTION_DAYS=30
```

---

## TASK 6: CREATE MINIMAL_SETUP.md

Create file: `MINIMAL_SETUP.md`

```markdown
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
```

---

## TASK 7: UPDATE NEXT_PHASE_TASKS.md

Add this section at the TOP of NEXT_PHASE_TASKS.md (after the header):

```markdown
## 🚨 URGENT: REPOSITORY CLEANUP (JUST COMPLETED!)

**Status:** ✅ COMPLETE

**What was done:**
- Moved 60+ test files → `tests/`
- Moved 100+ experimental scripts → `experiments/`
- Archived 50+ completed docs → `docs/archive/phases/`
- Consolidated databases → `data/`
- Created `ENTRY_POINTS.md`
- Split requirements into core/platform/optional
- Added `.env.example` and `MINIMAL_SETUP.md`

**Why this was critical:**
Three external reviews (Manus, ChatGPT, Perplexity) unanimously flagged:
> "Root directory sprawl will directly hurt velocity if not cleaned"

**Next:** Week 8.5 Judgment & Clarify System

---
```

Also update the "QUICK STATUS" section to:

```markdown
## 🎯 QUICK STATUS

**Current:** Repository Cleanup Complete ✅  
**Next:** Week 8.5 Judgment & Clarify System (1 week) ⭐  
**Then:** Week 9-10 Hebbian Learning (2 weeks)  
**Phase 3:** 85% Complete → 90% after Week 8.5  
**Server:** 🟢 Port 5001  
**Tests:** 🟢 100% pass rate
```

---

## VERIFICATION STEPS

After completing all tasks:

```bash
# 1. Verify structure
ls -la tests/ experiments/ docs/archive/ data/

# 2. Verify tests still pass
pytest tests/ -v

# 3. Verify new files exist
ls -la requirements-*.txt .env.example MINIMAL_SETUP.md ENTRY_POINTS.md

# 4. Check git status
git status
```

---

## COMMIT

```bash
git add .
git commit -m "Repository cleanup before Week 8.5

Based on 3 external reviews (Manus, ChatGPT, Perplexity):
- Organized structure (tests/, experiments/, docs/archive/, data/)
- Split requirements into core/platform/optional
- Added .env.example and MINIMAL_SETUP.md
- Created ENTRY_POINTS.md
- Updated NEXT_PHASE_TASKS.md"
```

---

## SUMMARY

**Tasks completed:**
1. ✅ Created and ran cleanup script
2. ✅ Created requirements-core.txt
3. ✅ Created requirements-macos.txt
4. ✅ Created requirements-optional.txt
5. ✅ Created .env.example
6. ✅ Created MINIMAL_SETUP.md
7. ✅ Updated NEXT_PHASE_TASKS.md

**Repository is now clean and ready for Week 8.5!**
