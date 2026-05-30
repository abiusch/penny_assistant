PYTHONPATH := src
VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv setup precommit test test-all smoke run plugin-test scan-repos

venv:
	@test -d $(VENV) || python3 -m venv $(VENV)

setup: venv
	$(PY) -m pip install --upgrade pip
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
	$(PIP) install pytest pre-commit aiohttp

precommit:
	pre-commit run --all-files --show-diff-on-failure

# Canonical suite: curated Weeks 8.5-13 feature tests (~408, 100% green, ~2s).
# File list is in pytest.ini (testpaths). PYTHONPATH=src is also set by conftest.py.
test:
	PYTHONPATH=$(PYTHONPATH) pytest --tb=short

# Everything, including legacy/live/audio/LLM tests (many fail offline). See QUARANTINE_NOTES.md.
test-all:
	PYTHONPATH=$(PYTHONPATH) pytest tests --ignore=whisper --run-slow --tb=short

# Test plugin system integration
plugin-test:
	PYTHONPATH=$(PYTHONPATH) $(PY) test_weather_plugin.py

# Test enhanced voice pipeline  
smoke:
	PYTHONPATH=$(PYTHONPATH) $(PY) penny_with_plugins.py --test

# Legacy smoke test
smoke-legacy:
	PYTHONPATH=$(PYTHONPATH) $(PY) -c "from core.pipeline import run_once; print(run_once())"

# Run enhanced voice assistant with plugins
run:
	PYTHONPATH=$(PYTHONPATH) $(PY) penny_with_plugins.py

# Run simple fallback version
run-simple:
	PYTHONPATH=$(PYTHONPATH) $(PY) penny_simple_fixed.py

# Avoid legit submodule internals and venv
scan-repos:
	find . -type d -name .git -not -path "./.git" -not -path "./.git/modules/*" -not -path "./$(VENV)/*" -print
