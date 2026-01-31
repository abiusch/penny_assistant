# Hebbian Learning User Guide

> Penny's adaptive learning system that learns from your conversations

**Last Updated:** January 31, 2026
**Status:** Production Ready (Week 10 Complete)
**Tests:** 199/199 passing

---

## What is Hebbian Learning?

Hebbian Learning is based on the neuroscience principle: "neurons that fire together, wire together." In Penny's context, this means:

- **Words you use** become associated with **contexts** (casual vs formal)
- **Personality dimensions** that appear together get **linked**
- **Conversation patterns** that repeat get **recognized**

Over time, Penny adapts to your communication style without explicit programming.

---

## Quick Start

### Check Status

```python
from src.personality.hebbian import HebbianLearningManager

manager = HebbianLearningManager(db_path="data/hebbian_learning.db")
report = manager.get_learning_report()

print(f"Staging patterns: {report['staging_count']}")
print(f"Permanent patterns: {report['permanent_count']}")
print(f"Promotion rate: {report['promotion_rate']:.1%}")
```

### Enable in Pipeline

Edit `penny_config.json`:
```json
{
    "hebbian": {
        "enabled": true
    }
}
```

Or via code:
```python
from research_first_pipeline import ResearchFirstPipeline

pipeline = ResearchFirstPipeline(hebbian_enabled=True)
```

---

## Three Learning Components

### 1. Vocabulary Associator

Learns which words you use in which contexts.

**Example:**
```
You say "ngl" in casual conversations
    → Penny learns: "ngl" = casual context (0.85 strength)

You say "furthermore" in formal discussions
    → Penny learns: "furthermore" = formal context (0.78 strength)
```

**Query associations:**
```python
# Check if a term fits a context
should_use = manager.should_use_term("ngl", "casual_chat")
# Returns: True (strength > threshold)

# Get all terms for a context
casual_terms = manager.get_vocabulary_for_context("casual_chat")
# Returns: [("ngl", 0.85), ("tbh", 0.72), ...]
```

### 2. Dimension Associator

Learns which personality dimensions tend to activate together.

**Example:**
```
When you need emotional support, you prefer brief responses
    → Penny learns: emotional_support + brief_responses (0.72 coactivation)

When discussing technical topics, you want detailed explanations
    → Penny learns: technical_depth + detailed_responses (0.68 coactivation)
```

**Query predictions:**
```python
# Predict other dimensions from one
predictions = manager.get_dimension_predictions_for(
    "emotional_support_style",
    value=0.8
)
# Returns: {"response_length_preference": 0.3, ...}
```

### 3. Sequence Learner

Learns conversation flow patterns.

**Example:**
```
Pattern: problem_statement → clarification → solution → positive_feedback
    → Penny recognizes this sequence and anticipates next states
```

**12 Conversation States:**
- `greeting` - Session start
- `problem_statement` - You describe an issue
- `clarification_question` - Penny asks for details
- `information_gathering` - Exchanging context
- `positive_feedback` - You express satisfaction
- `negative_feedback` - You express dissatisfaction
- `solution_provided` - Penny offers a fix
- `off_topic` - Casual tangent
- `deep_discussion` - Extended technical talk
- `emotional_support` - Empathetic exchange
- `quick_query` - Brief question/answer
- `farewell` - Session end

**Query predictions:**
```python
states = manager.get_likely_next_states("problem_statement")
# Returns: [("clarification_question", 0.45), ("solution_provided", 0.30), ...]
```

---

## Safety Systems

### Learning Quarantine

New patterns don't immediately affect behavior. They must prove themselves:

| Requirement | Value | Why |
|-------------|-------|-----|
| Min observations | 5 | Pattern must recur |
| Min days span | 7 | Not just one session |
| Min unique days | 3 | Consistent over time |
| Expiration | 30 days | Remove stale patterns |

**Check quarantine status:**
```python
report = manager.get_learning_report()
print(f"In staging: {report['staging_count']}")
print(f"Promoted: {report['permanent_count']}")
print(f"Recent promotions: {report['recent_promotions']}")
```

### Turn Budget

Each conversation turn has limits to prevent runaway learning:

| Limit | Value | Purpose |
|-------|-------|---------|
| Max writes | 5 | Prevent DB overload |
| Max lookups | 20 | Limit cache access |
| Max queries | 10 | Limit DB reads |
| Max time | 15s | Prevent hangs |

### Learning Safety Checks

Learning is skipped when:
- Judgment system flagged the message (vague, contradictory)
- Confidence is below 0.7
- Message is too short (< 5 chars)

---

## Configuration

### Full penny_config.json Options

```json
{
    "hebbian": {
        "enabled": false,
        "db_path": "data/hebbian_learning.db",

        "quarantine": {
            "min_observations": 5,
            "min_days_span": 7,
            "min_unique_days": 3,
            "expiration_days": 30
        },

        "turn_budget": {
            "max_time_ms": 15000,
            "max_writes": 5,
            "max_lookups": 20,
            "max_queries": 10
        },

        "observability": {
            "drift_threshold_staging_count": 100,
            "drift_threshold_promotion_rate": 0.1,
            "drift_threshold_old_pattern_days": 60,
            "log_learning_events": true
        },

        "learning_safety": {
            "min_confidence": 0.7,
            "min_message_length": 5,
            "skip_if_judgment_issues": true
        },

        "caching": {
            "enabled": true,
            "size": 100,
            "refresh_interval": 50
        }
    }
}
```

### Tuning Tips

**More aggressive learning:**
```json
"quarantine": {
    "min_observations": 3,
    "min_days_span": 3,
    "min_unique_days": 2
}
```

**More conservative learning:**
```json
"quarantine": {
    "min_observations": 10,
    "min_days_span": 14,
    "min_unique_days": 7
}
```

---

## Monitoring & Observability

### Health Check

```python
health = manager.get_health_summary()
print(f"Status: {health['status']}")
print(f"Components: {health['components']}")
print(f"Issues: {health['issues']}")
```

### System Stats

```python
stats = manager.get_system_stats()
print(f"Vocab associations: {stats['vocab']['total_associations']}")
print(f"Dimension coactivations: {stats['dimensions']['total_coactivations']}")
print(f"State transitions: {stats['sequences']['total_transitions']}")
print(f"Avg latency: {stats['performance']['avg_latency_ms']:.2f}ms")
```

### Drift Detection

The system warns when:
- Staging count > 100 (patterns accumulating)
- Promotion rate < 10% (patterns not qualifying)
- Patterns older than 60 days (stuck in staging)

```python
report = manager.get_learning_report()
for warning in report.get('warnings', []):
    print(f"Warning: {warning}")
```

### Export Data

```python
# Export all learning data
data = manager.export_all_data()

# Export learning log for analysis
log = manager.export_learning_log()
```

---

## Maintenance

### Apply Temporal Decay

Old, unused patterns naturally decay:

```python
# Apply decay for patterns unused in last 7 days
results = manager.apply_temporal_decay_all(days_inactive=7.0)
print(f"Vocab decayed: {results['vocab_associations']}")
print(f"Transitions decayed: {results['transitions']}")
```

### Prune Weak Patterns

Remove patterns that never got strong:

```python
results = manager.prune_all(min_strength=0.1, min_observations=2)
print(f"Removed: {results['vocab_associations']} weak vocab associations")
```

### Reset Session State

Clear current session (not learned data):

```python
manager.reset_session()
```

---

## Integration with Other Systems

### Works with Judgment (Week 8.5)

Hebbian learning respects the judgment system:

```
User: "Fix that thing"
    → Judgment flags as vague
    → Hebbian skips learning (no vague data)
    → Penny asks for clarification
```

### Works with Personality Post-Processor

Learned patterns inform personality adjustments:

```python
# Get predictions based on current state
predictions = manager.get_dimension_predictions_for(
    "emotional_support_style",
    value=current_emotional_state
)

# Use predictions to adjust other dimensions
for dim, predicted_value in predictions.items():
    personality_state[dim] = blend(personality_state[dim], predicted_value)
```

---

## Troubleshooting

### "No patterns being promoted"

**Check:** Is the system getting enough varied data?
```python
report = manager.get_learning_report()
print(f"Staging: {report['staging_count']}")
print(f"Avg observations per pattern: ...")
```

**Solution:** Lower promotion thresholds or wait for more data.

### "Learning seems slow"

**Check:** Is caching enabled?
```python
stats = manager.get_system_stats()
print(f"Cache enabled: {manager.enable_caching}")
print(f"Avg latency: {stats['performance']['avg_latency_ms']}ms")
```

**Solution:** Enable caching, increase cache size.

### "Patterns not matching expectations"

**Check:** Export and review learned data:
```python
data = manager.export_all_data()
for assoc in data['vocab_associations'][:10]:
    print(f"{assoc['term']} -> {assoc['context']}: {assoc['strength']:.2f}")
```

**Solution:** Use vocab_overrides table to correct specific associations.

---

## API Reference

### HebbianLearningManager

**Constructor:**
```python
HebbianLearningManager(
    db_path: str,
    enable_caching: bool = True,
    cache_size: int = 100,
    cache_refresh_interval: int = 50
)
```

**Main Methods:**
| Method | Description |
|--------|-------------|
| `process_conversation_turn(...)` | Main entry point for learning |
| `should_use_term(term, context)` | Check if term fits context |
| `get_vocabulary_for_context(context)` | Get terms for context |
| `get_dimension_predictions_for(dim, value)` | Predict other dimensions |
| `get_likely_next_states(state)` | Predict next conversation states |
| `get_learning_report()` | Get quarantine/promotion stats |
| `get_health_summary()` | Get system health |
| `get_system_stats()` | Get detailed statistics |
| `export_all_data()` | Export all learned patterns |
| `apply_temporal_decay_all(days)` | Apply decay to old patterns |
| `prune_all(min_strength, min_obs)` | Remove weak patterns |
| `reset_session()` | Clear session state |

### TurnBudget

**Constructor:**
```python
TurnBudget(
    max_turn_time_ms: int = 15000,
    max_learning_writes: int = 5,
    max_cache_lookups: int = 20,
    max_db_queries: int = 10
)
```

**Methods:**
| Method | Description |
|--------|-------------|
| `start_turn()` | Begin a new turn |
| `can_write()` | Check if writes available |
| `can_lookup()` | Check if lookups available |
| `can_query()` | Check if queries available |
| `is_time_exceeded()` | Check if time limit hit |
| `record_write()` | Record a write operation |
| `record_lookup()` | Record a lookup |
| `record_query()` | Record a query |
| `get_summary()` | Get budget usage summary |

---

## Further Reading

- [WEEK10_DAY9_COMPLETE.md](../../WEEK10_DAY9_COMPLETE.md) - Day 9 safety implementation
- [WEEK10_COMPLETE.md](../../WEEK10_COMPLETE.md) - Week 10 summary
- [NEXT_PHASE_TASKS.md](../../NEXT_PHASE_TASKS.md) - Project roadmap

---

**Questions?** Ask CJ or check the test files in `tests/test_hebbian_*.py` for usage examples.
