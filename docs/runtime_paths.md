# Configuration and data locations

The research conversation pipeline, its text launcher (`chat_penny.py`), and web
backend use paths rooted in the source checkout, regardless of the directory from
which Python is launched. They do not change the process working directory.

## Selection rules

| Resource | Default | Override |
| --- | --- | --- |
| Main configuration | `<project>/penny_config.json`; legacy `<project>/config/penny_config.json` only if the first is absent | `PENNY_CONFIG`, or the pipeline's explicit `config_path` argument |
| Conversation data | `<project>/data` | `PENNY_DATA_DIR`, or the pipeline's explicit `data_dir` argument |
| Personality database | `<selected data>/personality_tracking.db` | Pipeline's explicit `db_path` argument |
| Encryption key | `<selected data>/.encryption_key` | Select the corresponding data directory; keys are not migrated automatically |

Explicit arguments take precedence over environment variables. Absolute paths are
used directly; relative overrides resolve against the project root, not the launch
directory or selected config's parent. `~` is expanded. Changing the configuration
file alone does not change the data directory. Restart the application after
changing environment variables; this is not live model reconfiguration.

The shared configuration reader serves the model registry, base pipeline/router,
and legacy personality filter. Missing or invalid selected main configuration
causes pipeline startup to fail instead of silently selecting another model/file.
The standalone personality filter retains its empty-settings fallback on read
errors. The research pipeline loads one config snapshot for its components and
constructs its selected model once.

Example with a POSIX shell, using existing locations you intend to open:

```bash
PENNY_CONFIG=/absolute/path/to/penny_config.json PENNY_DATA_DIR=/absolute/path/to/data python /absolute/path/to/penny_assistant/chat_penny.py
```

Use the project's installed Python environment. This change does not install
missing web/audio dependencies or change how the server is exposed.

## What follows the selected data directory

ResearchFirstPipeline passes absolute paths to semantic memory and its encryption
key, consent preferences, personality snapshots, personality/slang/context helpers,
milestone tracking and A/B storage. The adapter's personality prompt also receives
the pipeline's database. The web backend reuses the pipeline's trackers; the text
observer receives the same personality database. Personality caches are keyed by
resolved database path, and pipeline A/B instances and encryption objects are no
longer shared across distinct data roots.

Standalone legacy/experimental scripts and lower-level storage constructors may
still have their own defaults. TTS/model caches, logs, packaging, voice routing
unification, and web request concurrency are separate work. This is not a migration
of every historical entry point or every use of a relative path in the repository.

## Existing data is preserved

There is no automatic data move, merge, deletion, or key rotation. This checkout's
`web_interface/data` already points to `../data` through a symlink; that is supported
and left intact.

If a different installation has a populated, separate `web_interface/data`, default
selection stops with an explanation. Set `PENNY_DATA_DIR` to the intended existing
store. Before migrating or combining stores, back up each directory **with its
matching encryption key** and establish which history belongs to which store.
Older alternate stores may have used the project-root key. An existing vector
store without a matching local key must have that key restored before startup;
Penny will not create a replacement. Invalid nonempty keys are not overwritten,
and an empty key for an existing store is rejected too. A new empty store can
still generate a fresh key, including into a preallocated empty key file.

## Verification and remaining limits

Offline tests exercise explicit and default selection, decoy files in the launch
directory, invalid configuration, separate legacy stores, symlinks, independent
pipeline stores, cache isolation/invalidation, key preservation and text observer
wiring. Three fresh Python processes launch from different scratch folders using
the real pipeline, prompt builders and persistence, with fake HTTP/audio/embeddings.
They retrieve previous synthetic turns and decrypt stored emotion metadata using
the same key. Tests assert real project data is unchanged.

This verifies startup paths and synthetic restart retrieval, not live microphone,
web browser or model behavior. The existing memory statistics counter uses an
in-memory turn map and resets on restart even though vector search recovers stored
turns; repairing that map and crash-safe persistence remains separate work.
