"""
Personality snapshots for version control and rollback.

Allows saving personality state at intervals and rolling back if needed.
Think of it like Git for Penny's personality - you can always undo changes.

Week 8 Implementation
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PersonalitySnapshot:
    """
    A point-in-time snapshot of Penny's personality state.
    
    This captures everything about Penny's current personality:
    - Formality level
    - Sarcasm tendency
    - Technical depth
    - Learned phrases (when culture learning is added in Week 9)
    - Emotional threads
    
    Like a save game checkpoint - you can always restore to this point.
    """
    
    def __init__(
        self,
        version: int,
        timestamp: datetime,
        personality_state: dict,
        emotional_threads: List[dict],
        conversation_count: int
    ):
        """
        Create a personality snapshot.
        
        Args:
            version: Sequential version number (1, 2, 3, ...)
            timestamp: When this snapshot was created
            personality_state: Current personality parameters
            emotional_threads: Active emotional threads
            conversation_count: Total conversations at snapshot time
        """
        self.version = version
        self.timestamp = timestamp
        self.personality_state = personality_state
        self.emotional_threads = emotional_threads
        self.conversation_count = conversation_count
    
    def to_dict(self) -> dict:
        """Serialize for storage"""
        return {
            'version': self.version,
            'timestamp': self.timestamp.isoformat(),
            'personality_state': self.personality_state,
            'emotional_threads': self.emotional_threads,
            'conversation_count': self.conversation_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PersonalitySnapshot':
        """Deserialize from storage"""
        return cls(
            version=data['version'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            personality_state=data['personality_state'],
            emotional_threads=data['emotional_threads'],
            conversation_count=data['conversation_count']
        )
    
    def __repr__(self) -> str:
        return (
            f"PersonalitySnapshot(v{self.version}, "
            f"{self.conversation_count} conversations, "
            f"{len(self.emotional_threads)} threads)"
        )


class PersonalitySnapshotManager:
    """
    Manages personality snapshots for version control and rollback.
    
    Features:
    - Auto-snapshot every N conversations (default 50)
    - Manual snapshot on demand
    - Rollback to previous version
    - View version history
    
    Use Cases:
    - User: "Penny's acting weird, go back to how she was yesterday"
    - Developer: Experiment with personality changes, rollback if bad
    - Safety: Automatic backup before major personality shifts
    
    Example:
        manager = PersonalitySnapshotManager()
        
        # Auto-creates snapshot every 50 conversations
        if manager.should_snapshot(conversation_count):
            snapshot = manager.create_snapshot(...)
        
        # User wants to rollback
        old_snapshot = manager.rollback_to_version(5)
        restore_personality(old_snapshot.personality_state)
    """
    
    def __init__(
        self,
        storage_path: str = "data/personality_snapshots",
        snapshot_interval: int = 50
    ):
        """
        Initialize snapshot manager.
        
        Args:
            storage_path: Directory to store snapshots
            snapshot_interval: Create snapshot every N conversations
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.snapshot_interval = snapshot_interval
        self.snapshots: List[PersonalitySnapshot] = []
        
        # Load existing snapshots from disk
        self._load_snapshots()
        
        logger.info(
            f"PersonalitySnapshotManager initialized "
            f"({len(self.snapshots)} snapshots, interval={snapshot_interval})"
        )
    
    def should_snapshot(self, conversation_count: int) -> bool:
        """
        Check if it's time to create a new snapshot.
        
        Args:
            conversation_count: Current number of conversations
            
        Returns:
            True if snapshot should be created
            
        Logic:
        - Always snapshot if no snapshots exist
        - Otherwise, snapshot every N conversations
        
        Example:
            >>> manager = PersonalitySnapshotManager(snapshot_interval=50)
            >>> manager.should_snapshot(1)    # True (first snapshot)
            >>> manager.should_snapshot(25)   # False (too soon)
            >>> manager.should_snapshot(50)   # True (interval reached)
            >>> manager.should_snapshot(51)   # False (just did one)
            >>> manager.should_snapshot(100)  # True (another interval)
        """
        if not self.snapshots:
            return True
        
        last_snapshot_count = self.snapshots[-1].conversation_count
        return conversation_count - last_snapshot_count >= self.snapshot_interval
    
    def create_snapshot(
        self,
        personality_state: dict,
        emotional_threads: List[dict],
        conversation_count: int
    ) -> PersonalitySnapshot:
        """
        Create a new personality snapshot.
        
        Args:
            personality_state: Current personality parameters
            emotional_threads: Active emotional threads
            conversation_count: Total conversations so far
            
        Returns:
            Created snapshot
            
        Example:
            >>> snapshot = manager.create_snapshot(
            ...     personality_state={'formality': 0.3, 'sarcasm': 0.6},
            ...     emotional_threads=[...],
            ...     conversation_count=150
            ... )
            >>> print(snapshot)
            PersonalitySnapshot(v4, 150 conversations, 3 threads)
        """
        version = len(self.snapshots) + 1
        
        snapshot = PersonalitySnapshot(
            version=version,
            timestamp=datetime.now(),
            personality_state=personality_state,
            emotional_threads=emotional_threads,
            conversation_count=conversation_count
        )
        
        self.snapshots.append(snapshot)
        self._save_snapshot(snapshot)
        
        logger.info(f"📸 Created personality snapshot v{version}")
        return snapshot
    
    def rollback_to_version(self, version: int) -> Optional[PersonalitySnapshot]:
        """
        Rollback personality to a previous version.
        
        Args:
            version: Version number to rollback to
            
        Returns:
            Snapshot for that version, or None if not found
            
        Example:
            >>> # User: "Go back to how you were yesterday"
            >>> snapshot = manager.rollback_to_version(5)
            >>> if snapshot:
            ...     restore_personality(snapshot.personality_state)
            ...     restore_threads(snapshot.emotional_threads)
        """
        for snapshot in self.snapshots:
            if snapshot.version == version:
                logger.info(f"↩️ Rolling back to personality v{version}")
                return snapshot
        
        logger.warning(f"Snapshot v{version} not found")
        return None
    
    def get_latest(self) -> Optional[PersonalitySnapshot]:
        """Get most recent snapshot"""
        return self.snapshots[-1] if self.snapshots else None
    
    def list_versions(self) -> List[dict]:
        """
        List all snapshot versions.
        
        Returns:
            List of dicts with version info
            
        Example:
            >>> versions = manager.list_versions()
            >>> for v in versions:
            ...     print(f"v{v['version']}: {v['conversation_count']} conversations")
            v1: 50 conversations
            v2: 100 conversations
            v3: 150 conversations
        """
        return [
            {
                'version': s.version,
                'timestamp': s.timestamp.isoformat(),
                'conversation_count': s.conversation_count,
                'thread_count': len(s.emotional_threads)
            }
            for s in self.snapshots
        ]
    
    def get_snapshot_at_time(self, timestamp: datetime) -> Optional[PersonalitySnapshot]:
        """
        Find snapshot closest to a given time.
        
        Useful for: "How was Penny acting last week?"
        
        Args:
            timestamp: Target time
            
        Returns:
            Closest snapshot before or at that time
        """
        candidates = [s for s in self.snapshots if s.timestamp <= timestamp]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.timestamp)
    
    def _save_snapshot(self, snapshot: PersonalitySnapshot):
        """Save snapshot to disk"""
        path = self.storage_path / f"snapshot_v{snapshot.version}.json"
        
        try:
            with open(path, 'w') as f:
                json.dump(snapshot.to_dict(), f, indent=2)
            logger.debug(f"Saved snapshot v{snapshot.version} to {path}")
        except Exception as e:
            logger.error(f"Failed to save snapshot v{snapshot.version}: {e}")
    
    def _load_snapshots(self):
        """Load all snapshots from disk"""
        if not self.storage_path.exists():
            logger.debug("No snapshot directory found, starting fresh")
            return
        
        snapshot_files = sorted(self.storage_path.glob("snapshot_v*.json"))
        
        for file in snapshot_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    snapshot = PersonalitySnapshot.from_dict(data)
                    self.snapshots.append(snapshot)
            except Exception as e:
                logger.error(f"Failed to load snapshot {file}: {e}")
        
        if self.snapshots:
            logger.info(f"Loaded {len(self.snapshots)} existing snapshots")
    
    def delete_snapshot(self, version: int) -> bool:
        """
        Delete a specific snapshot (use carefully).
        
        Args:
            version: Version number to delete
            
        Returns:
            True if deleted, False if not found
        """
        # Find snapshot
        snapshot = None
        for s in self.snapshots:
            if s.version == version:
                snapshot = s
                break
        
        if not snapshot:
            return False
        
        # Remove from list
        self.snapshots.remove(snapshot)
        
        # Delete file
        path = self.storage_path / f"snapshot_v{version}.json"
        if path.exists():
            path.unlink()
        
        logger.info(f"🗑️ Deleted snapshot v{version}")
        return True


if __name__ == "__main__":
    # Demo usage
    logging.basicConfig(level=logging.INFO)
    
    manager = PersonalitySnapshotManager(
        storage_path="data/test_snapshots",
        snapshot_interval=50
    )
    
    print("\n📸 Personality Snapshot Demo:")
    print("=" * 60)
    
    # Simulate personality evolution
    for i in range(1, 151, 50):
        personality_state = {
            'formality': 0.3 + (i * 0.001),
            'sarcasm': 0.6 - (i * 0.001),
            'technical_depth': 0.7
        }
        
        if manager.should_snapshot(i):
            snapshot = manager.create_snapshot(
                personality_state=personality_state,
                emotional_threads=[],
                conversation_count=i
            )
            print(f"\n✅ Created: {snapshot}")
    
    # List versions
    print("\n📋 Version History:")
    for v in manager.list_versions():
        print(f"  v{v['version']}: {v['conversation_count']} conversations")
    
    # Rollback
    print("\n↩️ Rolling back to v2...")
    old = manager.rollback_to_version(2)
    if old:
        print(f"  Restored: {old.personality_state}")
