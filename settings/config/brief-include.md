## Scoped worker policy

Execution and routine-work assignments use Codex gpt-6-luna with effort xhigh by default. Planning and optional independent-review assignments retain their separately assigned profiles. Do not silently downgrade the execution profile.

Use only the reasoning tier and CLI/model explicitly assigned in this task. Work from the supplied objective, relevant files, plan, and acceptance criteria. Keep the result concise: outcome, local copy and exact revision or diff, changed files, checks actually run with outcomes, and unresolved decisions or risks.

This worker is a leaf. Do not create subagents, additional coding-agent processes, managers, or nested swarms. If the assignment is ambiguous, requires a model change, or exceeds its scope, ask Firstmate. A planning scout returns its plan without making product changes. An execution worker implements the accepted scope and verifies it without broadening the task.

Implementation is subject to Firstmate's own code review. Hand back inspectable changes and verification evidence using the generated task's normal status and validation protocol: PR URL, branch, head SHA, changed files, checks actually run with outcomes, and remaining risks. Do not claim manager acceptance. Follow the task's existing waiting and completion instructions; do not invent a status event or bypass required validation, publication, or merge approval.

## Swarm branch rules

These apply when your brief names an integration branch.

- The saved copy of your work is the GitHub branch your brief names, a fresh branch such as `<task>-worker-2`. Push it and open your PR into the integration branch, not the default branch. A checkout on the PC is scratch the CLI needs; it is not the result. Do not finish while the only copy is unpushed.
- You may edit a file or function another worker also edits. Say which files you changed in the handoff. Paths in your brief are where you expect to work, not a lock.
- If your brief lists dependencies, wait until Firstmate says they have merged, then merge `origin/<integration branch>` into your branch before starting.
- Firstmate's verdict arrives as a steer and as a comment on your PR. `CHANGES REQUESTED` means fix each listed finding. `REJECTED` means redo the approach for the stated reason. Push new commits to the same branch, rerun the relevant checks, and return a finding-by-finding resolution with the new head SHA.
- Do not resolve a merge conflict with another worker yourself. A conflict helper reads every side and pushes a fresh `<task>-resolve-N` branch.
- Never rebase a pushed branch, force-push, delete branches, push unrelated changes or secrets, or merge anything yourself. Firstmate merges approved PRs into the integration branch; only the captain merges into the default branch.
