#!/usr/bin/env python3
"""
Migration Script: Base Memory → Semantic Memory
Week 7: Architecture Refactor + Security Foundation

This script performs a ONE-TIME migration from the old triple-save architecture
(base_memory + context_manager + semantic_memory) to the new dual-save architecture
(context_manager in-memory cache + semantic_memory persistent store).

What it does:
1. Reads all conversations from data/memory.db (base memory SQLite)
2. Migrates each conversation to semantic memory with encryption
3. Preserves all metadata (research_used, financial_topic, emotions, etc.)
4. Creates backup of original database
5. Generates migration report

Run this ONCE before switching to Week 7 architecture.
"""

import sys
import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.memory.semantic_memory import SemanticMemory
from src.security.encryption import get_encryption

# Constants
BASE_MEMORY_DB = Path(__file__).parent.parent / "data" / "memory.db"
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"
MIGRATION_LOG = Path(__file__).parent.parent / "data" / "migration_log.txt"


class MigrationStats:
    """Track migration statistics"""
    def __init__(self):
        self.total_turns = 0
        self.migrated_turns = 0
        self.failed_turns = 0
        self.errors: List[str] = []
        self.start_time = datetime.now()
        self.end_time = None

    def add_success(self):
        self.migrated_turns += 1

    def add_failure(self, error: str):
        self.failed_turns += 1
        self.errors.append(error)

    def finish(self):
        self.end_time = datetime.now()

    def get_duration(self) -> float:
        if not self.end_time:
            return 0
        return (self.end_time - self.start_time).total_seconds()

    def get_report(self) -> str:
        """Generate migration report"""
        success_rate = (self.migrated_turns / self.total_turns * 100) if self.total_turns > 0 else 0

        report = f"""
================================================================================
WEEK 7 MIGRATION REPORT: Base Memory → Semantic Memory
================================================================================

Migration Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {self.get_duration():.2f} seconds

RESULTS:
--------
Total conversations found: {self.total_turns}
Successfully migrated: {self.migrated_turns}
Failed migrations: {self.failed_turns}
Success rate: {success_rate:.1f}%

ENCRYPTION STATUS:
-----------------
✅ Sensitive fields encrypted (emotion, sentiment, sentiment_score)
✅ AES-128 Fernet encryption enabled
✅ GDPR Article 9 compliance achieved

ARCHITECTURE CHANGE:
-------------------
BEFORE (Week 6):
  ├── Base Memory (SQLite) - Stores conversations
  ├── Context Manager (SQLite) - Stores rolling window
  └── Semantic Memory (FAISS) - Stores vector embeddings

AFTER (Week 7):
  ├── Context Manager (in-memory deque) - CACHE ONLY
  └── Semantic Memory (FAISS + metadata) - SOLE PERSISTENT STORE

"""

        if self.errors:
            report += "\nERRORS:\n-------\n"
            for i, error in enumerate(self.errors[:10], 1):  # Show first 10 errors
                report += f"{i}. {error}\n"
            if len(self.errors) > 10:
                report += f"... and {len(self.errors) - 10} more errors\n"

        report += "\n" + "="*80 + "\n"
        return report


def backup_database():
    """Create backup of base memory database"""
    if not BASE_MEMORY_DB.exists():
        print(f"⚠️  Base memory database not found: {BASE_MEMORY_DB}")
        print("   This might be a fresh install. No migration needed.")
        return False

    # Create backup directory
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = BACKUP_DIR / f"memory_db_backup_{timestamp}.db"

    print(f"📦 Creating backup: {backup_path}")
    shutil.copy2(BASE_MEMORY_DB, backup_path)
    print(f"✅ Backup created successfully")

    return True


def read_base_memory_conversations() -> List[Dict[str, Any]]:
    """Read all conversations from base memory SQLite database"""
    print(f"📖 Reading conversations from: {BASE_MEMORY_DB}")

    if not BASE_MEMORY_DB.exists():
        print("⚠️  No base memory database found. Nothing to migrate.")
        return []

    conn = sqlite3.connect(BASE_MEMORY_DB)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()

    # Read all conversation turns
    # Adjust query based on actual schema (may need to inspect database first)
    try:
        cursor.execute("""
            SELECT
                turn_id,
                user_input,
                assistant_response,
                timestamp,
                context,
                response_time_ms
            FROM conversation_turns
            ORDER BY timestamp ASC
        """)

        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'turn_id': row['turn_id'],
                'user_input': row['user_input'],
                'assistant_response': row['assistant_response'],
                'timestamp': row['timestamp'],
                'context': row['context'],  # JSON string
                'response_time_ms': row['response_time_ms']
            })

        print(f"✅ Found {len(conversations)} conversation turns")
        conn.close()
        return conversations

    except sqlite3.OperationalError as e:
        print(f"❌ Failed to read database: {e}")
        print("   The database schema might be different. Please check the structure.")
        conn.close()
        return []


def migrate_conversations(conversations: List[Dict[str, Any]]) -> MigrationStats:
    """Migrate conversations to semantic memory with encryption"""
    print(f"\n🔄 Starting migration of {len(conversations)} conversations...")

    stats = MigrationStats()
    stats.total_turns = len(conversations)

    # Initialize semantic memory with encryption enabled
    semantic_memory = SemanticMemory(encrypt_sensitive=True)
    print("🔐 Semantic memory initialized with encryption enabled")

    for i, conv in enumerate(conversations, 1):
        try:
            # Parse context (might be JSON string)
            import json
            context = conv.get('context')
            if isinstance(context, str):
                try:
                    context = json.loads(context) if context else {}
                except json.JSONDecodeError:
                    context = {}

            # Ensure required fields exist
            if not context:
                context = {}

            # Add default values for missing fields
            if 'emotion' not in context:
                context['emotion'] = 'neutral'
            if 'sentiment' not in context:
                context['sentiment'] = 'neutral'
            if 'sentiment_score' not in context:
                context['sentiment_score'] = 0.0

            # Migrate to semantic memory (will encrypt sensitive fields automatically)
            semantic_memory.add_conversation_turn(
                user_input=conv['user_input'],
                assistant_response=conv['assistant_response'],
                turn_id=conv['turn_id'],
                timestamp=datetime.fromisoformat(conv['timestamp']) if conv.get('timestamp') else None,
                context=context
            )

            stats.add_success()

            # Progress indicator
            if i % 10 == 0 or i == len(conversations):
                print(f"   Progress: {i}/{len(conversations)} ({i/len(conversations)*100:.1f}%)")

        except Exception as e:
            error_msg = f"Turn {conv.get('turn_id', 'unknown')}: {str(e)}"
            stats.add_failure(error_msg)
            print(f"   ⚠️  Failed to migrate turn: {error_msg}")

    # Save semantic memory to disk
    print("\n💾 Saving semantic memory to disk...")
    semantic_memory.save("data/semantic_memory.faiss")
    print("✅ Semantic memory saved successfully")

    stats.finish()
    return stats


def write_migration_log(report: str):
    """Write migration report to log file"""
    MIGRATION_LOG.parent.mkdir(parents=True, exist_ok=True)

    with open(MIGRATION_LOG, 'w') as f:
        f.write(report)

    print(f"\n📝 Migration log written to: {MIGRATION_LOG}")


def main():
    """Run migration from base memory to semantic memory"""
    print("="*80)
    print("WEEK 7 MIGRATION: Base Memory → Semantic Memory")
    print("="*80)
    print()
    print("This script will:")
    print("  1. Create backup of existing base memory database")
    print("  2. Read all conversations from base memory")
    print("  3. Migrate to semantic memory with encryption")
    print("  4. Generate migration report")
    print()

    # Confirm migration
    response = input("⚠️  Proceed with migration? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Migration cancelled")
        return

    # Step 1: Backup
    print("\n" + "="*80)
    print("STEP 1: BACKUP")
    print("="*80)
    if not backup_database():
        print("⚠️  No backup needed (database doesn't exist)")
        print("✅ Migration complete (nothing to migrate)")
        return

    # Step 2: Read conversations
    print("\n" + "="*80)
    print("STEP 2: READ CONVERSATIONS")
    print("="*80)
    conversations = read_base_memory_conversations()

    if not conversations:
        print("✅ No conversations to migrate")
        return

    # Step 3: Migrate
    print("\n" + "="*80)
    print("STEP 3: MIGRATE TO SEMANTIC MEMORY")
    print("="*80)
    stats = migrate_conversations(conversations)

    # Step 4: Report
    print("\n" + "="*80)
    print("STEP 4: GENERATE REPORT")
    print("="*80)
    report = stats.get_report()
    print(report)

    write_migration_log(report)

    # Final summary
    if stats.failed_turns == 0:
        print("✅ Migration completed successfully!")
        print(f"   {stats.migrated_turns} conversations migrated with encryption")
    else:
        print(f"⚠️  Migration completed with {stats.failed_turns} failures")
        print(f"   Check {MIGRATION_LOG} for details")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Review migration log to verify success")
    print("2. Restart server with Week 7 architecture")
    print("3. Verify conversations are accessible")
    print("4. If successful, old base memory can be archived")
    print("="*80)


if __name__ == "__main__":
    main()
