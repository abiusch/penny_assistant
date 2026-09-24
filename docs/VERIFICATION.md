# Penny verification guide

Use [AGENTS.md](../AGENTS.md) for authority and [current tasks](../NEXT_PHASE_TASKS.md)
for dated results. Commands below select checks; they are not claims that a new
revision passed. The [architecture map](SYSTEM_BLUEPRINT.md) connects concerns to
source files and tests.

## Routine offline checks

Run from the repository root with the project's dependencies already installed
in `.venv`. Use synthetic data and temporary storage; preserve live history and keys.

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PENNY_DISABLE_HEALTH_LOOP=1 make test
```

`make test` uses `.venv/bin/python` and the curated `testpaths` in `pytest.ini`.
The equivalent direct command is useful when `make` is unavailable:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PENNY_DISABLE_HEALTH_LOOP=1 PYTHONPATH=src .venv/bin/python -m pytest --tb=short
```

The separate pipeline characterizations use the real pipeline with fake
audio/embeddings/model responses and isolated storage:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PENNY_DISABLE_HEALTH_LOOP=1 PYTHONPATH=src .venv/bin/python -m pytest tests/test_pipeline_characterization.py tests/test_pipeline_characterization_extended.py --run-slow --tb=short
```

The `--run-slow` switch is required by their historical marker; these two files
are offline. Do not generalize that to other slow tests. To investigate one
subsystem, replace those two file arguments with the specific canonical files
listed in the architecture map, then broaden only as the change requires.

Do not use `pytest tests` or `make test-all` as the routine check. A positional
directory overrides the curated list and collects legacy/live/audio scripts.
[Quarantine notes](../QUARANTINE_NOTES.md) record historical collection problems;
individual files need inspection before reintroducing them.

## What the tests establish

[offline_pipeline_factory](../tests/conftest.py) patches expensive dependencies
before construction and selects scratch config/data. It retains real context,
vector persistence and personality components, shuts down research managers and
checks production data file sizes/mtimes (excluding SQLite WAL/SHM sidecars).
That guard is useful evidence, not a proof that every possible live resource is
isolated. New tests must explicitly isolate their own storage and external I/O.

Characterization tests stub the tool loop; the tool-roundtrip and model-error
suites cover additional real orchestration paths. Preserve behavior assertions
through refactors. For model replies, assert stable contracts such as consent,
correct tool results and failure side effects, allowing natural wording variation.
Exact assertions remain appropriate for deliberate fixed error messages.

Two strict expected failures in `test_capability_gate.py` document unfinished
enforcement: tool availability differs from its manifest, and disabling the
safety wrapper exposes raw tools. A green run with those expected failures does
not mean enforcement is complete. Offline tests do not validate live speech,
model quality, full browser behavior or simultaneous web conversations.

## GitHub and handoff evidence

[ci.yml](../.github/workflows/ci.yml) runs canonical and characterization suites on
Linux/Python 3.11 and 3.13, focused tool-safety checks on Windows/Python 3.13, and
an integration import job. The doctor step tolerates failure; its presence in a
green job does not establish a healthy live installation. Dependency watchdog and
automated review workflows are separate from this test pipeline.

At wrap-up, record the branch/commit, exact commands/results, environment limits,
changed behavior and remaining gaps in `NEXT_PHASE_TASKS.md`. Confirm the pushed
branch matches the local commit. Inspect checks and actual review output against
the latest PR commit: a successful review job can have skipped review. After a
user-approved merge, check main's own CI at its merge commit separately. A PR's
green checks are not evidence for a different main revision.

On this Mac on September 24, Apple's Git and Make were blocked by an unaccepted
Xcode license. Existing `/opt/homebrew/bin/git` worked; direct `.venv/bin/python`
avoids Make. Accepting Apple's agreement is CJ's action, not an agent workaround.
No global developer-tool settings need changing for the direct test command.
