# Emotional data consent

CJ's confirmed choice: keep ordinary conversation history when deleting emotional
data; remove derived emotion labels and emotional check-in history.

## Behavior

The research pipeline uses one consent manager for semantic memory, recent context
and personality snapshots. The default remains opt-out. Without tracking consent,
new conversation metadata omits `emotion`, `emotion_confidence`, `sentiment` and
`sentiment_score`. Emotion detection may still inform the current reply; it does
not create stored tracking labels. Text mentioning emotions remains ordinary
conversation text.

With consent, those fields are retained with the existing encryption behavior.
Check-in consent is separately required and cannot override tracking opt-out.
Changes to consent, intensity threshold and memory window take effect in the live
pipeline rather than requiring a restart to update the continuity enable flag.

`revoke_consent(delete_data=False)` disables further tracking. It does not erase
historical disk data. Ordinary prompt-facing memory reads suppress historical
tracking fields while opted out. Use `delete_data=True` to remove historical labels
and check-in threads from the active store.

## Existing API

These operations apply to the selected runtime data directory. No new web setting
or natural-language command is introduced by this change.

```python
pipeline.consent_manager.grant_consent(proactive_checkins=False)
pipeline.consent_manager.revoke_consent(delete_data=False)
pipeline.consent_manager.revoke_consent(delete_data=True)
```

Use these methods rather than mutating the `preferences` dictionary. Each boundary
reads the durable preference file; in-memory edits are not consent changes.
Standalone `SemanticMemory` defaults to the consent file under its conventional
data root (`<data>/embeddings/vector_store`); custom layouts should pass an explicit
`consent_manager`. Standalone snapshot managers also accept one. A standalone
ConsentManager without a connected deletion handler raises if deletion is requested,
instead of claiming it deleted a store it does not own.

## Deletion and recovery

1. Persist opt-out and a pending-deletion marker, with a deletion cutoff timestamp.
2. Clear current emotional threads and cached metadata. Redact the four tracking
   fields from the vector metadata file, preserving conversation text, vector IDs,
   embeddings, timestamps and unrelated metadata. Remove emotional threads from
   every `snapshot_v*.json`, preserving personality state and snapshot identity.
3. Persist the completion audit event and clear the pending marker only after all
   cleanup succeeds. New opt-in is blocked while deletion remains pending.

The main pipeline resumes pending deletion during initialization. An unreadable
snapshot, missing metadata file or failed replacement produces an error and leaves
the request pending. Restore/repair the affected file and retry startup or call
`pipeline.consent_manager.resume_pending_deletion()`. If the initial consent update
itself cannot be saved, the request is explicitly unconfirmed and tracking is
disabled in that manager; a future process cannot recover an intent that never
reached disk.

Preferences, redacted vector metadata and redacted snapshots use temporary-file
replacement with file flushing. A failed replacement preserves the prior file and
cleans its temporary file. Completion recording can safely be retried after data
has already been redacted. This is recoverable multi-file cleanup, not one database
transaction or a guarantee against every power-loss/filesystem failure.

A persistent `.user_consent.json.lock` sidecar serializes participating runtime
writes and consent changes across threads/processes. The OS releases the advisory
lock on process exit; do not delete its sidecar while applications are running.
The deletion cutoff also prevents older cached records/threads from being written
back with removed labels, even after a later opt-in. New opted-in turns can retain
their own labels. The test suite exercises thread and separate-process contention
on the local platform; Windows uses its native byte-range locking implementation.

## Scope and remaining work

This removes application tracking metadata and check-in history from the active
store. It does not delete conversations, their text-derived embeddings, personality
preferences, unrelated files, encryption keys, existing logs or external backups
and exports. It is not filesystem-level secure erasure. Historical audit entries
from the old implementation are retained; they are not automatically treated as
new deletion requests. No actual user deletion or consent toggle was run as part
of development.

Writers must use these consent-aware interfaces and the same consent file. Generic
VectorStore use and other legacy/experimental stores are not a consent service.
The vector store's older non-atomic general-save behavior and stale conversation
snapshot overwrites still need a separate durability/single-writer improvement;
the consent lock does not merge independent conversation snapshots. Web request
state isolation, current-turn emotion inference policy, and UI settings remain
separate work.

Verification uses isolated real stores with synthetic conversations and mocked
model/audio/embeddings. Tests cover default opt-out, opt-in encryption, revoke with
and without deletion, preserved text/vectors/keys, pending retries and corruption,
mid-generation revocation, stale caches after regrant, and thread/process ordering.
One characterization formerly asserting metadata retention during opt-out is
intentionally corrected. Two check-in fixtures now grant consent through the public
API, and the encrypted-restart probe explicitly opts in. These are disclosed
behavior/setup changes, not presented as a behavior-preserving refactor.
