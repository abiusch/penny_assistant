# Week 13: User Model - COMPLETE

**Date:** February 27, 2026
**Status:** COMPLETE
**Tests:** 397/397 passing (100%)

---

## Summary

Week 13 gives Penny explicit, human-readable knowledge about the user — built as a lightweight knowledge graph as recommended in the 2026 AI Landscape Review. Beliefs are extracted from natural language, boosted with each supporting observation, and the user can inspect and correct them at any time.

> "Penny should be able to surface her beliefs on demand: 'Here's what I think I know about you — want to correct anything?' (no commercial assistant does this)"
> — 2026 AI Landscape Review

---

## What Was Built

### Component 1: UserBeliefStore

**File:** `src/personality/user_belief_store.py` (~260 lines)

Lightweight knowledge graph: `subject → predicate → object_value` triples.

**Typed predicates (vocabulary):**

| Category | Predicates |
|----------|-----------|
| Preferences | `prefers`, `dislikes`, `likes` |
| Expertise | `expert_in`, `learning`, `unfamiliar_with` |
| Work | `works_on`, `works_with`, `works_at` |
| Personal | `is`, `has`, `uses` |
| Communication | `responds_well_to`, `frustrated_by` |

**Confidence model:**
- New belief: `BASE_CONFIDENCE = 0.5`
- Each new evidence: `+0.08` (capped at `MAX_CONFIDENCE = 0.97`)
- User correction: immediately set to `CORRECTION_CONFIDENCE = 0.95`

| Method | Description |
|--------|-------------|
| `add_or_update_belief()` | Upsert belief, boost confidence |
| `get_beliefs()` | Retrieve, filter by predicate/confidence |
| `correct_belief()` | User explicitly corrects a belief |
| `remove_belief()` | Delete a belief |
| `get_summary()` | Human-readable summary with correction markers |
| `get_belief_report()` | Statistics overview |

**Database Tables:**
```sql
user_beliefs       -- (belief_id, subject, predicate, object_value,
                        confidence, evidence_count, context, ...)
belief_evidence    -- Raw evidence text per belief
belief_corrections -- Audit log of user corrections
```

---

### Component 2: BeliefExtractor

**File:** `src/personality/belief_extractor.py` (~190 lines)

Extracts beliefs from natural language using regex patterns.

**Example extractions:**

| User says | Extracted belief |
|-----------|-----------------|
| "I'm an expert in Python" | `expert_in → python` |
| "I use FastAPI for all my projects" | `works_with → fastapi` |
| "I prefer brief answers" | `prefers → brief_answers` |
| "I've never used Kubernetes" | `unfamiliar_with → kubernetes` |
| "I'm learning Rust" | `learning → rust` |
| "I'm working on penny assistant" | `works_on → penny_assistant` |
| "I'm on macOS" | `uses → macos` |

**Design:** high precision > high recall. Only extracts beliefs from explicit statements — no guessing from tone.

| Method | Description |
|--------|-------------|
| `extract_from_turn()` | Extract all beliefs from one message |
| `detect_correction()` | Check if user is correcting something |
| `extract_explicit_correction()` | Apply a correction |
| `get_relevant_beliefs()` | Retrieve beliefs relevant to current context |
| `build_context_snippet()` | Compact string for LLM prompt injection |

**Context injection format:**
```
[User: expert_in→python, prefers→brief_answers, works_on→penny_assistant]
```

---

### Component 3: Pipeline Integration

**File:** `research_first_pipeline.py` (modified)

**Feature flag:** `self.user_model_enabled = False` (safe rollout)

**Integration point (Step 1.2 in `think()`):**
```python
if self.belief_extractor:
    new_beliefs = self.belief_extractor.extract_from_turn(
        actual_command, session_id=conversation_id
    )
    if new_beliefs:
        logger.info(f"🧠 UserModel: {len(new_beliefs)} belief(s) extracted")
```

**Optional prompt injection** (when user model enabled):
```python
belief_context = self.belief_extractor.build_context_snippet(
    context_keywords=["python", "api"]
)
# → "[User: expert_in→python, prefers→brief_answers]"
# Inject into LLM system prompt
```

---

## Transparency: "What Do You Think You Know About Me?"

Penny can generate a full belief report on demand:

```python
summary = pipeline.belief_store.get_summary()
```

Output:
```
Here's what I think I know about you:
  • expert in: python (85% confident)
  • prefers: brief answers (78% confident)
  • works on: penny assistant (92% confident)
  • learning: rust (50% confident)
  • uses: macos (71% confident) ✓

Want to correct anything?
```

The `✓` marker shows beliefs confirmed by the user via explicit correction.

---

## Architecture (Dual Memory — as recommended in AI Landscape Review)

```
┌─────────────────────────────────────────────────────┐
│                 Penny's Memory                       │
│                                                      │
│  ┌─────────────────────┐  ┌──────────────────────┐  │
│  │  IMPLICIT PATTERNS  │  │   EXPLICIT BELIEFS   │  │
│  │   (Hebbian, W9-10)  │  │   (UserModel, W13)   │  │
│  │                     │  │                      │  │
│  │ Word associations   │  │ CJ → expert_in       │  │
│  │ Dim co-activations  │  │    → python (85%)    │  │
│  │ Sequence patterns   │  │ CJ → prefers         │  │
│  │                     │  │    → brief (78%)     │  │
│  │ Statistical, opaque │  │ Typed, inspectable,  │  │
│  │ Learned from use    │  │ user-correctable     │  │
│  └─────────────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## Configuration

### penny_config.json

```json
{
    "user_model": {
        "enabled": false,
        "db_path": "data/personality_tracking.db",
        "subject": "user",
        "extraction": {
            "min_confidence_for_context": 0.65,
            "max_beliefs_in_context": 5
        },
        "summary": {
            "min_confidence": 0.6,
            "max_beliefs": 10
        }
    }
}
```

---

## Test Coverage

### New Tests: 66 tests

| File | Tests | Description |
|------|-------|-------------|
| `test_user_belief_store.py` | 28 | Store CRUD, confidence, corrections |
| `test_belief_extractor.py` | 24 | Pattern extraction, signals |
| `test_user_model_integration.py` | 14 | Multi-turn, corrections, context |

### Full Test Suite: 397 tests

| Week | Component | Tests |
|------|-----------|-------|
| 8.5 | Judgment & Clarify | 62 |
| 9–10 | Hebbian Learning | 137 |
| 11 | Outcome Tracking | 73 |
| 12 | Goal Continuity | 59 |
| **13** | **User Model** | **66** |
| **Total** | | **397** |

---

## Files Created/Modified

### Created
| File | Lines | Description |
|------|-------|-------------|
| `src/personality/user_belief_store.py` | ~260 | Knowledge graph store |
| `src/personality/belief_extractor.py` | ~190 | NLP extraction layer |
| `tests/test_user_belief_store.py` | ~220 | 28 tests |
| `tests/test_belief_extractor.py` | ~180 | 24 tests |
| `tests/test_user_model_integration.py` | ~160 | 14 tests |
| `WEEK13_COMPLETE.md` | — | This document |

### Modified
| File | Changes |
|------|---------|
| `research_first_pipeline.py` | Week 13 imports + init + Step 1.2 |
| `penny_config.json` | `user_model` section added |

---

## What's Next

The core learning systems (Weeks 8.5–13) are now complete:

| System | Status |
|--------|--------|
| Judgment & Clarify | ✅ Week 8.5 |
| Hebbian Learning | ✅ Weeks 9–10 |
| Outcome Tracking | ✅ Week 11 |
| Goal Continuity | ✅ Week 12 |
| User Model | ✅ Week 13 |

### Phase 5: Polish & Productization (Weeks 14–18)
- **Week 14:** Platform Abstraction Layer
- **Week 15:** Capability Awareness System
- **Week 16:** Repository Organization
- **Week 17:** Penny Console (Observability Dashboard)
- **Week 18:** Cross-Platform Support

### High-Priority Improvements (from AI Landscape Review)
- Streaming TTS + barge-in support (transformative voice UX)
- Two-path RAG (vector + KG) — KG now available from Week 13
- LLM benchmark: Nemotron vs. Qwen3-8B / Llama 3.1 8B

---

**Completed:** February 27, 2026
**Tests:** 397/397 passing (100%)
**Phase 4 (Weeks 11–13): COMPLETE**
