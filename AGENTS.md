# Project working agreement

CJ approved these standing instructions on September 13, 2026:

- Continue improving Penny using `NEXT_PHASE_TASKS.md` as the current task list.
- Independently prioritize fixes, edit code, run tests, update dependencies,
  repair CI, resolve conflicts, commit and push branches, and create or update
  pull requests. Keep the task document current.
- Ask CJ before merging, deploying, spending additional money, deleting live
  user data, or expanding security permissions.
- For PR #39 specifically, CJ approved allowing only the `claude` bot to trigger
  the existing review job, which has PR-write and identity-token permissions.
  This does not authorize other expansions of security permissions.

Use isolated synthetic data for tests. Preserve live conversation history and
encryption keys. Record actual validation results and distinguish local checks
from GitHub checks against a specific commit. App-enforced restrictions still apply.
