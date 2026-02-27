# Week 12: Goal Continuity - COMPLETE

**Date:** February 27, 2026
**Status:** COMPLETE
**Tests:** 331/331 passing (100%)

---

## Summary

Week 12 gives Penny a memory for *unfinished business*. Goals detected in conversation are tracked across sessions and revived at appropriate moments — always within the ProactivityBudget hard limits from Week 11.

---

## What Was Built

### Component 1: GoalTracker

**File:** `src/personality/goal_tracker.py` (~340 lines)

Persists user goals across sessions with full lifecycle management.

**Goal States:**
```
detected → active → suspended → completed
                              → abandoned
```

**Auto-suspension:** Goals with no activity after 1 day move to `suspended` automatically (configurable via `AUTO_SUSPEND_DAYS`).

**Detection patterns** (regex, case-insensitive):
- `"I want to..."`, `"I need to..."`, `"I'm trying to..."`
- `"working on"`, `"building"`, `"fixing"`, `"setting up"`
- `"my goal is"`, `"help me"`

**Completion signals:** `"done"`, `"fixed"`, `"thanks, that worked"`, `"solved"`, etc.

**Abandon signals:** `"nevermind"`, `"forget it"`, `"moving on"`, `"scrap it"`, etc.

| Method | Description |
|--------|-------------|
| `process_turn(message)` | Main entry point — call each turn |
| `get_active_goals()` | Goals currently being worked on |
| `get_suspended_goals()` | Goals dormant > N days |
| `mark_completed(goal_id)` | Mark goal done |
| `mark_abandoned(goal_id)` | Mark goal dropped |
| `mark_suspended(goal_id)` | Manually suspend |
| `days_since_last_mentioned(goal_id)` | Dormancy in days |
| `get_goals_report()` | Summary statistics |

**Database Tables:**
```sql
goals (
    goal_id, description, state, created_at,
    last_mentioned, completed_at, session_id,
    context_snippet, mention_count
)
goal_events (
    id, goal_id, event_type, timestamp, session_id, note
)
```

---

### Component 2: FollowUpEngine

**File:** `src/personality/followup_engine.py` (~160 lines)

Decides when and how to follow up on suspended goals. **Every follow-up goes through `ProactivityBudget.can_nudge_about_goal()` — no exceptions.**

**Message types:**
| Type | When | Example |
|------|------|---------|
| `soft_nudge` | < 7 days dormant | "Hey, still working on finish the report?" |
| `permission_request` | ≥ 7 days (requires permission) | "Quick check — do you still want me to follow up on 'finish the report'?" |
| `last_chance` | ≥ 12 days dormant | "Last chance to revive this one: finish the report. Still relevant?" |

| Method | Description |
|--------|-------------|
| `get_followups_for_session()` | Generate follow-ups at session start |
| `needs_permission(goal_id)` | Check if permission needed |
| `can_follow_up(goal_id)` | Quick budget check |
| `generate_soft_nudge(goal_id)` | Generate single nudge message |
| `get_followup_summary()` | Overview of pending follow-ups |

---

### Component 3: Pipeline Integration

**File:** `research_first_pipeline.py` (modified)

**Feature flag:** `self.goal_continuity_enabled = False` (safe rollout)

**Integration point (Step 1.15 in `think()`):**
```python
if self.goal_tracker:
    goal_result = self.goal_tracker.process_turn(
        actual_command, session_id=conversation_id
    )
    if goal_result["new_goal"]:
        logger.info(f"🎯 New goal tracked: ...")
    if goal_result["updated_goals"]:
        logger.info(f"🎯 {len(goal_result['updated_goals'])} goal(s) updated")
```

**Session start follow-ups** (via `FollowUpEngine.get_followups_for_session()`):
- Called once at the beginning of each session
- Surfaces max 1 follow-up by default
- Respects ProactivityBudget before every nudge

---

## Safety Design

Goal Continuity is built *on top of* Week 11's ProactivityBudget, so all hard limits apply automatically:

```
Goal suspended for 2 days?
    → Soft nudge (if budget allows)

Goal suspended for 7+ days?
    → Must ask permission first (budget blocks direct nudge)

Goal suspended for 12+ days?
    → Last-chance message

Goal suspended for 14+ days?
    → Can resurrect (max 1/week via can_resurrect_goal())

Daily budget exhausted (2 nudges)?
    → No follow-ups, full stop
```

---

## Configuration

### penny_config.json

```json
{
    "goal_continuity": {
        "enabled": false,
        "db_path": "data/personality_tracking.db",
        "auto_suspend_days": 1,
        "followup": {
            "max_per_session": 1,
            "min_confidence": 0.8
        }
    }
}
```

### Enabling

```json
"goal_continuity": {
    "enabled": true
}
```

Or via code:
```python
pipeline = ResearchFirstPipeline()
pipeline.goal_continuity_enabled = True
pipeline.goal_tracker = GoalTracker()
pipeline.followup_engine = FollowUpEngine(pipeline.goal_tracker, pipeline.proactivity_budget)
```

---

## Test Coverage

### New Tests: 59 tests

| File | Tests | Description |
|------|-------|-------------|
| `test_goal_tracker.py` | 29 | Pattern detection, lifecycle, suspension |
| `test_followup_engine.py` | 17 | Budget gating, message types, summary |
| `test_goal_continuity_integration.py` | 13 | E2E, multi-session, safety |

### Full Test Suite: 331 tests

| Component | Tests |
|-----------|-------|
| Hebbian (Weeks 9–10) | 137 |
| Judgment (Week 8.5) | 62 |
| Outcome Tracking (Week 11) | 73 |
| **Goal Continuity (Week 12)** | **59** |
| **Total** | **331** |

---

## Files Created/Modified

### Created
| File | Lines | Description |
|------|-------|-------------|
| `src/personality/goal_tracker.py` | ~340 | GoalTracker |
| `src/personality/followup_engine.py` | ~160 | FollowUpEngine |
| `tests/test_goal_tracker.py` | ~220 | 29 tests |
| `tests/test_followup_engine.py` | ~170 | 17 tests |
| `tests/test_goal_continuity_integration.py` | ~180 | 13 tests |
| `WEEK12_COMPLETE.md` | — | This document |

### Modified
| File | Changes |
|------|---------|
| `research_first_pipeline.py` | Week 12 imports + init + Step 1.15 |
| `penny_config.json` | `goal_continuity` section added |

---

## Usage Examples

### Track a goal

```python
tracker = GoalTracker()
result = tracker.process_turn("I want to add rate limiting to the API")
if result["new_goal"]:
    print(f"Tracking: {result['new_goal']['description']}")
```

### Session start follow-ups

```python
budget = ProactivityBudget()
engine = FollowUpEngine(tracker, budget)

followups = engine.get_followups_for_session(session_id="sess_xyz")
for f in followups:
    print(f"[{f['type']}] {f['message']}")
```

### Goals report

```python
report = tracker.get_goals_report()
print(f"Active: {report['active']}")
print(f"Suspended: {report['suspended']}")
print(f"Completed: {report['completed']}")
```

---

## What's Next

### Week 13: User Model
- Penny maintains explicit beliefs about the user
- Confidence scores for each belief
- User-correctable (transparent reasoning)
- Example: `{"prefers_brief_answers": 0.85, "expert_in_python": 0.72}`

---

**Completed:** February 27, 2026
**Tests:** 331/331 passing (100%)
**Ready for:** Week 13 (User Model)
