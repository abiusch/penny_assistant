#!/usr/bin/env python3
"""
Integrated Configuration System
Combines ChatGPT's cached config loading with personality system configuration
"""

import json
import os
import time
import threading
from typing import Dict, Any, Optional
from functools import lru_cache

# Thread-safe config state
_lock = threading.Lock()
_STATE = {"path": None, "mtime": 0, "cfg": {}}

def default_config_path() -> str:
    """Get default config path with environment variable override."""
    return os.environ.get("PENNY_CONFIG", "penny_config.json")

def _load_from_file(path: str) -> Dict[str, Any]:
    """Load configuration from file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_base_config() -> Dict[str, Any]:
    """
    Cached config loader with mtime refresh.
    Environment variable PENNY_CONFIG may override path.
    """
    path = default_config_path()
    mtime = os.path.getmtime(path) if os.path.exists(path) else 0
    
    with _lock:
        if _STATE["path"] != path or _STATE["mtime"] != mtime:
            _STATE["cfg"] = _load_from_file(path) if mtime else {}
            _STATE["path"] = path
            _STATE["mtime"] = mtime
    
    return _STATE["cfg"]

def load_integrated_config() -> Dict[str, Any]:
    """
    Enhanced config loader for complete personality system.
    Adds defaults for all personality subsystems.
    """
    base_config = load_base_config()
    
    # Ensure personality configuration exists with sensible defaults
    personality_config = base_config.setdefault('personality', {})
    
    # ML Personality Core defaults
    personality_config.setdefault('ml_learning_enabled', True)
    personality_config.setdefault('adaptation_rate', 0.1)
    personality_config.setdefault('learning_confidence_threshold', 0.5)
    personality_config.setdefault('max_learning_history', 1000)
    
    # Dynamic States defaults
    personality_config.setdefault('dynamic_states_enabled', True)
    personality_config.setdefault('state_transition_probability', 0.8)
    personality_config.setdefault('natural_state_duration_minutes', 30)
    personality_config.setdefault('context_override_enabled', True)
    
    # Performance monitoring defaults
    performance_config = base_config.setdefault('performance', {})
    performance_config.setdefault('monitoring_enabled', False)
    performance_config.setdefault('demo_mode', False)
    performance_config.setdefault('show_timing_metrics', False)
    performance_config.setdefault('lazy_loading_enabled', True)
    
    # Enhanced humor system defaults
    humor_config = personality_config.setdefault('humor', {})
    humor_config.setdefault('contextual_humor_enabled', True)
    humor_config.setdefault('relationship_callbacks_enabled', True)
    humor_config.setdefault('tech_industry_roasting_enabled', True)
    humor_config.setdefault('timing_based_humor_enabled', True)
    
    # Safety and fallback defaults
    safety_config = base_config.setdefault('safety', {})
    safety_config.setdefault('graceful_degradation_enabled', True)
    safety_config.setdefault('fallback_to_simple_personality', True)
    safety_config.setdefault('max_error_retries', 3)
    
    # Database configuration
    db_config = base_config.setdefault('database', {})
    db_config.setdefault('personality_db_path', 'data/penny_personality.db')
    db_config.setdefault('auto_create_db_dir', True)
    
    return base_config

def get_personality_config() -> Dict[str, Any]:
    """Get personality-specific configuration."""
    return load_integrated_config().get('personality', {})

def get_performance_config() -> Dict[str, Any]:
    """Get performance monitoring configuration."""
    return load_integrated_config().get('performance', {})

def is_demo_mode() -> bool:
    """Check if system is in demo mode (optimized for speed, minimal logging)."""
    return get_performance_config().get('demo_mode', False)

def is_monitoring_enabled() -> bool:
    """Check if performance monitoring is enabled."""
    return get_performance_config().get('monitoring_enabled', False)

def reset_config_cache():
    """Force reload of configuration on next access."""
    with _lock:
        _STATE["mtime"] = 0

@lru_cache(maxsize=1)
def get_cached_ml_config() -> Dict[str, Any]:
    """Cached ML personality configuration for performance."""
    return get_personality_config()

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration has required sections and sensible values.
    Returns True if valid, False otherwise.
    """
    try:
        # Check required top-level sections
        required_sections = ['personality', 'performance', 'database']
        for section in required_sections:
            if section not in config:
                print(f"Warning: Missing config section: {section}")
                return False
        
        # Validate personality config
        personality = config['personality']
        if not isinstance(personality.get('adaptation_rate'), (int, float)):
            print("Warning: adaptation_rate must be numeric")
            return False
        
        if not 0.0 <= personality.get('adaptation_rate', 0.1) <= 1.0:
            print("Warning: adaptation_rate must be between 0.0 and 1.0")
            return False
        
        # Validate database path
        db_path = config['database'].get('personality_db_path')
        if db_path and config['database'].get('auto_create_db_dir', True):
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        
        return True
        
    except Exception as e:
        print(f"Config validation error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Integrated Configuration System")
    print("=" * 45)
    
    # Test basic config loading
    config = load_integrated_config()
    print(f"Loaded config with {len(config)} top-level sections")
    
    # Test validation
    is_valid = validate_config(config)
    print(f"Config validation: {'PASSED' if is_valid else 'FAILED'}")
    
    # Test specific getters
    personality_config = get_personality_config()
    print(f"ML Learning enabled: {personality_config['ml_learning_enabled']}")
    print(f"Dynamic states enabled: {personality_config['dynamic_states_enabled']}")
    print(f"Demo mode: {is_demo_mode()}")
    print(f"Monitoring enabled: {is_monitoring_enabled()}")
    
    # Test cache behavior
    print(f"Cached ML config adaptation rate: {get_cached_ml_config()['adaptation_rate']}")
    
    print("\\nIntegrated configuration system ready!")
