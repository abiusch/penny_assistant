# Penny architecture and behavior map

Source review: September 24, 2026, against merged `main` at `6b06d7c` (#41).
This is a navigation aid, not another backlog. Read [current tasks](../NEXT_PHASE_TASKS.md)
for later changes and [verification](VERIFICATION.md) before running checks.
Code presence, offline test coverage and live verification are different evidence.

## Conversation path

The text launcher [chat_penny.py](../chat_penny.py) and Flask backend
[server.py](../web_interface/server.py) construct
[ResearchFirstPipeline](../research_first_pipeline.py). Its `think()` method
requires `State.THINKING`. The normal path runs input hooks, judgment/clarification,
emotion processing, research, context retrieval, prompt construction and the tool
loop, then response processing, memory storage and post-turn bookkeeping.
Clarification and generation failures return early.

The web backend shares one pipeline object across requests. Concurrent turn
isolation is not established. The text launcher's legacy memory commands still
reference removed `base_memory`/`enhanced_memory` attributes. `make run` launches
[penny_with_plugins.py](../penny_with_plugins.py), a separate voice path; do not
assume every entry point exercises the research pipeline's contracts.

## Source and coverage index

Test paths below are relative to `tests/`. Canonical files are selected by
[pytest.ini](../pytest.ini); characterization files require a separate command.

| Concern | Implementation to inspect | Existing evidence and boundary |
| --- | --- | --- |
| Conversation orchestration | [research_first_pipeline.py](../research_first_pipeline.py): `think`, `_input_prehooks`, `_persist_turn` | `test_pipeline_characterization.py`, `test_pipeline_characterization_extended.py`: offline contracts, with a stubbed tool loop; not live model quality |
| Config and data roots | [runtime_paths.py](../src/runtime_paths.py), [path rules](runtime_paths.md) | `test_runtime_paths.py`: scratch-directory launches, key preservation, restart retrieval and helper isolation |
| Model selection and errors | [registry.py](../src/llm/registry.py), [adapter](../src/adapters/llm/openai_compat.py), [errors.py](../src/llm/errors.py) | `test_llm_registry.py`, `test_model_error_handling.py`: selected client, sanitized failure replies and skipped failed-turn persistence; real requests are mocked |
| Tool parsing, replay and execution | [tool_orchestrator.py](../src/tools/tool_orchestrator.py), [tool_registry.py](../src/tools/tool_registry.py) | `test_tool_roundtrip.py`, `test_tool_request_safety.py`: real tool round trips with synthetic model responses, request threads and worker timeouts |
| Conversation memory | [semantic_memory.py](../src/memory/semantic_memory.py), [vector_store.py](../src/memory/vector_store.py), [context_manager.py](../src/memory/context_manager.py) | `test_memory_restart.py`: restart ID mapping/counts and similarity exclusion; not crash recovery or concurrent writer safety |
| Memory failures | [vector_store.py](../src/memory/vector_store.py), pipeline `_persist_turn`, [recovery limits](memory_storage_recovery.md) | `test_memory_storage_errors.py`: invalid pairs, failed writes/reloads and skipped post-save effects; not paired-file atomicity |
| Emotion consent and deletion | [consent_manager.py](../src/memory/consent_manager.py), [emotional_continuity.py](../src/memory/emotional_continuity.py), [consent behavior](emotional_data_consent.md) | `test_consent_storage.py`: opt-out, retained history, deletion retries and participating writer ordering; not a transaction for all conversation data |
| Personality voice and adaptation | [prompt builder](../src/personality/dynamic_personality_prompt_builder.py), [post-processor](../src/personality/personality_response_post_processor.py), [tracker](../personality_tracker.py), pipeline `_update_dimension_if_changed` | Characterizations cover control/treatment routing and prompt wiring; do not establish naturalness or live adaptation quality |
| Snapshots and forgetting | [personality_snapshots.py](../src/personality/personality_snapshots.py), [forgetting_mechanism.py](../src/memory/forgetting_mechanism.py) | Consent tests cover emotional-thread redaction; characterizations cover snapshot/decay hooks, not full restore or long-term quality |
| Hebbian learning | [hebbian package](../src/personality/hebbian/), pipeline `_is_safe_to_learn` | Canonical `test_hebbian_*.py`: subsystem behavior/safety; pipeline switch is off by default |
| Outcomes and proactivity | [outcome_tracker.py](../src/personality/outcome_tracker.py), [proactivity_budget.py](../src/personality/proactivity_budget.py) | `test_outcome_tracker.py`, `test_proactivity_budget.py`, `test_outcome_integration.py`; pipeline switch is off by default |
| Goals and follow-ups | [goal_tracker.py](../src/personality/goal_tracker.py), [followup_engine.py](../src/personality/followup_engine.py) | `test_goal_tracker.py`, `test_followup_engine.py`, `test_goal_continuity_integration.py`; pipeline switch is off by default |
| User beliefs | [user_belief_store.py](../src/personality/user_belief_store.py), [belief_extractor.py](../src/personality/belief_extractor.py) | `test_user_belief_store.py`, `test_belief_extractor.py`, `test_user_model_integration.py`, `test_user_model_enhancements.py`; pipeline switch is off by default |
| Capability enforcement | [tool_registry.py](../src/tools/tool_registry.py) | `test_capability_gate.py`: two strict expected failures expose declaration drift and the `enable_safety=False` bypass; neither is fixed |

## Contracts to preserve

Penny's prompt builder calls for natural, matter-of-fact conversation, dry wit and
context-appropriate sarcasm. It rejects forced humor and excessive enthusiasm.
The prompt builder and post-processor default to a learning confidence threshold
of 0.65. Numeric dimension updates in `_update_dimension_if_changed` blend by
the dimension's learning rate. Preserve explicit preferences and gradual adaptation;
historical README examples are not the current voice specification.

The constructor sets `hebbian_enabled`, `outcome_tracking_enabled`,
`goal_continuity_enabled` and `user_model_enabled` to `False`. These implemented
systems are not automatically active. Do not enable them as incidental cleanup.
Preserve learning confidence checks, staging and budgets, and follow-up limits.

The research pipeline's ordinary conversation history lives in semantic memory:
a FAISS `.index` plus `.pkl` metadata pair. Recent context is an in-memory cache;
personality, consent and snapshots have separate stores. There is no general
transaction covering all of them. Metadata-only conversation deletion leaves
vector slots in the index. Merged [PR #41](https://github.com/abiusch/penny_assistant/pull/41)
adds failure containment: invalid pairs refuse startup, failed writes poison normal
store operations, and a failed conversation save preserves the generated answer
with a warning while skipping context caching and success hooks. It does not
provide paired-file transactions, automatic recovery or stale-writer merging.
Preserve its save-before-cache order and failure-side-effect tests in any post-turn
refactor. Consent deletion retains its separate pending-deletion/retry path.

Tracking consent defaults to off. Emotion inference may inform the current reply;
durable derived tracking fields require consent. CJ chose to keep conversation
text when deleting emotional data. Preserve encryption keys, ordinary history,
explicit preferences, deletion cutoffs and pending-deletion retries. See the
[consent contract](emotional_data_consent.md) for retention and deletion boundaries.

## Developer continuity is separate from Penny's memory

Project Overlord supplied useful architecture-index and handoff ideas. Its generic
bootstrap, permission rules, roadmap convention and hooks have not been installed
in Penny. [AGENTS.md](../AGENTS.md) remains the approved agreement; the task list
remains the backlog. The nested Overlord checkout is a separate repository.

CJ reports Claude Code archives at `/Users/CJ/Development/session-archives`, outside
the project. They are developer evidence, never input to Penny's personal memory,
embeddings or learning. Archive installation/scheduling was not revalidated in this
pass. Optional model summaries/indexing are off; Codex capture was not implemented.
Penny's privacy, voice and learning behavior remain responsibilities of runtime
code and its tests.
