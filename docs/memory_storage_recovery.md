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

Stop writers and retain the affected files for inspection. Fix permissions or
available disk space as appropriate. If one file is missing or the pair is
inconsistent, restore a known matching `vector_store.index` and `vector_store.pkl`
pair from the same backup, together with the matching encryption key when needed.
Do not delete a remaining file simply to force creation of an empty store. Starting
the pipeline again validates the restored pair before it can accept new turns.
This development work performs no live data recovery, deletion, or migration.

## Limits and next work

The two replacements are **not an atomic transaction**. A process interruption or
second-file failure can leave a mixed pair requiring recovery. Count/dimension
validation detects many such mismatches, but cannot prove that two otherwise valid
files of the same shape belong to the same generation. No automatic backup or
reconstruction is introduced. Flushing each file is not a guarantee against every
power-loss/filesystem failure. Existing pickle files are trusted local data, not
safe inputs from unknown sources.

This change does not merge stale writers, physically remove deleted vectors, fix
legacy explicit filepath save/load wrappers, or make full-store saves incremental.
The next durability step needs a transactional record store or an explicit paired
checkpoint protocol, recovery tests and a writer coordination policy. Standalone
vector users without a consent manager retain their existing lack of shared locks.

Verification uses synthetic FAISS stores and an isolated pipeline: incomplete and
corrupt files, invalid metadata, dimension mismatch, both replacement failures,
serialization failure, failed reload/clear/delete, startup cleanup, and the actual
user-facing save-failure path. Existing consent/restart and pipeline characterization
tests also run without changing their assertions.
