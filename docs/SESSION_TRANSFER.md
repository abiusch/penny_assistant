# Penny session continuity

Read [AGENTS.md](../AGENTS.md), then [NEXT_PHASE_TASKS.md](../NEXT_PHASE_TASKS.md).
The task list owns current priorities, PR status and validation results. This page
is a short navigation and handoff guide, not a second task queue.

- [Architecture and behavior map](SYSTEM_BLUEPRINT.md): code locations, disabled
  feature switches, voice, consent and storage contracts.
- [Verification guide](VERIFICATION.md): offline commands, coverage limits and
  how to distinguish local, PR and main results.
- [September 24 Claude handoff](reviews/2026-09-24_claude_handoff.md): dated work
  summary; refresh GitHub state before relying on its open-PR status.
- [September 6 review](reviews/2026-09-06_project_review.md): original findings;
  historical defect probes are not current correctness checks.

Start by checking the checkout, local edits, current PR heads and review results.
Finish by updating the task list with actual evidence and linking any new dated
handoff here. Preserve ongoing changes and the approved merge boundary.

Do not run Overlord's generic bootstrap over Penny. Developer transcript archives
stay outside runtime memory; no transcript ingestion, new hooks or optional model
indexing is part of this tailored documentation adoption.
