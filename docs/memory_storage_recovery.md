# Memory storage failures

Penny now raises `MemoryStorageError` when the vector store cannot be loaded or
saved. A missing half of an existing store, unreadable file, wrong embedding
dimension, invalid metadata record/ID, or mismatched index count and next ID stops
startup. It does not silently create an empty replacement. Both files absent
still means a new empty store. Valid metadata-only deletion holes remain supported.

Loads validate temporary objects before installing them. A failed reload retains
the old objects internally but marks that instance unusable; normal reads, writes,
deletion, clearing and statistics refuse further use. A successful validated
`VectorStore.load()` or a new instance can resume after the files are repaired.
Restart the pipeline after recovery so its conversation-ID map is rebuilt too.

Saves serialize both files before changing either, then replace each through a
flushed temporary file. A failure replacing one file preserves that file's old
bytes and raises an unconfirmed-save error. It also marks the instance unusable,
so partially mutated in-memory records cannot be returned as saved conversations
or silently written by a later operation. Consent cleanup retains its separate
pending-deletion/retry behavior.

The research pipeline saves persistent memory before caching the turn or running
post-save learning/follow-up work. On a storage failure it returns the generated
answer with a short warning that saving could not be confirmed, and skips success
metrics and response tagging. Storage errors escaping earlier stages return a
memory-unavailable reply. Failed memory initialization shuts down the research
manager. Auxiliary non-storage failures keep their prior non-fatal behavior.

## Recovery

If another instance changed the store, leave the newer files intact and restart
the outdated pipeline. This conflict does not by itself mean files are damaged.
An unsuccessful turn was not committed; decide whether to retry it after restart.
Do not restore an older backup over healthy newer conversations to clear a conflict.

Stop writers and retain the affected files for inspection. Fix permissions or
available disk space as appropriate. If one file is missing or the pair is
inconsistent, restore a known matching `vector_store.index` and `vector_store.pkl`
pair from the same backup, together with the matching encryption key when needed.
Do not delete a remaining file simply to force creation of an empty store. Starting
the pipeline again validates the restored pair before it can accept new turns.
This development work performs no live data recovery, deletion, or migration.

## Competing writers

Before `add`, `save`, `delete` or `clear` changes memory, VectorStore compares the
current pair's SHA-256 fingerprints with the bytes it last loaded or successfully
saved. Different content, missing files, or another instance's first save causes
`MemoryStorageError` before mutation. That instance then refuses normal reads and
writes until a validated reload. Restart the full pipeline to also rebuild its
conversation-ID map. It does not silently merge or retry an unsuccessful turn.

A shared thread/process lock covers the check, mutation and both writes. Startup
and explicit loads use the same lock, so cooperating readers cannot load the
temporary mixed pair halfway through a healthy save. Standalone VectorStore
instances participate too. The existing consent lock is acquired first; the
shared lock implementation has moved to `storage_lock.py`. A stable
`.vector_store.index.lock` sidecar remains on disk; do not remove it while writers
are running. Relative paths are resolved at construction so a later working-directory
change cannot redirect this instance's files or locks.

Emotional deletion still reads and redacts the latest disk metadata, including
newer conversations absent from its cache. Successful redaction by an outdated
instance does not make its stale conversation snapshot safe to save. Its ordinary
operations remain blocked until reload/restart. The current owner can continue
after its own successful redaction. The consent pending-deletion/retry protocol
is preserved; an older instance cannot restore deleted labels by saving its cache.

## Limits and next work

The two replacements are **not an atomic transaction**. A process interruption or
second-file failure can leave a mixed pair requiring recovery. Count/dimension
validation detects many such mismatches, but cannot prove that two otherwise valid
files of the same shape belong to the same generation. No automatic backup or
reconstruction is introduced. Flushing each file is not a guarantee against every
power-loss/filesystem failure. Existing pickle files are trusted local data, not
safe inputs from unknown sources.

Fingerprinting reads both complete files before each outer write, adding I/O to
the existing full-store rewrite. This favors preservation over throughput; it is
not incremental persistence. Normal in-memory reads are snapshots, not automatic
cross-instance refresh, and this does not isolate simultaneous web conversations.
The lock is advisory: old Penny versions, manual file edits and other programs
that bypass it can still race. All writers must use the cooperating implementation.
Network filesystem locking and power-loss guarantees are not established here.

This change rejects rather than merges stale writers. Physical removal of deleted
vectors, legacy explicit filepath save/load wrappers and incremental saves remain
separate work.
The next durability step needs a transactional record store or an explicit paired
checkpoint protocol and recovery tests. Writer conflict rejection is a prerequisite,
not a replacement for that work.

Verification uses synthetic FAISS stores and an isolated pipeline: incomplete and
corrupt files, invalid metadata, dimension mismatch, both replacement failures,
serialization failure, failed reload/clear/delete, startup cleanup, and the actual
user-facing save-failure path. Existing consent/restart and pipeline characterization
tests cover the related contracts. Writer-conflict cases exercise outdated
add/save/delete/clear, first-save races, same-shape changes, missing files, separate
processes, threads, startup during paired writes, consent cleanup and the actual
pipeline warning/side effects. One consent test now explicitly expects an outdated
writer to fail and uses a restarted pipeline for the next successful turn;
the preservation assertions remain. Characterization assertions are unchanged.
