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
from contextlib import contextmanager
from functools import wraps
import threading
import os
from src.memory.storage_io import atomic_write

logger = logging.getLogger(__name__)
EMOTIONAL_FIELDS = frozenset({'emotion', 'emotion_confidence', 'sentiment', 'sentiment_score'})
_locks = {}
_locks_guard = threading.Lock()


class _StoreLock:
    """Reentrant thread lock plus an OS-released advisory process lock."""
    def __init__(self):
        self.thread = threading.RLock()
        self.depth = threading.local()

    @contextmanager
    def hold(self, path):
        with self.thread:
            depth = getattr(self.depth, 'value', 0)
            if depth:
                self.depth.value = depth + 1
                try:
                    yield
                finally:
                    self.depth.value = depth
                return
            # A stable sidecar is necessary: locking the JSON inode would stop
            # protecting it when an atomic preference update replaces the file.
            with open(path.with_name('.' + path.name + '.lock'), 'a+b') as lock_file:
                if os.name == 'nt':
                    import msvcrt
                    lock_file.seek(0, os.SEEK_END)
                    if lock_file.tell() == 0:
                        lock_file.write(b'0')
                        lock_file.flush()
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_file, fcntl.LOCK_EX)
                self.depth.value = 1
                try:
                    yield
                finally:
                    self.depth.value = 0
                    if os.name == 'nt':
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(lock_file, fcntl.LOCK_UN)


def without_emotion(metadata):
    """Remove derived tracking fields; retain words and unrelated metadata."""
    return {key: value for key, value in (metadata or {}).items() if key not in EMOTIONAL_FIELDS}


def serialized(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.guard():
            return method(self, *args, **kwargs)
    return call


def consent_guarded(method):
    """Use one fresh consent snapshot throughout a storage operation."""
    @wraps(method)
    def call(self, *args, **kwargs):
        if self.consent_manager is None:
            return method(self, *args, **kwargs)
        with self.consent_manager.guard():
            return method(self, *args, **kwargs)
    return call


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
        self.storage_path = Path(storage_path).resolve()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with _locks_guard:
            self._lock = _locks.setdefault(str(self.storage_path), _StoreLock())
        self._delete_handler = None
        self._write_failed = False
        self._guard_depth = threading.local()
        
        # Default preferences (conservative/privacy-first)
        self.preferences = {
            'emotional_tracking_enabled': False,  # Opt-in
            'proactive_checkins_enabled': False,  # Opt-in
            'intensity_threshold': 0.8,           # Only significant emotions
            'memory_window_days': 7,              # Default window
            'consent_given_at': None,             # When user opted in
            'last_modified_at': None,             # Last preference change
            'emotional_deletion_pending': False,
            'emotional_data_deleted_before': None,
        }
        self._defaults = self.preferences.copy()
        
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
        if self.is_tracking_enabled():
            logger.info("Consent already given")
            return True
        
        logger.info("Consent required - emotional tracking disabled")
        return False
    
    @serialized
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
        if self.preferences['emotional_deletion_pending']:
            raise RuntimeError('Emotional deletion is pending; complete deletion before opting in again')
        self.preferences['emotional_tracking_enabled'] = emotional_tracking is True
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
    
    @serialized
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
        if delete_data:
            self.preferences['emotional_deletion_pending'] = True
            self.preferences['emotional_data_deleted_before'] = datetime.now().isoformat()
        
        self._log_audit_event('consent_revoked', {
            'delete_data': delete_data
        })
        
        self._save_preferences()
        if delete_data:
            self.resume_pending_deletion()
        
        logger.warning(f"Consent revoked (delete_data={delete_data})")
    
    @serialized
    def is_tracking_enabled(self) -> bool:
        """Check if emotional tracking is enabled"""
        return (self.preferences['emotional_tracking_enabled'] is True
                and not self.preferences['emotional_deletion_pending'] and not self._write_failed)
    
    @serialized
    def is_checkins_enabled(self) -> bool:
        """Check if proactive check-ins are enabled"""
        return self.is_tracking_enabled() and self.preferences['proactive_checkins_enabled'] is True
    
    @serialized
    def get_intensity_threshold(self) -> float:
        """Get current intensity threshold for tracking"""
        return self.preferences['intensity_threshold']
    
    @serialized
    def get_memory_window(self) -> int:
        """Get current memory window in days"""
        return self.preferences['memory_window_days']
    
    @serialized
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
    
    @serialized
    def get_preferences(self) -> dict:
        """Get all current preferences"""
        return self.preferences.copy()
    
    @serialized
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
    
    @contextmanager
    def guard(self):
        """Serialize consent changes and guarded writes across runtime instances.

        Read the durable setting at each boundary so older instances observe it.
        Other writers must participate in this lock. It does not solve the vector
        store's independent problem of merging stale conversation snapshots.
        """
        with self._lock.hold(self.storage_path):
            depth = getattr(self._guard_depth, 'value', 0)
            if depth == 0:
                self._load_preferences()
            self._guard_depth.value = depth + 1
            try:
                yield
            finally:
                self._guard_depth.value = depth

    def set_delete_handler(self, handler):
        self._delete_handler = handler

    @serialized
    def resume_pending_deletion(self):
        if not self.preferences['emotional_deletion_pending']:
            return
        if self._delete_handler is None:
            raise RuntimeError('Emotional deletion requires a connected storage handler')
        self._delete_handler()
        self.preferences['emotional_deletion_pending'] = False
        self._log_audit_event('emotional_data_deleted', {})
        self._save_preferences()

    @serialized
    def was_deleted(self, timestamp):
        cutoff = self.preferences['emotional_data_deleted_before']
        if not cutoff:
            return False
        try:
            return not timestamp or datetime.fromisoformat(timestamp) <= datetime.fromisoformat(cutoff)
        except (TypeError, ValueError):
            return True  # Unknown dates cannot resurrect pre-deletion metadata.

    def filter_context(self, metadata):
        return dict(metadata or {}) if self.is_tracking_enabled() else without_emotion(metadata)

    def filter_record(self, record, *, reading=False):
        if self.was_deleted(record.get('timestamp')) or (reading and not self.is_tracking_enabled()):
            record = without_emotion(record)
            record['context'] = without_emotion(record.get('context'))
        return record

    def filter_threads(self, threads, *, reading=False):
        if reading and not self.is_tracking_enabled():
            return []
        return [thread for thread in threads if not self.was_deleted(thread.get('timestamp'))]

    def _save_preferences(self):
        """Save preferences to disk"""
        try:
            data = {
                'preferences': self.preferences,
                'audit_log': self.audit_log
            }
            
            atomic_write(self.storage_path, json.dumps(data, indent=2).encode('utf-8'))
            self._write_failed = False
            
            logger.debug(f"Saved preferences to {self.storage_path}")
        
        except Exception as e:
            self._write_failed = True
            raise RuntimeError('Failed to save consent preferences; change is not confirmed') from e
    
    def _load_preferences(self):
        """Load preferences from disk"""
        if not self.storage_path.exists():
            logger.debug("No existing preferences found, using defaults")
            self.preferences = self._defaults.copy()
            self.audit_log = []
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            preferences = data.get('preferences', {})
            if not isinstance(preferences, dict) or not isinstance(data.get('audit_log', []), list):
                raise ValueError('Invalid consent record')
            self.preferences = {**self._defaults, **preferences}
            self.audit_log = data.get('audit_log', [])
            
            logger.info("Loaded existing preferences")
        
        except Exception as e:
            self.preferences = self._defaults.copy()
            raise RuntimeError('Cannot read consent preferences; tracking is disabled') from e
    
    @serialized
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
