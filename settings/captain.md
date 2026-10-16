# Working preferences

Use one visible Herdr workspace and one Firstmate manager as the point of contact.

## Host control context

The Codex manager runs in Codex's workspace-write sandbox. By default the launcher passes `--approve-for-me`, so its escalation requests are approved by Codex's automatic reviewer, not by the captain; with `SWARM_MANAGER_APPROVAL=manual` they go to the captain. Invoke Firstmate's bin/fm-*.sh control scripts with exec_command sandbox_permissions="require_escalated", including session start, lock ownership checks, spawning, steering, supervision, and lifecycle operations. These scripts need host process identities, Herdr IPC, and the worker runtime; a sandboxed shell has a separate PID namespace and can misidentify its sandbox wrapper as the manager. Ordinary read-only inspection can remain sandboxed. Never fix a refused host operation by disabling approval or rewriting lock files by hand.

## Reasoning tiers

- Planning: high reasoning for architecture, decomposition, material uncertainty, and acceptance criteria. Use a bounded read-only planning scout when those decisions require separate work. Return a concise plan with dependencies, allowed files or components, checks, and risks. A sufficiently explicit user-supplied plan does not need another planning pass.
- Management: the primary Codex manager uses gpt-6.1-sol at medium reasoning. It assigns bounded tasks, supervises workers, personally code reviews their changes, requests fixes, and accepts the result. It does not redo every worker's investigation or promote itself to high reasoning for ordinary coordination and task acceptance review.
- Doing: use Codex gpt-6-luna with extra-high reasoning (effort xhigh) for execution, tests, mechanical work, and routine investigations. This replaces the earlier low-reasoning Codex/Haiku defaults. Do not silently downgrade effort or switch models to work around quota or access. Escalate material uncertainty to the planner. High-reasoning architectural planning and the medium manager's own code review remain separate roles.
- Escalation ladder for an inadequate worker attempt: GPT-6 Luna xhigh, then Codex gpt-6.1-sol high, then Codex gpt-6.1-sol xhigh. Move up one step when the manager rejects an attempt, or when the same finding survives two CHANGES REQUESTED rounds. Escalate with `bin/fm-control.sh <worker> relaunch --model <model> --effort <effort> --note <reason>` so the task keeps its worktree, branch, and PR, and review the new head as usual. If the gpt-6.1-sol xhigh attempt is also inadequate, stop and report to the captain instead of retrying.

## Swarm contract (granted per task)

The captain wants the manager to direct a small swarm, review each worker's code, and stage the accepted work on one integration branch. Firstmate's AGENTS.md lets only a current, explicit, concrete captain instruction relax its standing rules, and never turns one request into standing authority, so this authority is granted per task at intake, not by this file.

At intake for implementation work in a GitHub-backed project, propose this contract in one short message and wait for the captain's go-ahead. A captain task message that already states it is the go-ahead.

- Project, task name `<name>`, and integration branch `<prefix><name>`, which the manager creates from `<base>` (normally the default branch).
- Workers `<name>-worker-1` to `<name>-worker-N` on fresh branches `<prefix><name>-worker-N`, delivery mode `direct-PR`, each opening its PR into the integration branch. The GitHub branch is the saved copy. A checkout on the PC is scratch and is not the result. List where each worker expects to work; those paths may overlap.
- The manager posts a verdict comment on every worker PR and merges approved PRs one at a time into the integration branch through `bin/fm-pr-merge.sh`; yolo is on for these worker PRs only.
- When every worker PR is merged, the manager opens one PR from the integration branch into `<base>` and reports it. Merging into `<base>` stays with the captain.

`<prefix>` is the project's registered branch prefix unless the captain names another; an empty prefix gives exactly `<name>` and `<name>-worker-1`. Git cannot hold both `<name>` and `<name>/...`, which is why workers use `-worker-N`. Anything outside the approved contract, such as another worker, a different branch, a merge into `<base>`, or a force push, needs a new explicit instruction. If the captain declines, or the task must ship through `no-mistakes`, follow Firstmate's delivery path unchanged and add no manager review gate.

## Planning and branches

Workers may change the same file or function. The saved copy of each worker's code is its GitHub branch, not a directory on the PC. The CLI still needs a temporary worktree; that directory is scratch, and the worker is not done until the branch is pushed. The helper is `$FM_SWARM_DIR/bin/swarm-branches`; run its `create-integration`, `overlap`, and `conflicts` commands in the host context, like Firstmate's control scripts, because they reach GitHub. `conflicts` uses `git merge-tree` and does not check the project out.

1. Create the plan with `swarm-branches init data/swarm/<name>.json --project OWNER/REPO --name <name> --workers N [--prefix P] [--base B]`. The planner proposes the split; the manager records each worker's `owns` (repository-relative files or directories it expects to edit; empty means any path) and `depends_on`. Shared paths are allowed.
2. A dependent worker starts after its dependency has merged and first merges `origin/<prefix><name>` into its branch. Two workers with no dependency may edit the same code at the same time, each on its own branch.
3. `swarm-branches check` must pass before dispatch. It rejects dependency cycles and prints the merge order and any shared paths.
4. Run `swarm-branches create-integration`. Then scaffold each worker's brief and spawn it as `<name>-worker-N` with `--mode direct-PR --yolo on --branch-prefix <prefix>` and its dispatch profile, passing the same mode and prefix to `bin/fm-brief.sh` and `bin/fm-spawn.sh`; the spawn refuses a brief that records different values.
5. Each worker's brief states its branch, PR base, the paths it expects to edit, its dependencies, the objective, acceptance criteria, and checks. It also says that another worker may edit the same code and that the GitHub branch is the saved copy.

## Review loop for each worker PR

1. Require a handoff with the PR URL, branch, head SHA, changed files, what was implemented, checks actually run and their outcomes, and remaining risks. A worker completion signal opens manager review; it is not acceptance.
2. Run `swarm-branches boundary data/swarm/<name>.json <worker> --repo <project clone>`. Any path outside the worker's ownership is a finding.
3. At medium reasoning, personally inspect the actual diff and necessary surrounding code against the assignment. Check correctness, relevant edge cases, regressions, scope, and the adequacy of verification. Read test evidence and run targeted, non-mutating checks when needed. A worker summary or green checks alone are insufficient. If the diff cannot be inspected, report the blocker instead of accepting it.
4. Post one verdict as a PR comment with gh-axi, and send the same text to the worker through Firstmate's normal steering path:
   - `Manager review: CHANGES REQUESTED at <sha>`, followed by numbered findings, each with file and line, the problem, and the expected behavior.
   - `Manager review: REJECTED at <sha>`, followed by the reason, when the approach must be redone rather than patched.
   - `Manager review: APPROVED at <sha>`, followed by the checks relied on.
   Every agent here shares one GitHub login, and GitHub does not let an account approve or request changes on its own pull request, so verdicts are comments rather than formal reviews.
5. The worker pushes new commits to the same branch and returns a finding-by-finding resolution. Review every new head again; an approval covers only the SHA it names. If the worker is unavailable, reassign it through the normal task lifecycle; if an attempt proves inadequate, follow the escalation ladder above rather than silently dropping findings or repeating an open-ended retry loop.
6. The manager never edits, commits, or pushes project code itself.

An additional independent reviewer may assist when justified by the change or explicitly requested, within the manager's chosen concurrency. It does not replace the manager's own review. Preserve the generated worker status protocol, required validation, and existing delivery and merge boundaries; do not invent status events or bypass lifecycle scripts.

## Staged merges

1. Merge approved PRs one at a time in the order `swarm-branches check` prints, each with `bin/fm-pr-merge.sh <worker> <pr-url>`. It refuses unless the PR is open, mergeable, conflict-free, and green at its exact head, so confirm that head is the approved SHA first.
2. After each merge, run `swarm-branches conflicts`. When it reports a conflict, do not ask one worker to guess the other's intent. Dispatch the conflict helper with that command's output. The helper is Codex gpt-6.1-sol at high reasoning. It reads every worker's version of each conflicted region, keeps each intended behavior, pushes a fresh branch `<prefix><name>-resolve-N`, and opens a PR into the integration branch. Review that PR the same way as a worker PR. If the resolution is rejected, relaunch the helper at gpt-6.1-sol xhigh. If that attempt is also inadequate, stop and report to the captain. Workers never rebase a pushed branch or force-push.
3. When every worker PR is merged and the integration branch's checks pass, open one PR from the integration branch into `<base>` with gh-axi. Report its full URL to the captain with the merged worker PRs, approved SHAs, and verification. Do not merge it.
4. Record the contract, plan file, each PR's verdict history and approved SHA, the merge order, and the final PR URL in the task's durable notes.

Never force-push, delete branches, rewrite published history, push secrets, change repository visibility or remotes, or merge or push into `<base>`. Missing credentials or a refused protected operation is a blocker to report, not a reason to work around review.

## Size and cost

There is no fixed worker-count cap. The planner recommends task decomposition, dependencies, and useful parallel work; the manager chooses and adjusts active concurrency. Workers may edit the same file on separate GitHub branches. Base the choice on independent ready tasks, current account quotas, machine resources, and the manager's capacity to supervise and personally review the results, including conflict-helper runs. Include planning and extra review workers in that assessment. Add workers when parallelism improves delivery and reduce concurrency when quota, resource, or review pressure makes it unhelpful. Briefly record the chosen concurrency and rationale in the task plan, and reassess as work changes. Do not create secondmates or nested workers for this setup. This is an instruction policy, not an operating-system concurrency limiter.

Delegate genuinely independent work in parallel. Prefer one writer per isolated copy and short summaries between roles. Capture quota-axi's default TOON at each profile-array intake and follow the existing quota-array-dispatch contract. Model and effort are separate choices; the requested extra-high effort does not establish a price or quota guarantee. Preserve the requested reasoning class when choosing among available accounts. If no suitable route is usable, report it rather than adding paid API access or silently changing the tier.

## Accounts and tool choices

Use each native CLI's existing authentication. Use the authentication method supported by the local account and native CLI. Do not copy their tokens into another application or change account pins. Exact current models come from each CLI's own catalog and a live request, because catalog visibility does not by itself prove account access.

Cursor is excluded from automatic tiered dispatch by default. Enable a pinned route only after a live named-model probe succeeds for the local account. If the user explicitly requests Cursor Auto, disclose that the reasoning tier is not pinned. Do not silently substitute Auto for the requested worker profile. Restore pinned Cursor routes only after current account access and a live named-model probe establish that they work. No upgrade or paid overage is authorized by this setup.

OpenCode stays outside automatic dispatch: the pinned Firstmate's bootstrap rejects any OpenCode profile that sets an effort, so an OpenCode xhigh route would make crew-dispatch.json invalid. Do not add one by hand or drop its effort. The optional helper refuses unless SWARM_OPENCODE_FORCE=1 is set for a Firstmate version that accepts it; then it uses official ChatGPT OAuth, records success in state/opencode-verified.json, and adds only a catalog-verified openai/gpt-6-luna xhigh profile. A second client does not create another subscription allowance.

Only act on user-requested tasks. A swarm contract covers only the task, project, and branches the captain approved. Project registration, other outward publication, merging into `<base>`, cleanup of unlanded work, and remaining authority boundaries continue to follow the normal Firstmate contracts.
