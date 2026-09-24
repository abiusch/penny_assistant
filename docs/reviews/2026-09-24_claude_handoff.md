# Penny reliability work — handoff to Claude

Snapshot: September 24, 2026. Read [current tasks](../../NEXT_PHASE_TASKS.md) for
later developments, [architecture](../SYSTEM_BLUEPRINT.md) for source locations
and [verification](../VERIFICATION.md) for commands. This supplements the
[September 7 handoff](2026-09-07_claude_handoff.md).

## Since the previous handoff

PRs #32–#41 are merged; main is `6b06d7ce04346dc35b594ca564eb136857119a1b`.
The work progressed from tool parsing/result replay and request-thread timeouts
to these reliability fixes:

- #36: model failures produce controlled replies instead of leaking prompts or
  provider exceptions; failed assistant turns skip persistence and success hooks.
- #37: config/data roots are independent of launch directory; helpers share the
  selected stores and encryption keys are preserved.
- #38: enforce emotion-tracking consent at storage/read boundaries. CJ explicitly
  chose to retain conversations while deleting derived emotional tracking data.
  Pending deletion retries after restart; consent-related writes are coordinated.
- #39: dependency updates and the specifically approved Claude-bot review allowlist.
  The workflow-changing review skipped rather than reviewing; later PRs received
  reviews after the workflow matched main.
- #40: restore conversation-ID lookups/counts after restart and exclude the source
  turn by ID from similar-conversation results.

Main's post-#40 test pipeline passed at `85b58bb`
([run 34767192912](https://github.com/abiusch/penny_assistant/actions/runs/34767192912)).
This is separate from the dependency watchdog's newer runs on that same commit.

## Latest memory fix and open dependency work

[PR #41](https://github.com/abiusch/penny_assistant/pull/41),
`865a19e58ab078f1ba9307a801a3c56f346006f5`: all five checks passed. Claude's two
posted reviews found no blockers and independently ran **653 passed, 2 expected
failures**, plus **30** characterizations. The PR rejects broken vector-store pairs,
reports unconfirmed writes, blocks normal reuse after failure, and persists before
caching/running post-save hooks. Its 18 new failure tests matter to future refactors.
CJ merged it September 24 as `6b06d7c`; this documentation branch includes it.
Main's post-merge CI also passed at `6b06d7c`, checked independently:
[run 36056483851](https://github.com/abiusch/penny_assistant/actions/runs/36056483851).

The PR provides individual-file atomic replacement, not paired transactions.
Second-file failure can leave a mixed pair; some equal-shape mismatches are not
detectable. Consent deletion intentionally retains its separate retry behavior,
including on an instance marked failed. Recovery, stale writers and transaction
design remain follow-ups. No live history was repaired, migrated or deleted.

[PR #42](https://github.com/abiusch/penny_assistant/pull/42) changes anyio and torch
pins plus the task document. Its author reports a clean install and **635 passed,
2 expected failures** before #41. All five earlier checks passed on `1e27574`,
but the review log ended while installation was still running, without a finished
review. A green review-job badge was insufficient evidence.

After #41 merged, refreshed #42 with main and reconciled only `NEXT_PHASE_TASKS.md`,
retaining both recaps. Refresh commit `7f782da` has **653 passed, 2 expected failures**
and **30 characterizations** locally in an isolated checkout. That run uses the
existing Python 3.13 environment with anyio 4.10.0 and torch 2.8.0; it validates
code/conflict resolution, not the upgraded pins. Fresh GitHub install/tests and
review are required on the refreshed commit before a merge recommendation.

The documentation branch and #42 both touch `NEXT_PHASE_TASKS.md`; reconcile status
and preserve relevant recaps rather than choosing one whole side of a conflict.
CJ retains merge authority under [AGENTS.md](../../AGENTS.md).

## Documentation adoption

Overlord contributed workflow ideas, not runtime personality or memory features.
This pass adds a code-backed architecture/test map and continuity links, flags the
December 2025 roadmap as historical, and corrects the obsolete restart-counter
warning. It preserves the existing task source and standing authority.

Hebbian, outcomes, goals/follow-ups and user-belief systems exist but default off
in the research pipeline. Preserve Penny's dry, natural voice, confidence-based
adaptation, explicit preferences, consent/deletion, snapshots and proactivity limits.
Developer archives remain separate from personal memory. No generic bootstrap,
hooks, runtime feature enablement or archive ingestion was performed.

Next implementation priorities remain in the task list: finish the open reliability
work, then address transactional memory durability and stale writers before entry
point/concurrent conversation cleanup. The two capability expected failures and
live web/audio verification are still open; passing offline checks does not close them.
