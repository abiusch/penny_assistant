# PRD — Source-of-Truth (SoT) System for PennyGPT

**Status:** v1 Draft · **Owner:** CJ + Claude Code · **Primary user:** the coding **Agent** (human is secondary)
**One-liner:** A single, fast, read-only way for an agent to learn *exactly* how Penny is wired — every subsystem, config, database, integration, and feature flag — so sessions start informed instead of re-deriving context.

> **TL;DR for an agent landing here cold:**
> 1. Read §6 "Get Familiar" protocol.
> 2. Run `make sot-pull` → emits `docs/_generated/manifest.local.json` + `.md`.
> 3. GREP `docs/SYSTEM_BLUEPRINT.md` for your concern (it maps concern → source → command).
> 4. To check drift/health, run `make sot-validate`.

---

## 1. Problem & motivation

- PennyGPT spans **8 cognitive subsystems** (judgment, hebbian, outcome tracking, goal continuity, user model, personality, memory, tools), a **voice pipeline** (STT → LLM → TTS), a **research pipeline**, and **30+ SQLite databases** in `data/`. The wiring is implicit and scattered across `penny_config.json`, hardcoded paths, feature flags, and live database state.
- Every new Claude Code session re-discovers the same facts — which LLM is active, what feature flags are on, which databases matter vs which are test artifacts, where the canonical entry points are — wasting tokens and risking wrong assumptions that **break working code** (proven by the May 2026 experiments/ regression).
- There is no single command that answers: *"What is the current, real state of everything, and how is each value set?"*
- `NEXT_PHASE_TASKS.md` is the current single-source-of-truth, but it's a planning document, not a live system inventory. It can't tell you if the LLM endpoint is reachable, if a database is corrupted, or if feature flags in config match what the pipeline actually reads.

## 2. Goals / non-goals

**Goals**
- **G1. One action → full inventory.** `make sot-pull` queries all live state into one structured artifact.
- **G2. Grounded, never guessed.** Values come from live sources (config files, database introspection, endpoint checks), not from memory or stale docs.
- **G3. Agent-digestible.** A compact, GREP-indexed blueprint maps *concern → where it lives → how to pull/verify it*.
- **G4. Safe to commit.** No API keys or secrets — only names, presence, and digests.
- **G5. Drift-aware.** A validator flags when reality diverges from documented invariants (e.g., config says hebbian enabled but database tables don't exist).

**Non-goals**
- Not a replacement for `NEXT_PHASE_TASKS.md` (which remains the planning/roadmap document).
- Not a deploy tool or runtime monitor.
- Not a replacement for the architecture audit (`PENNY_ARCHITECTURE_AUDIT.md`).

## 3. Users & top user journeys

| User | Journey | Today | With SoT |
|---|---|---|---|
| **Claude Code (cold start)** | "Understand Penny before touching it" | Reads NEXT_PHASE_TASKS.md, greps code, probes files ad hoc (4.5s pipeline construction to test anything) | Reads §6, runs `make sot-pull`, greps blueprint — minutes, grounded |
| **Claude Code (targeted task)** | "Where is the Hebbian quarantine threshold configured?" | Searches penny_config.json, then code, then docs — hope it's consistent | GREP blueprint → `penny_config.json → hebbian.quarantine.min_observations` |
| **Claude Code (pre-change safety)** | "Will this break the pipeline? What's the real state?" | Manual file reads, run diagnostics_week6.py | `make sot-validate` → PASS/FAIL on all invariants |
| **CJ (session handoff)** | "Give next agent full context" | Write session summary manually | Commit manifest + blueprint — agent reads generated state |

**Action flow (happy path):**
```
session start
  └─> read CLAUDE.md pointer ──> SYSTEM_BLUEPRINT.md §"Get Familiar"
        └─> make sot-pull                          (read-only introspection)
              └─> docs/_generated/manifest.local.json (+ .md render)
        └─> GREP blueprint for concern ──> source + pull command + invariant
  task work …
  └─> make sot-validate                            (confirm no drift before/after change)
```

## 4. Solution architecture (two layers + a validator)

### Layer A — Live introspection: `scripts/sot_pull.py`

A **read-only** Python script that queries every source and writes:
- `docs/_generated/manifest.local.json` — structured, diffable machine truth.
- `docs/_generated/manifest.local.md` — human/agent-readable render (tables).

**Sources & what it pulls:**

| Domain | Source | Pulls | Secret handling |
|---|---|---|---|
| **LLM endpoint** | `penny_config.json` → `llm.*` + HTTP probe `localhost:1234/v1/models` | Active model, registered models, endpoint reachability, provider | API key name only (`lm-studio`) |
| **Feature flags** | `penny_config.json` → `judgment/hebbian/outcome/goal/user_model.enabled` | All flag states (true/false) | — |
| **Config values** | `penny_config.json` (full) | All non-secret config values, thresholds, timeouts | Redact any key matching `*api_key*`, `*secret*`, `*token*` |
| **Database inventory** | `data/*.db` file listing + `PRAGMA table_list` on each | File sizes, table counts, last modified, schema summary | — |
| **Primary DB health** | `data/personality_tracking.db` → `PRAGMA integrity_check` + key table counts | Integrity status, row counts for: user_beliefs, hebbian_staging_patterns, outcome_observations, goal_items, proactive_nudges | — |
| **Vector store** | `data/embeddings/` listing | Index files present, sizes | — |
| **Entry points** | Check existence of `penny.py`, `chat_penny.py`, `research_first_pipeline.py` | Present/missing, file sizes | — |
| **Test suite** | `make test --dry-run` or parse `pytest.ini` testpaths | Canonical test count, quarantined test count | — |
| **Diagnostics** | `python diagnostics_week6.py --json` (if available) | Pass/fail counts | — |
| **Git state** | `git rev-parse HEAD`, `git status --porcelain`, `git log -1` | Current commit, dirty files count, last commit message | — |
| **Python env** | `python --version`, key package versions | Python version, pytest, sqlite3 | — |
| **TTS/STT config** | `penny_config.json` → `tts.*`, `stt.*` | Backend chain, active voice, model size | ElevenLabs key: name only |
| **Secrets inventory** | `data/.encryption_key`, `.env`, `penny_config.json` | **Names + presence only** | ⚠️ Never values |
| **Disk usage** | `du -sh data/`, `du -sh data/embeddings/`, total repo size | Storage consumption | — |

**Security rules for Layer A:**
- Read-only. No writes, no network calls except LLM endpoint probe.
- Anything matching `*api_key*`, `*secret*`, `*token*`, `*password*`, `*encryption_key*` → prints `<key_name> → SET (digest …)` / `UNSET`, never the value.
- Script **aborts with error** if redaction self-test detects a potential secret leak in output.
- Output JSON is **safe to commit** to git.

### Layer B — Curated blueprint: `docs/SYSTEM_BLUEPRINT.md`

The durable "why/how" that can't be auto-pulled, plus the GREP index. Sections:

- **Get Familiar** — the §6 protocol, inlined.
- **GREP INDEX** — the heart (see §5): `concern | where it lives | pull command | invariant`.
- **Architecture topology** — pipeline flow, subsystem dependencies, database roles.
- **Subsystem wiring map** — which subsystems talk to which, integration points, feature flag dependencies.
- **Entry points** — canonical ways to run Penny (voice, chat, server, tests).
- **Configuration model** — what's in penny_config.json vs hardcoded vs database-driven.
- **Database map** — which .db files are production vs test artifacts vs legacy.
- **Safety & security** — encryption, PII, GDPR compliance, proactivity budget limits.
- **Update protocol** — see §7.

### Validator: `scripts/sot_validate.py`

Asserts invariants (PASS/FAIL, exit code 0 or 1) for CI and pre-change gates.

**SoT relationship:** *pull = inventory (what is), validate = contract (what must be).*

**Invariants to check:**

| Check | Expected | Severity |
|---|---|---|
| `penny_config.json` is valid JSON | parseable | FAIL |
| LLM endpoint reachable | HTTP 200 from `localhost:1234/v1/models` | WARN |
| `data/personality_tracking.db` integrity | `PRAGMA integrity_check = ok` | FAIL |
| Primary DB tables exist | user_beliefs, hebbian_staging_patterns, outcome_observations, strategy_success_rates, goal_items, proactive_nudges | FAIL |
| Canonical entry points exist | penny.py, chat_penny.py, research_first_pipeline.py | FAIL |
| `make test` passes | exit code 0 | FAIL |
| Diagnostics pass | 18/18 | WARN |
| Feature flags match config | pipeline reads from penny_config.json, not hardcoded | WARN |
| No secrets in manifest output | redaction self-test | FAIL |
| Git working tree clean | no uncommitted changes (optional) | WARN |
| Encryption key present | `data/.encryption_key` exists | FAIL |
| No test .db files in data/ | test_*.db count = 0 (or quarantined) | WARN |
| Vector store present | `data/embeddings/` non-empty | WARN |

## 5. The GREP INDEX (format spec)

A dense table in `docs/SYSTEM_BLUEPRINT.md`, designed so `rg "<keyword>"` lands an agent on the exact answer.

| Concern (keywords) | Lives in | Pull / verify | Invariant |
|---|---|---|---|
| **llm model / active model / which llm** | `penny_config.json` → `llm.active_model` + `llm.models` | manifest → llm | `gpt-oss-20b` via localhost:1234 |
| **llm endpoint / lm studio / ollama** | `penny_config.json` → `llm.base_url` | manifest → llm + HTTP probe | reachable, HTTP 200 |
| **llm registry / model switching** | `src/llm/registry.py` | `available_models()` | matches penny_config.json models |
| **feature flags / enabled subsystems** | `penny_config.json` → `*.enabled` | manifest → feature_flags | judgment=true, rest=false (default) |
| **hebbian quarantine / promotion threshold** | `penny_config.json` → `hebbian.quarantine.*` | manifest → hebbian | min_obs=5, min_days=7 |
| **turn budget / max writes / max time** | `penny_config.json` → `hebbian.turn_budget.*` | manifest → hebbian | max_writes=5, max_time=15000ms |
| **proactivity budget / nudge limit** | `penny_config.json` → `outcome_tracking.proactivity_budget.*` | manifest → outcome | max_nudges=2/day, max_resurrections=1/week |
| **belief staging / belief quarantine** | `penny_config.json` → `user_model.*` + `belief_staging` table | manifest → user_model | min_obs=3 (via code), staging table exists |
| **belief confidence / min confidence** | `penny_config.json` → `user_model.extraction.min_confidence_for_context` | manifest → user_model | 0.65 |
| **database path / db location** | `penny_config.json` → `*.db_path` + `ResearchFirstPipeline(db_path=, data_dir=)` | manifest → databases | `data/personality_tracking.db` primary |
| **database health / integrity** | `data/personality_tracking.db` | `PRAGMA integrity_check` | ok |
| **entry point / how to run / start penny** | `ENTRY_POINTS.md` + root `.py` files | manifest → entry_points | penny.py, chat_penny.py, research_first_pipeline.py present |
| **test suite / test count / make test** | `pytest.ini` → `testpaths` | `make test --dry-run` | 451+ tests, ~2s |
| **diagnostics / health check** | `diagnostics_week6.py` | `python diagnostics_week6.py` | 18/18 |
| **tts / voice / elevenlabs** | `penny_config.json` → `tts.*` | manifest → tts | elevenlabs primary, fallback chain |
| **stt / whisper / speech recognition** | `penny_config.json` → `stt.*` | manifest → stt | whisper base model |
| **personality / tone / penny voice** | `penny_config.json` → `personality.*` | manifest → personality | penny tone, profile path valid |
| **judgment / clarification / stakes** | `penny_config.json` → `judgment.*` | manifest → judgment | enabled=true, threshold=0.4 |
| **encryption / security / gdpr** | `data/.encryption_key` | manifest → secrets | key present (never value) |
| **git state / last commit / dirty** | `git rev-parse HEAD` | manifest → git | clean working tree |
| **pipeline / think() / god object** | `research_first_pipeline.py` | `wc -l` | ~1167 lines (track for R1 decomposition) |
| **config hardcoded / feature flag drift** | `penny_config.json` vs pipeline `__init__` | validate → flag_drift | config values match runtime |
| **memory / vectors / embeddings** | `data/embeddings/` | manifest → vector_store | directory non-empty |
| **snapshot / personality snapshot** | `data/personality_snapshots/` | manifest → snapshots | directory exists |
| **refactoring / R1-R6 / audit** | `PENNY_ARCHITECTURE_AUDIT.md` | — (human-maintained) | R6 done, R1 pending Week 16 |

## 6. "Get Familiar" protocol (what every agent does first)

1. **Read the pointer.** `CLAUDE.md` (or agent rules) points here. Read this §6 + the GREP index above.
2. **Read planning context.** Scan `NEXT_PHASE_TASKS.md` §"QUICK STATUS" for current phase and priorities.
3. **Pull truth.** Run `make sot-pull`. Read the rendered `docs/_generated/manifest.local.md`.
4. **For a specific question:** `rg "<concern>" docs/SYSTEM_BLUEPRINT.md` → follow the row's pull/verify command.
5. **Before/after any change:** Run `make sot-validate` and confirm no new FAIL.
6. **Rules:**
   - Never hardcode a value you can pull from `penny_config.json`.
   - Never print a secret value (names/digests only).
   - Never assume feature flag state — check config.
   - Never modify `research_first_pipeline.py` `think()` without characterization tests.

## 7. Update protocol (keep it true)

- **Trigger to re-run `sot-pull`:** any config change, database schema change, new subsystem, feature flag toggle, LLM model switch, dependency addition.
- **Trigger to update blueprint:** a new subsystem, integration, or concern not yet in the GREP index → add a row + update the pull script.
- **Trigger to update validator:** a new invariant worth gating → add the check + expected value.
- **Drift = validator FAIL:** fix the environment or update the docs. Never ignore.
- **Ownership:** whoever makes the change updates the SoT in the **same commit**.
- **Versioning:** manifests are timestamped + git-tracked. Blueprint version bumped on structural changes.

## 8. Agent-rules integration (`CLAUDE.md`)

Create `CLAUDE.md` at project root with this section:

```md
## Source of Truth (read before acting)

- To learn the system, follow docs/SOURCE_OF_TRUTH_SYSTEM_PRD.md §6 "Get Familiar".
- Read NEXT_PHASE_TASKS.md §"QUICK STATUS" for current priorities.
- Pull live state: `make sot-pull` → `docs/_generated/manifest.local.md`.
- Find any config: `rg "<concern>" docs/SYSTEM_BLUEPRINT.md` → source → pull cmd → invariant.
- Verify before/after changes: `make sot-validate`.
- Never hardcode a pullable value; never print a secret value (names/digests only).
- Never modify `think()` without characterization tests.
- When you change config/schema/flags/integrations, regenerate the manifest
  and update the blueprint/validator in the SAME commit.

## Key files
- `NEXT_PHASE_TASKS.md` — planning & roadmap (single source of truth for priorities)
- `docs/SYSTEM_BLUEPRINT.md` — system wiring (single source of truth for configuration)
- `PENNY_ARCHITECTURE_AUDIT.md` — code quality audit & R1-R6 refactoring roadmap
- `penny_config.json` — runtime configuration (all feature flags, thresholds, LLM config)
- `ENTRY_POINTS.md` — canonical ways to run Penny

## Architecture rules
- Single-threaded development (no agent swarms). Direction > Speed.
- Safety-first: judgment before learning, staging before permanent.
- `research_first_pipeline.py` `think()` has characterization tests (`tests/test_pipeline_characterization*.py`) — extend them before changing `think()`'s behavior, don't remove coverage.
- `make test` = canonical suite (451+ tests). `make test-all` = includes quarantined legacy tests.
- See `QUARANTINE_NOTES.md` for excluded tests and reasons.
```

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Secret leakage into committed manifest | Redaction allowlist + self-test that **aborts script** if secret pattern detected in output |
| Manifest goes stale | Generated on demand (`make sot-pull`); committed copies are snapshots; validator flags drift |
| Maintenance burden | "Update in same commit" protocol; script auto-covers most fields — only new subsystems need hand-wiring |
| LLM endpoint down during pull | Pull reports `UNREACHABLE` gracefully; doesn't fail entire script |
| Database corruption undetected | Validator runs `PRAGMA integrity_check` on primary databases |
| Feature flag drift (config says X, code does Y) | Validator checks config vs pipeline behavior where possible |
| Test artifacts in data/ polluting inventory | Filter `test_*` files separately in manifest; validator warns on presence |

## 10. Phased delivery

- **Phase 0 (Now — 2-3 hours):**
  - Build `scripts/sot_validate.py` (invariant checker — PASS/FAIL/WARN on all items in §4 validator table).
  - Create `CLAUDE.md` at project root with §8 content.
  - Wire into Makefile: `make sot-validate`.

- **Phase 1 (3-4 hours):**
  - Build `scripts/sot_pull.py` covering: penny_config.json parse, database inventory + integrity, LLM probe, git state, entry points, test suite, secrets inventory, disk usage.
  - Output `docs/_generated/manifest.local.json` + `.md`.
  - Include redaction self-test (abort on leak).
  - Wire into Makefile: `make sot-pull`.

- **Phase 2 (2-3 hours):**
  - Write `docs/SYSTEM_BLUEPRINT.md` with full GREP index (seed from §5 above), topology, subsystem wiring map, database map, configuration model, security prose.
  - Update CLAUDE.md with final paths.

- **Phase 3 (1-2 hours):**
  - Add deeper checks: cross-reference penny_config.json feature flags vs pipeline `__init__` hardcoded values, database table existence vs enabled subsystem, vector store health.
  - Add `--diff` mode to compare two manifest snapshots.

- **Phase 4 (Future):**
  - Scheduled drift check (cron or git hook).
  - HTML render of manifest.
  - Integration with Week 17 Penny Console (observability dashboard).

## 11. Success metrics

- Time-to-context for a cold CC session drops from "read 5+ files + probe ad hoc" to **≤ 2 commands** (`sot-pull` + grep blueprint).
- Zero regressions caused by stale/guessed configuration values (currently the #1 source of breakage).
- Manifest + blueprint updated in the same commit as the change they describe.
- Validator catches drift before it becomes a bug (e.g., database schema doesn't match enabled feature flags).

## 12. Relationship to existing documents

| Document | Role | SoT relationship |
|---|---|---|
| `NEXT_PHASE_TASKS.md` | Planning & roadmap priorities | **Unchanged** — remains the planning SoT. Blueprint handles system wiring. |
| `PENNY_ARCHITECTURE_AUDIT.md` | Code quality assessment & refactoring roadmap | **Unchanged** — remains the refactoring guide. SoT is operational, not architectural. |
| `penny_config.json` | Runtime configuration | **Primary source** for the pull script. SoT validates it matches reality. |
| `ENTRY_POINTS.md` | How to run Penny | **Consumed** by pull script. Blueprint may supersede with richer detail. |
| `QUARANTINE_NOTES.md` | Excluded tests & reasons | **Referenced** by blueprint. Not duplicated. |
| `CURRENT_STATUS.md` | System status summary | **May be superseded** by generated manifest.local.md (auto-generated > hand-maintained). |

---

**Estimated total effort:** 8-12 hours across Phases 0-3.

**When to build:** Fits naturally as a Week 16 deliverable (Repository Organization Part 2) or as a standalone pre-Phase-5 investment.

**Companion artifacts:** `scripts/sot_validate.py`, `scripts/sot_pull.py`, `docs/SYSTEM_BLUEPRINT.md`, `CLAUDE.md`

---

*This PRD adapted from the generic Source-of-Truth System template for PennyGPT's specific architecture, subsystems, and development workflow.*
