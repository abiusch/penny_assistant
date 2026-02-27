# Week 11: Outcome Tracking - COMPLETE

**Date:** February 27, 2026
**Status:** COMPLETE
**Tests:** 272/272 passing (100%)

---

## Summary

Week 11 gives Penny the ability to learn from results, not just patterns. The system tracks whether responses help or hurt, learns which strategies work in which contexts, and — critically — prevents the "helpful-stalker bot" failure mode identified in the 2026 AI Risk Analysis.

---

## What Was Built

### Component 1: OutcomeTracker

**File:** `src/personality/outcome_tracker.py` (~300 lines)

Tracks response effectiveness over time.

| Method | Description |
|--------|-------------|
| `observe_outcome()` | Record one outcome (positive/negative/neutral) |
| `detect_user_reaction()` | Auto-detect reaction from follow-up text |
| `get_strategy_success_rate()` | Rolling success % per strategy per context |
| `suggest_best_strategy()` | Recommend best strategy from history |
| `get_outcome_report()` | Full statistics overview |
| `generate_response_id()` | Unique ID for response tracking |

**Reaction Detection:**
- **Positive signals:** "thanks", "perfect", "worked", "great", "👍", etc.
- **Negative signals:** "didn't work", "wrong", "unclear", "too much", "👎", etc.
- **Neutral:** everything else (excluded from success rate calc)

**Response Types:**
- `code_example` — contains ` ``` `
- `brief_answer` — < 100 chars
- `detailed_explanation` — > 500 chars
- `conversational` — 100–500 chars, no code

**Database Tables:**
```sql
outcome_observations     -- Individual outcome records
strategy_success_rates   -- Aggregated stats per strategy+context
user_reaction_patterns   -- Raw reaction detection log
```

---

### Component 2: ProactivityBudget

**File:** `src/personality/proactivity_budget.py` (~200 lines)

**Risk 2 mitigation: Runaway Autonomy prevention.**

Enforces hard limits on proactive behaviour to prevent "helpful-stalker bot" syndrome.

#### Hard Limits (NOT configurable)

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_NUDGES_PER_DAY` | 2 | Max unprompted mentions per day |
| `MAX_GOAL_RESURRECTIONS_WEEK` | 1 | Max dormant goal resurfaces per week |
| `DORMANT_THRESHOLD_DAYS` | 14 | Goal is "dormant" after 14 days |
| `REQUIRE_PERMISSION_AFTER_DAYS` | 7 | Must ask user if goal > 7 days old |
| `MIN_CONFIDENCE_FOR_PROACTIVE` | 0.8 | Minimum confidence to nudge |

| Method | Description |
|--------|-------------|
| `can_nudge_about_goal()` | Check all safety conditions |
| `can_resurrect_goal()` | Check if dormant goal can resurface |
| `request_permission_for_goal()` | Generate permission-request message |
| `record_nudge()` | Track against daily budget |
| `record_resurrection()` | Track against weekly budget |
| `get_budget_summary()` | Show current usage + hard limits |

**Database Tables:**
```sql
proactive_nudges      -- Daily nudge log
goal_resurrections    -- Weekly resurrection log
```

---

### Component 3: Pipeline Integration

**File:** `research_first_pipeline.py` (modified)

**Feature flag:** `self.outcome_tracking_enabled = False` (safe rollout)

**Integration points:**

1. **Turn start** — detect reaction from current user message about the *previous* response
2. **Turn end** — tag new response with a unique ID and type for next-turn detection

```python
# At turn start: detect reaction to previous response
if self.outcome_tracker and self._last_response_id:
    reaction, conf = self.outcome_tracker.detect_user_reaction(user_message)
    if reaction != "neutral":
        self.outcome_tracker.observe_outcome(last_response_id, ...)

# At turn end: tag current response
resp_type = classify_response_type(final_response)
self._last_response_id = OutcomeTracker.generate_response_id()
self._last_response_type = resp_type
```

---

## Safety Design: Preventing Runaway Autonomy (Risk 2)

From the 2026 AI Risk Analysis, the "helpful-stalker bot" failure mode occurs when an AI:
- Proactively nudges too often about things the user has moved on from
- Resurrects old goals at bad times without asking
- Assumes intent continuity when the user has changed direction

**ProactivityBudget prevents this by:**

```
User hasn't mentioned goal for 7+ days?
    → MUST ask permission before bringing it up

Goal dormant for 14+ days?
    → Can only resurrect ONCE per week (and still need permission)

Confidence < 0.8?
    → Don't nudge at all (wait for clearer signal)

Already nudged 2 times today?
    → No more nudges regardless of goal importance
```

These limits are module-level constants, NOT config values — they can't be "turned up" by accident.

---

## Configuration

### penny_config.json

```json
{
    "outcome_tracking": {
        "enabled": false,
        "db_path": "data/personality_tracking.db",
        "proactivity_budget": {
            "max_nudges_per_day": 2,
            "max_resurrections_per_week": 1,
            "dormant_threshold_days": 14,
            "permission_required_after_days": 7,
            "min_confidence_for_proactive": 0.8
        }
    }
}
```

> Note: `max_nudges_per_day` and related values are shown for documentation only.
> The actual limits are hard-coded module constants in `proactivity_budget.py`.

### Enabling outcome tracking

```json
"outcome_tracking": {
    "enabled": true
}
```

Or via code:
```python
pipeline = ResearchFirstPipeline()
pipeline.outcome_tracking_enabled = True
pipeline.outcome_tracker = OutcomeTracker()
pipeline.proactivity_budget = ProactivityBudget()
```

---

## Test Coverage

### New Tests: 73 tests

| File | Tests | Description |
|------|-------|-------------|
| `test_outcome_tracker.py` | 33 | Recording, detection, rates, reporting |
| `test_proactivity_budget.py` | 26 | Limits, thresholds, messages, summary |
| `test_outcome_integration.py` | 14 | E2E flow, multi-turn, safety |

### Full Test Suite: 272 tests

| Component | Tests |
|-----------|-------|
| Hebbian Vocabulary | 24 |
| Hebbian Dimensions | 15 |
| Hebbian Sequences | 22 |
| Hebbian Integration | 14 |
| Hebbian Manager | 36 |
| Hebbian Safety | 26 |
| Judgment Phase 1A | 10 |
| Judgment Phase 1B | 20 |
| Judgment Phase 1C | 13 |
| Penny Style Clarifier | 18 |
| Pipeline Debug | 1 |
| **Outcome Tracker** | **33** |
| **Proactivity Budget** | **26** |
| **Outcome Integration** | **14** |
| **Total** | **272** |

---

## Files Created/Modified

### Created
| File | Lines | Description |
|------|-------|-------------|
| `src/personality/outcome_tracker.py` | ~300 | OutcomeTracker |
| `src/personality/proactivity_budget.py` | ~200 | ProactivityBudget |
| `tests/test_outcome_tracker.py` | ~200 | 33 tests |
| `tests/test_proactivity_budget.py` | ~170 | 26 tests |
| `tests/test_outcome_integration.py` | ~160 | 14 tests |
| `WEEK11_COMPLETE.md` | — | This document |

### Modified
| File | Changes |
|------|---------|
| `research_first_pipeline.py` | Week 11 imports + init + integration |
| `penny_config.json` | `outcome_tracking` section added |

---

## Usage Examples

### Check what's working

```python
tracker = OutcomeTracker()
report = tracker.get_outcome_report()
print(f"Overall success rate: {report['overall_success_rate']:.1%}")
for s in report['strategies']:
    print(f"  {s['strategy']}: {s['success_rate']:.1%} ({s['positive']}+/{s['negative']}-)")
```

### Detect reaction

```python
reaction, confidence = tracker.detect_user_reaction("that worked perfectly!")
# → ("positive", 0.7)
```

### Check proactivity budget

```python
budget = ProactivityBudget()
summary = budget.get_budget_summary()
print(f"Nudges today: {summary['nudges_today']}/{summary['limits']['max_nudges_per_day']}")
print(f"Resurrections this week: {summary['resurrections_this_week']}/1")

# Before nudging:
allowed, reason = budget.can_nudge_about_goal(
    "project_x",
    last_mentioned=datetime(2026, 2, 20),
    confidence=0.85
)
if not allowed:
    print(f"Can't nudge: {reason}")
```

---

## What's Next

### Week 12: Goal Continuity
- Track unfinished business across sessions
- Remember suspended tasks
- Proactive follow-ups (within ProactivityBudget limits!)

### Week 13: User Model
- Explicit beliefs about the user
- Confidence scores per belief
- User-correctable model

---

**Completed:** February 27, 2026
**Tests:** 272/272 passing (100%)
**Ready for:** Week 12 (Goal Continuity)
