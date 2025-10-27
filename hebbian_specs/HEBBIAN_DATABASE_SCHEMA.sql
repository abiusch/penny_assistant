-- ============================================================================
-- HEBBIAN LEARNING LAYER - DATABASE SCHEMA
-- ============================================================================
-- Date: October 27, 2025
-- Status: Design Specification
-- Database: personality_tracking.db (extends existing schema)
--
-- This schema adds Hebbian learning tables to the existing personality
-- tracking database. All new tables are prefixed with appropriate namespaces
-- to avoid conflicts.
-- ============================================================================

-- ============================================================================
-- 1. VOCABULARY ASSOCIATION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- vocab_associations: Core association matrix (term × context → strength)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vocab_associations (
    term TEXT NOT NULL,
    context_type TEXT NOT NULL,
    strength REAL DEFAULT 0.5 CHECK (strength >= 0.0 AND strength <= 1.0),
    observation_count INTEGER DEFAULT 1,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (term, context_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_vocab_term ON vocab_associations(term);
CREATE INDEX IF NOT EXISTS idx_vocab_context ON vocab_associations(context_type);
CREATE INDEX IF NOT EXISTS idx_vocab_strength ON vocab_associations(strength DESC);
CREATE INDEX IF NOT EXISTS idx_vocab_last_updated ON vocab_associations(last_updated);

-- ----------------------------------------------------------------------------
-- vocab_context_observations: Historical log of vocabulary observations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vocab_context_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    context_type TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_message TEXT,
    session_id TEXT,
    FOREIGN KEY (term, context_type) REFERENCES vocab_associations(term, context_type)
);

-- Index for querying observation history
CREATE INDEX IF NOT EXISTS idx_vocab_obs_timestamp ON vocab_context_observations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_vocab_obs_term ON vocab_context_observations(term);

-- ----------------------------------------------------------------------------
-- vocab_overrides: Manual overrides for problematic associations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vocab_overrides (
    term TEXT NOT NULL,
    context_type TEXT NOT NULL,
    override_strength REAL NOT NULL CHECK (override_strength >= 0.0 AND override_strength <= 1.0),
    reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'user',
    PRIMARY KEY (term, context_type)
);

-- ============================================================================
-- 2. DIMENSION CO-ACTIVATION TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- dimension_coactivations: Pairwise co-activation matrix
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dimension_coactivations (
    dim1 TEXT NOT NULL,
    dim2 TEXT NOT NULL,
    strength REAL DEFAULT 0.0 CHECK (strength >= 0.0 AND strength <= 1.0),
    observation_count INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dim1, dim2),
    CHECK (dim1 < dim2)  -- Ensure (A,B) not (B,A) to avoid duplicates
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_coact_dim1 ON dimension_coactivations(dim1);
CREATE INDEX IF NOT EXISTS idx_coact_dim2 ON dimension_coactivations(dim2);
CREATE INDEX IF NOT EXISTS idx_coact_strength ON dimension_coactivations(strength DESC);

-- ----------------------------------------------------------------------------
-- coactivation_observations: Historical log of dimension activations
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS coactivation_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    dimensions_json TEXT NOT NULL,  -- JSON: {"dim1": 0.8, "dim2": 0.9, ...}
    context_snapshot TEXT,          -- JSON: conversation context
    session_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_coact_obs_timestamp ON coactivation_observations(timestamp DESC);

-- ----------------------------------------------------------------------------
-- multi_dim_patterns: Patterns of 3+ dimensions activating together
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS multi_dim_patterns (
    pattern_id TEXT PRIMARY KEY,
    dimensions_json TEXT NOT NULL,  -- JSON: {"empathy": 0.85, "brief": 0.9, "simple": 0.8}
    frequency INTEGER DEFAULT 1,
    avg_satisfaction REAL DEFAULT 0.5,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pattern_frequency ON multi_dim_patterns(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_pattern_satisfaction ON multi_dim_patterns(avg_satisfaction DESC);

-- ----------------------------------------------------------------------------
-- negative_correlations: Anti-correlated dimension pairs
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS negative_correlations (
    dim_high TEXT NOT NULL,
    dim_low TEXT NOT NULL,
    correlation_strength REAL DEFAULT 0.0,  -- Negative correlation coefficient
    observation_count INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dim_high, dim_low)
);

-- ============================================================================
-- 3. CONVERSATION SEQUENCE TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- conversation_state_transitions: Markov chain transition matrix
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversation_state_transitions (
    state_from TEXT NOT NULL,
    state_to TEXT NOT NULL,
    transition_count INTEGER DEFAULT 1,
    transition_probability REAL DEFAULT 0.0 CHECK (transition_probability >= 0.0 AND transition_probability <= 1.0),
    last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
    first_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (state_from, state_to)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_transitions_from ON conversation_state_transitions(state_from);
CREATE INDEX IF NOT EXISTS idx_transitions_to ON conversation_state_transitions(state_to);
CREATE INDEX IF NOT EXISTS idx_transitions_count ON conversation_state_transitions(transition_count DESC);
CREATE INDEX IF NOT EXISTS idx_transitions_prob ON conversation_state_transitions(transition_probability DESC);

-- ----------------------------------------------------------------------------
-- state_sequences: Recurring sequences of conversation states
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS state_sequences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_json TEXT NOT NULL UNIQUE,  -- JSON: ["problem", "technical", "simple"]
    sequence_hash TEXT NOT NULL,         -- Hash for fast lookup
    frequency INTEGER DEFAULT 1,
    avg_satisfaction REAL DEFAULT 0.5,
    avg_user_rating REAL,
    last_observed DATETIME DEFAULT CURRENT_TIMESTAMP,
    first_observed DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sequence_frequency ON state_sequences(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_sequence_satisfaction ON state_sequences(avg_satisfaction DESC);
CREATE INDEX IF NOT EXISTS idx_sequence_hash ON state_sequences(sequence_hash);

-- ----------------------------------------------------------------------------
-- pattern_templates: Learned patterns with skip opportunities
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pattern_templates (
    pattern_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    sequence_json TEXT NOT NULL,           -- JSON: Full sequence
    skip_opportunities_json TEXT,          -- JSON: States that can be skipped
    frequency INTEGER DEFAULT 1,
    success_rate REAL DEFAULT 0.5,         -- How often pattern leads to satisfaction
    confidence REAL DEFAULT 0.5,
    last_applied DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_template_frequency ON pattern_templates(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_template_confidence ON pattern_templates(confidence DESC);

-- ----------------------------------------------------------------------------
-- state_classification_log: Log of state classifications for debugging
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS state_classification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_message TEXT NOT NULL,
    classified_state TEXT NOT NULL,
    confidence REAL,
    context_json TEXT,
    session_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_state_log_timestamp ON state_classification_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_state_log_state ON state_classification_log(classified_state);

-- ============================================================================
-- 4. CONFIGURATION & METADATA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- hebbian_config: Configuration parameters for Hebbian components
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hebbian_config (
    component TEXT NOT NULL,
    parameter TEXT NOT NULL,
    value REAL NOT NULL,
    description TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (component, parameter)
);

-- Initialize default configuration
INSERT OR IGNORE INTO hebbian_config (component, parameter, value, description) VALUES
    -- Vocabulary Associator
    ('vocab', 'learning_rate', 0.05, 'Rate of association strengthening'),
    ('vocab', 'competitive_rate', 0.01, 'Rate of competitive weakening'),
    ('vocab', 'decay_rate_per_day', 0.001, 'Daily decay for unused associations'),
    ('vocab', 'confidence_threshold', 0.65, 'Threshold for predictions'),
    ('vocab', 'default_strength', 0.5, 'Initial association strength'),

    -- Dimension Associator
    ('dimensions', 'learning_rate', 0.05, 'Rate of co-activation strengthening'),
    ('dimensions', 'activation_threshold', 0.6, 'Threshold for active dimension'),
    ('dimensions', 'prediction_threshold', 0.65, 'Threshold for predictions'),
    ('dimensions', 'multi_dim_min_size', 3, 'Min dimensions for multi-dim pattern'),

    -- Sequence Learner
    ('sequences', 'pattern_threshold', 5, 'Min frequency to create pattern'),
    ('sequences', 'prediction_confidence', 0.7, 'Min confidence to anticipate'),
    ('sequences', 'max_history_length', 10, 'Max conversation states to track'),

    -- Performance
    ('performance', 'enable_caching', 1, 'Enable LRU caching (0/1)'),
    ('performance', 'cache_size', 200, 'LRU cache size'),
    ('performance', 'cache_refresh_interval', 100, 'Conversations between cache refresh'),
    ('performance', 'batch_size', 10, 'Batch size for DB updates');

-- ----------------------------------------------------------------------------
-- hebbian_stats: System-level statistics
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hebbian_stats (
    stat_name TEXT PRIMARY KEY,
    stat_value REAL NOT NULL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Initialize statistics
INSERT OR IGNORE INTO hebbian_stats (stat_name, stat_value) VALUES
    ('total_vocab_associations', 0),
    ('total_coactivations', 0),
    ('total_state_transitions', 0),
    ('total_patterns_detected', 0),
    ('total_predictions_made', 0),
    ('total_predictions_correct', 0),
    ('last_decay_run', 0),
    ('last_cache_refresh', 0);

-- ----------------------------------------------------------------------------
-- hebbian_performance_log: Performance tracking
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hebbian_performance_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    component TEXT NOT NULL,
    operation TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_perf_timestamp ON hebbian_performance_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_perf_component ON hebbian_performance_log(component);

-- ============================================================================
-- 5. MIGRATION & COMPATIBILITY VIEWS
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: Recent vocabulary associations for debugging
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_recent_vocab_associations AS
SELECT
    term,
    context_type,
    strength,
    observation_count,
    last_updated,
    ROUND((julianday('now') - julianday(last_updated)), 1) AS days_since_update
FROM vocab_associations
WHERE last_updated >= datetime('now', '-30 days')
ORDER BY last_updated DESC;

-- ----------------------------------------------------------------------------
-- View: Top co-activations
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_top_coactivations AS
SELECT
    dim1,
    dim2,
    strength,
    observation_count,
    last_updated
FROM dimension_coactivations
WHERE strength > 0.5
ORDER BY strength DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- View: Most common state transitions
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_common_transitions AS
SELECT
    state_from,
    state_to,
    transition_count,
    transition_probability,
    last_observed
FROM conversation_state_transitions
ORDER BY transition_count DESC
LIMIT 20;

-- ----------------------------------------------------------------------------
-- View: System health summary
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_hebbian_health AS
SELECT
    (SELECT COUNT(*) FROM vocab_associations) AS vocab_associations_count,
    (SELECT COUNT(*) FROM vocab_associations WHERE strength > 0.65) AS strong_vocab_count,
    (SELECT COUNT(*) FROM dimension_coactivations) AS coactivations_count,
    (SELECT COUNT(*) FROM dimension_coactivations WHERE strength > 0.5) AS strong_coact_count,
    (SELECT COUNT(*) FROM conversation_state_transitions) AS transitions_count,
    (SELECT COUNT(*) FROM state_sequences WHERE frequency >= 5) AS recurring_sequences_count,
    (SELECT COUNT(*) FROM pattern_templates) AS pattern_templates_count,
    (SELECT AVG(latency_ms) FROM hebbian_performance_log WHERE timestamp >= datetime('now', '-1 hour')) AS avg_latency_last_hour;

-- ============================================================================
-- 6. TRIGGERS FOR DATA INTEGRITY
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Trigger: Update vocab_associations observation count
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS vocab_update_observation_count
AFTER INSERT ON vocab_context_observations
BEGIN
    UPDATE vocab_associations
    SET
        observation_count = observation_count + 1,
        last_updated = CURRENT_TIMESTAMP
    WHERE term = NEW.term AND context_type = NEW.context_type;
END;

-- ----------------------------------------------------------------------------
-- Trigger: Update coactivation observation count
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS coact_update_observation_count
AFTER INSERT ON coactivation_observations
BEGIN
    -- This would require complex JSON parsing, implement in Python instead
    -- Just update last_modified for any coactivation
    UPDATE dimension_coactivations
    SET last_updated = CURRENT_TIMESTAMP
    WHERE last_updated < CURRENT_TIMESTAMP;
END;

-- ----------------------------------------------------------------------------
-- Trigger: Prevent invalid association strengths
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS vocab_prevent_invalid_strength
BEFORE UPDATE OF strength ON vocab_associations
BEGIN
    SELECT CASE
        WHEN NEW.strength < 0.0 OR NEW.strength > 1.0
        THEN RAISE(ABORT, 'Association strength must be between 0.0 and 1.0')
    END;
END;

-- ----------------------------------------------------------------------------
-- Trigger: Prevent invalid co-activation strengths
-- ----------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS coact_prevent_invalid_strength
BEFORE UPDATE OF strength ON dimension_coactivations
BEGIN
    SELECT CASE
        WHEN NEW.strength < 0.0 OR NEW.strength > 1.0
        THEN RAISE(ABORT, 'Co-activation strength must be between 0.0 and 1.0')
    END;
END;

-- ============================================================================
-- 7. MIGRATION PLAN
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Migration: Add Hebbian tables to existing database
-- ----------------------------------------------------------------------------
-- This schema can be applied to an existing personality_tracking.db file.
-- All tables use IF NOT EXISTS, so it's safe to run multiple times.
--
-- Steps:
-- 1. Backup existing database: cp personality_tracking.db personality_tracking.db.backup
-- 2. Apply this schema: sqlite3 personality_tracking.db < HEBBIAN_DATABASE_SCHEMA.sql
-- 3. Verify tables exist: sqlite3 personality_tracking.db ".tables"
-- 4. Check health: sqlite3 personality_tracking.db "SELECT * FROM v_hebbian_health;"
--
-- Rollback:
-- If needed to remove Hebbian tables (for testing):
-- DROP TABLE IF EXISTS vocab_associations;
-- DROP TABLE IF EXISTS vocab_context_observations;
-- DROP TABLE IF EXISTS vocab_overrides;
-- DROP TABLE IF EXISTS dimension_coactivations;
-- DROP TABLE IF EXISTS coactivation_observations;
-- DROP TABLE IF EXISTS multi_dim_patterns;
-- DROP TABLE IF EXISTS negative_correlations;
-- DROP TABLE IF EXISTS conversation_state_transitions;
-- DROP TABLE IF EXISTS state_sequences;
-- DROP TABLE IF EXISTS pattern_templates;
-- DROP TABLE IF EXISTS state_classification_log;
-- DROP TABLE IF EXISTS hebbian_config;
-- DROP TABLE IF EXISTS hebbian_stats;
-- DROP TABLE IF EXISTS hebbian_performance_log;

-- ============================================================================
-- 8. UTILITY QUERIES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Query: Get association strength for a term-context pair
-- ----------------------------------------------------------------------------
-- SELECT strength FROM vocab_associations
-- WHERE term = 'ngl' AND context_type = 'casual_chat';

-- ----------------------------------------------------------------------------
-- Query: Get top contexts for a term
-- ----------------------------------------------------------------------------
-- SELECT context_type, strength, observation_count
-- FROM vocab_associations
-- WHERE term = 'ngl'
-- ORDER BY strength DESC
-- LIMIT 5;

-- ----------------------------------------------------------------------------
-- Query: Get strongest co-activations for a dimension
-- ----------------------------------------------------------------------------
-- SELECT dim2 AS other_dimension, strength, observation_count
-- FROM dimension_coactivations
-- WHERE dim1 = 'emotional_support_style'
-- ORDER BY strength DESC
-- LIMIT 5;

-- ----------------------------------------------------------------------------
-- Query: Get most common state transitions from a given state
-- ----------------------------------------------------------------------------
-- SELECT state_to, transition_count, transition_probability
-- FROM conversation_state_transitions
-- WHERE state_from = 'problem_statement'
-- ORDER BY transition_count DESC;

-- ----------------------------------------------------------------------------
-- Query: Get recurring conversation sequences
-- ----------------------------------------------------------------------------
-- SELECT sequence_json, frequency, avg_satisfaction
-- FROM state_sequences
-- WHERE frequency >= 5
-- ORDER BY frequency DESC;

-- ----------------------------------------------------------------------------
-- Query: Apply temporal decay (run daily)
-- ----------------------------------------------------------------------------
-- UPDATE vocab_associations
-- SET strength = strength * (1.0 - (
--     0.001 * (julianday('now') - julianday(last_updated))
-- ))
-- WHERE julianday('now') - julianday(last_updated) >= 1.0;

-- ----------------------------------------------------------------------------
-- Query: Prune weak associations
-- ----------------------------------------------------------------------------
-- DELETE FROM vocab_associations
-- WHERE strength < 0.1 AND observation_count < 2;

-- ============================================================================
-- 9. PERFORMANCE OPTIMIZATION NOTES
-- ============================================================================

-- All critical columns have indexes:
-- • vocab_associations: term, context_type, strength, last_updated
-- • dimension_coactivations: dim1, dim2, strength
-- • conversation_state_transitions: state_from, state_to, transition_count
-- • state_sequences: frequency, satisfaction, sequence_hash
--
-- Expected table sizes after 100 conversations:
-- • vocab_associations: ~500 rows (~50KB)
-- • dimension_coactivations: ~21 rows (7 dims → 7*6/2 = 21 pairs) (~2KB)
-- • conversation_state_transitions: ~50 rows (~5KB)
-- • state_sequences: ~20 rows (~5KB)
-- • Total Hebbian data: ~100KB per 100 conversations
--
-- Query performance targets:
-- • Get association strength: <1ms (indexed lookup)
-- • Get top contexts: <2ms (indexed sort)
-- • Get co-activations: <1ms (indexed lookup)
-- • Get transitions: <2ms (indexed sort)
-- • Batch updates: <10ms (transaction batching)

-- ============================================================================
-- 10. DATA VALIDATION QUERIES
-- ============================================================================

-- Check for invalid strengths
-- SELECT 'Invalid vocab strength' AS issue, term, context_type, strength
-- FROM vocab_associations
-- WHERE strength < 0.0 OR strength > 1.0
-- UNION ALL
-- SELECT 'Invalid coact strength', dim1, dim2, strength
-- FROM dimension_coactivations
-- WHERE strength < 0.0 OR strength > 1.0;

-- Check for orphaned observations
-- SELECT 'Orphaned vocab observation' AS issue, term, context_type
-- FROM vocab_context_observations vco
-- WHERE NOT EXISTS (
--     SELECT 1 FROM vocab_associations va
--     WHERE va.term = vco.term AND va.context_type = vco.context_type
-- );

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

-- Schema version: 1.0
-- Last updated: October 27, 2025
-- Compatible with: personality_tracking.db (Phase 2 schema)
-- Status: Ready for implementation
