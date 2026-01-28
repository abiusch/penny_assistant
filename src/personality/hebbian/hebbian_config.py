"""
Hebbian Learning Configuration
Centralized configuration for all Hebbian components
"""

from typing import Dict, Any, Optional
import os
import sqlite3
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

HEBBIAN_DEFAULT_CONFIG: Dict[str, Dict[str, Any]] = {
    # Vocabulary Associator
    'vocab': {
        'learning_rate': 0.05,
        'competitive_rate': 0.01,
        'decay_rate_per_day': 0.001,
        'confidence_threshold': 0.65,
        'max_association_strength': 1.0,
        'min_association_strength': 0.0,
        'default_strength': 0.5
    },

    # Dimension Associator
    'dimensions': {
        'learning_rate': 0.05,
        'activation_threshold': 0.6,
        'prediction_threshold': 0.65,
        'multi_dim_min_size': 3
    },

    # Sequence Learner
    'sequences': {
        'pattern_threshold': 5,
        'prediction_confidence': 0.7,
        'max_history_length': 10
    },

    # Performance
    'performance': {
        'enable_caching': True,
        'cache_size': 200,
        'cache_refresh_interval': 100,
        'batch_size': 10
    },

    # Safety
    'safety': {
        'max_decay_iterations': 100,
        'strength_cap': 1.0,
        'strength_floor': 0.0
    }
}


class HebbianConfig:
    """Configuration manager for Hebbian learning"""

    def __init__(self, db_path: str = "data/personality_tracking.db"):
        """
        Initialize configuration manager

        Args:
            db_path: Path to database (for loading config)
        """
        self.db_path = db_path
        self.config = self._deep_copy(HEBBIAN_DEFAULT_CONFIG)

        # Load from database if available
        self._load_from_db()

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _deep_copy(self, config: Dict) -> Dict:
        """Create a deep copy of config dict"""
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy(value)
            else:
                result[key] = value
        return result

    def get(self, component: str, parameter: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            component: Component name (vocab, dimensions, sequences, etc.)
            parameter: Parameter name
            default: Default value if not found

        Returns:
            Configuration value
        """
        try:
            return self.config[component][parameter]
        except KeyError:
            return default

    def set(self, component: str, parameter: str, value: Any) -> None:
        """
        Set configuration value

        Args:
            component: Component name
            parameter: Parameter name
            value: New value
        """
        if component not in self.config:
            self.config[component] = {}
        self.config[component][parameter] = value

        # Persist to database
        self._save_to_db(component, parameter, value)

    def _load_from_db(self) -> None:
        """Load configuration from database"""
        if not os.path.exists(self.db_path):
            logger.debug(f"Database not found at {self.db_path}, using defaults")
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT component, parameter, value
                    FROM hebbian_config
                """)
                for component, parameter, value in cursor.fetchall():
                    if component not in self.config:
                        self.config[component] = {}
                    # Convert boolean values
                    if value in (0, 1) and parameter.startswith('enable'):
                        value = bool(value)
                    self.config[component][parameter] = value
        except sqlite3.Error as e:
            logger.warning(f"Could not load Hebbian config from DB: {e}")

    def _save_to_db(self, component: str, parameter: str, value: Any) -> None:
        """Save a single config value to database"""
        if not os.path.exists(self.db_path):
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Convert boolean to int for SQLite
                if isinstance(value, bool):
                    value = int(value)
                cursor.execute("""
                    INSERT OR REPLACE INTO hebbian_config
                    (component, parameter, value, last_updated)
                    VALUES (?, ?, ?, datetime('now'))
                """, (component, parameter, value))
                conn.commit()
        except sqlite3.Error as e:
            logger.warning(f"Could not save Hebbian config to DB: {e}")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        env_mappings = {
            'HEBBIAN_VOCAB_LEARNING_RATE': ('vocab', 'learning_rate', float),
            'HEBBIAN_VOCAB_COMPETITIVE_RATE': ('vocab', 'competitive_rate', float),
            'HEBBIAN_VOCAB_DECAY_RATE': ('vocab', 'decay_rate_per_day', float),
            'HEBBIAN_VOCAB_THRESHOLD': ('vocab', 'confidence_threshold', float),
            'HEBBIAN_DIM_LEARNING_RATE': ('dimensions', 'learning_rate', float),
            'HEBBIAN_DIM_ACTIVATION_THRESHOLD': ('dimensions', 'activation_threshold', float),
            'HEBBIAN_SEQ_PATTERN_THRESHOLD': ('sequences', 'pattern_threshold', int),
            'HEBBIAN_ENABLE_CACHING': ('performance', 'enable_caching', lambda x: x.lower() == 'true'),
            'HEBBIAN_CACHE_SIZE': ('performance', 'cache_size', int),
        }

        for env_var, (component, parameter, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    self.config[component][parameter] = converter(value)
                    logger.info(f"Hebbian config override: {component}.{parameter} = {value}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid env var {env_var}={value}: {e}")

    def save_all_to_db(self) -> None:
        """Save all configuration to database"""
        for component, params in self.config.items():
            for parameter, value in params.items():
                self._save_to_db(component, parameter, value)

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return config as dictionary"""
        return self._deep_copy(self.config)


# Global config instance (lazy initialization)
_global_config: Optional[HebbianConfig] = None


def get_config(db_path: str = "data/personality_tracking.db") -> HebbianConfig:
    """Get or create global config instance"""
    global _global_config
    if _global_config is None:
        _global_config = HebbianConfig(db_path)
    return _global_config
