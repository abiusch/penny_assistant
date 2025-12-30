"""
User consent and preferences for emotional tracking.

Ensures users maintain control over how Penny remembers their emotions.
Privacy-first design: opt-in, transparent, reversible.

Week 8 Implementation
"""

import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ConsentManager:
    """
    Manages user consent and preferences for emotional tracking.
    
    Core Principles:
    - Opt-in by default (user must explicitly enable)
    - Transparent (user knows what's tracked and why)
    - Reversible (user can disable and delete data)
    - Granular (user can control specific features)
    
    This is about building trust. Users need to feel in control of what
    Penny remembers about their emotional state.
    
    Features:
    - Emotional tracking on/off
    - Proactive check-ins on/off
    - Manual data deletion
    - Export emotional data
    - Audit log of consent changes
    """
    
    def __init__(self, storage_path: str = "data/user_consent.json"):
        """
        Initialize consent manager.
        
        Args:
            storage_path: Where to store consent preferences
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Default preferences (conservative/privacy-first)
        self.preferences = {
            'emotional_tracking_enabled': False,  # Opt-in
            'proactive_checkins_enabled': False,  # Opt-in
            'intensity_threshold': 0.8,           # Only significant emotions
            'memory_window_days': 7,              # Default window
            'consent_given_at': None,             # When user opted in
            'last_modified_at': None              # Last preference change
        }
        
        # Audit log
        self.audit_log: list = []
        
        # Load existing preferences
        self._load_preferences()
        
        logger.info(
            f"ConsentManager initialized "
            f"(tracking={self.preferences['emotional_tracking_enabled']})"
        )
    
    def request_consent(self) -> bool:
        """
        Request user consent for emotional tracking.
        
        This should be called the first time emotional tracking is mentioned.
        Returns current consent status.
        
        Returns:
            True if consent already given, False if still needed
            
        Example:
            >>> if not consent_mgr.request_consent():
            ...     show_consent_dialog()
        """
        if self.preferences['emotional_tracking_enabled']:
            logger.info("Consent already given")
            return True
        
        logger.info("Consent required - emotional tracking disabled")
        return False
    
    def grant_consent(
        self,
        emotional_tracking: bool = True,
        proactive_checkins: bool = False
    ):
        """
        User grants consent for emotional tracking.
        
        Args:
            emotional_tracking: Enable emotion tracking
            proactive_checkins: Enable proactive check-ins
            
        Example:
            >>> # User clicks "Yes, track my emotions"
            >>> consent_mgr.grant_consent(
            ...     emotional_tracking=True,
            ...     proactive_checkins=True
            ... )
        """
        self.preferences['emotional_tracking_enabled'] = emotional_tracking
        self.preferences['proactive_checkins_enabled'] = proactive_checkins
        self.preferences['consent_given_at'] = datetime.now().isoformat()
        self.preferences['last_modified_at'] = datetime.now().isoformat()
        
        self._log_audit_event('consent_granted', {
            'emotional_tracking': emotional_tracking,
            'proactive_checkins': proactive_checkins
        })
        
        self._save_preferences()
        
        logger.info(
            f"Consent granted: tracking={emotional_tracking}, "
            f"checkins={proactive_checkins}"
        )
    
    def revoke_consent(self, delete_data: bool = False):
        """
        User revokes consent for emotional tracking.
        
        Args:
            delete_data: Whether to delete existing emotional data
            
        Example:
            >>> # User: "Stop tracking my emotions"
            >>> consent_mgr.revoke_consent(delete_data=True)
        """
        self.preferences['emotional_tracking_enabled'] = False
        self.preferences['proactive_checkins_enabled'] = False
        self.preferences['last_modified_at'] = datetime.now().isoformat()
        
        self._log_audit_event('consent_revoked', {
            'delete_data': delete_data
        })
        
        self._save_preferences()
        
        logger.warning(f"Consent revoked (delete_data={delete_data})")
    
    def is_tracking_enabled(self) -> bool:
        """Check if emotional tracking is enabled"""
        return self.preferences['emotional_tracking_enabled']
    
    def is_checkins_enabled(self) -> bool:
        """Check if proactive check-ins are enabled"""
        return self.preferences['proactive_checkins_enabled']
    
    def get_intensity_threshold(self) -> float:
        """Get current intensity threshold for tracking"""
        return self.preferences['intensity_threshold']
    
    def get_memory_window(self) -> int:
        """Get current memory window in days"""
        return self.preferences['memory_window_days']
    
    def update_preferences(
        self,
        intensity_threshold: Optional[float] = None,
        memory_window_days: Optional[int] = None,
        proactive_checkins: Optional[bool] = None
    ):
        """
        Update specific preferences without changing consent.
        
        Args:
            intensity_threshold: New threshold (0.0-1.0)
            memory_window_days: New window (1-30 days)
            proactive_checkins: Enable/disable check-ins
            
        Example:
            >>> # User: "Only track very strong emotions"
            >>> consent_mgr.update_preferences(intensity_threshold=0.9)
            
            >>> # User: "Remember emotions for 2 weeks"
            >>> consent_mgr.update_preferences(memory_window_days=14)
        """
        changes = {}
        
        if intensity_threshold is not None:
            # Clamp to valid range
            intensity_threshold = max(0.0, min(1.0, intensity_threshold))
            self.preferences['intensity_threshold'] = intensity_threshold
            changes['intensity_threshold'] = intensity_threshold
        
        if memory_window_days is not None:
            # Clamp to reasonable range (1-30 days)
            memory_window_days = max(1, min(30, memory_window_days))
            self.preferences['memory_window_days'] = memory_window_days
            changes['memory_window_days'] = memory_window_days
        
        if proactive_checkins is not None:
            self.preferences['proactive_checkins_enabled'] = proactive_checkins
            changes['proactive_checkins'] = proactive_checkins
        
        if changes:
            self.preferences['last_modified_at'] = datetime.now().isoformat()
            self._log_audit_event('preferences_updated', changes)
            self._save_preferences()
            
            logger.info(f"Preferences updated: {changes}")
    
    def get_preferences(self) -> dict:
        """Get all current preferences"""
        return self.preferences.copy()
    
    def get_audit_log(self) -> list:
        """
        Get audit log of all consent changes.
        
        Useful for transparency: "Show me when and how my settings changed"
        
        Returns:
            List of audit events with timestamps
        """
        return self.audit_log.copy()
    
    def _log_audit_event(self, event_type: str, details: dict):
        """Log a consent/preference change"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        self.audit_log.append(event)
        
        # Keep last 100 events only
        if len(self.audit_log) > 100:
            self.audit_log = self.audit_log[-100:]
    
    def _save_preferences(self):
        """Save preferences to disk"""
        try:
            data = {
                'preferences': self.preferences,
                'audit_log': self.audit_log
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Saved preferences to {self.storage_path}")
        
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
    
    def _load_preferences(self):
        """Load preferences from disk"""
        if not self.storage_path.exists():
            logger.debug("No existing preferences found, using defaults")
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.preferences.update(data.get('preferences', {}))
            self.audit_log = data.get('audit_log', [])
            
            logger.info("Loaded existing preferences")
        
        except Exception as e:
            logger.error(f"Failed to load preferences: {e}")
    
    def export_consent_record(self) -> dict:
        """
        Export complete consent record for user.
        
        GDPR Article 20: Right to data portability.
        User can request their consent history.
        
        Returns:
            Complete record of all consent decisions
        """
        return {
            'preferences': self.preferences,
            'audit_log': self.audit_log,
            'exported_at': datetime.now().isoformat()
        }


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    consent_mgr = ConsentManager(storage_path="data/test_consent.json")
    
    print("\n🔒 Consent Manager Demo:")
    print("=" * 60)
    
    # Check initial consent
    print("\n1. Initial state:")
    print(f"   Tracking enabled: {consent_mgr.is_tracking_enabled()}")
    print(f"   Check-ins enabled: {consent_mgr.is_checkins_enabled()}")
    
    # User grants consent
    print("\n2. User grants consent:")
    consent_mgr.grant_consent(
        emotional_tracking=True,
        proactive_checkins=True
    )
    print(f"   Tracking enabled: {consent_mgr.is_tracking_enabled()}")
    
    # User adjusts preferences
    print("\n3. User adjusts preferences:")
    consent_mgr.update_preferences(
        intensity_threshold=0.9,
        memory_window_days=14
    )
    prefs = consent_mgr.get_preferences()
    print(f"   Threshold: {prefs['intensity_threshold']}")
    print(f"   Window: {prefs['memory_window_days']} days")
    
    # Show audit log
    print("\n4. Audit log:")
    for event in consent_mgr.get_audit_log():
        print(f"   [{event['timestamp']}] {event['event_type']}")
    
    # User revokes consent
    print("\n5. User revokes consent:")
    consent_mgr.revoke_consent(delete_data=True)
    print(f"   Tracking enabled: {consent_mgr.is_tracking_enabled()}")
