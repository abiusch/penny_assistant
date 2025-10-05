# ⚠️ IMPORTANT: Python Command Fix

## Issue
All documentation says `python` but macOS requires `python3`

## Quick Fix - Use These Commands Instead:

### All Commands Should Use `python3`:

```bash
# Demo
python3 personality_observer.py

# Check learning
python3 check_personality_learning.py

# Inspect profile
python3 inspect_phase1_profile.py

# Run tests
python3 test_personality_evolution_phase1.py
python3 test_phase1_integration.py
```

## OR: Activate Virtual Environment First

If you activate your venv, then `python` will work:

```bash
source .venv/bin/activate
# Now 'python' works and points to python3
python personality_observer.py
```

## For All Documentation:

Wherever you see `python` in the docs, use `python3` instead (or activate venv first).

---

**Apologies for the inconsistency! All the code itself is Python 3, just the command examples were wrong.**
