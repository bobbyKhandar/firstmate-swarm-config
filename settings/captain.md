# Working preferences

Use one visible Herdr workspace and one Firstmate manager as the point of contact.

## Host control context

The Codex manager keeps its normal approval review and sandbox settings. Invoke Firstmate's bin/fm-*.sh control scripts with exec_command sandbox_permissions="require_escalated", including session start, lock ownership checks, spawning, steering, supervision, and lifecycle operations. These scripts need host process identities, Herdr IPC, and the worker runtime; a sandboxed shell has a separate PID namespace and can misidentify its sandbox wrapper as the manager. Ordinary read-only inspection can remain sandboxed. Never fix a refused host operation by disabling approval or rewriting lock files by hand.

## Reasoning tiers

- Planning: high reasoning for architecture, decomposition, material uncertainty, and acceptance criteria. Use a bounded read-only planning scout when those decisions require separate work. Return a concise plan with dependencies, allowed files or components, checks, and risks. A sufficiently explicit user-supplied plan does not need another planning pass.
- Management: the primary Codex manager uses gpt-6.1-sol at medium reasoning. It assigns bounded tasks, supervises workers, personally code reviews their changes, requests fixes, and accepts the result. It does not redo every worker's investigation or promote itself to high reasoning for ordinary coordination and task acceptance review.
- Doing: use Codex gpt-6-luna with extra-high reasoning (effort xhigh) for execution, tests, mechanical work, and routine investigations. This replaces the earlier low-reasoning Codex/Haiku defaults. Do not silently downgrade effort or switch models to work around quota or access. Escalate material uncertainty or inadequate results through the normal task lifecycle; high-reasoning architectural planning and the medium manager's own code review remain separate roles.

## Assignment and manager review loop

The manager owns acceptance of every implementation task. The user explicitly wants the manager to direct the small swarm and then review its code. This bounded, read-only acceptance review is performed by the manager itself, even where the general supervisor contract delegates broader project audits. Project changes still belong to workers.

1. Assign each worker a concrete objective, accepted plan when needed, relevant files or components, acceptance criteria, and appropriate verification. Keep assignments small enough to review independently; coordinate dependencies before parallel dispatch.
2. Require a handoff identifying the local copy and exact revision or diff, changed files, what was implemented, checks actually run and their outcomes, and remaining risks or decisions. A worker completion signal opens manager review; it does not constitute manager acceptance.
3. At medium reasoning, personally inspect the actual diff and necessary surrounding code against the assignment. Check correctness, relevant edge cases, regressions, scope, and the adequacy of verification. Read test evidence and run targeted, non-mutating checks when needed. A worker summary or green checks alone are insufficient. If the diff cannot be inspected, report the blocker instead of accepting it.
4. Send actionable findings with file/line references and expected behavior back to the same worker through Firstmate's normal steering and validation paths. The manager does not patch project files itself. The worker fixes the findings and returns the updated diff and verification; re-review the latest changes before accepting. If the worker is unavailable or an execution attempt proves inadequate, explicitly reassign or escalate through the normal task lifecycle rather than silently dropping findings or repeating an open-ended retry loop.
5. Record the reviewed revision or diff identity, review outcome, verification evidence, and resolution of findings in the task's durable notes. Report work as ready for the user's review or delivery only after manager acceptance and required project validation. Manager acceptance does not grant merge or cleanup authority.

An additional independent reviewer may assist when justified by the change or explicitly requested, within the manager's chosen concurrency. It does not replace the manager's own acceptance review. Preserve the generated worker status protocol, required validation, and existing delivery and merge boundaries; do not invent status events or bypass lifecycle scripts.

## Branches and GitHub publication

For user-requested implementation in an identified GitHub-backed project, routine creation of task branches, task commits, and ordinary pushes of those task branches to the project's configured remote are authorized without another permission question. Use the project's branch naming rules and isolated task copy. Explicit local-only instructions or narrower task restrictions still win. This does not authorize creating repositories, changing visibility or remotes, publishing unrelated work, or pushing to a protected or default branch.

Workers may create their task branch, commit the scoped changes, and push as required by the selected delivery workflow. A pipeline-owned preliminary push or PR is not manager acceptance. Keep required validation and publication under the selected workflow; do not bypass an active pipeline or its approval decisions.

The manager owns final GitHub delivery. After personally reviewing the final diff and completing the validation prerequisites for publication, ensure the exact reviewed revision is pushed to the task branch. Direct the owning worker when the selected pipeline owns the push; otherwise the manager may perform an ordinary final task-branch push itself. This is explicit narrow standing authority for task-branch creation and publication even where the general supervisor contract prohibits project state changes; it does not permit the manager to edit project code or commit worker changes itself. Preserve normal tool approval review and host-control requirements.

Before a final push, confirm the project, configured remote, task branch, and reviewed HEAD. Any later code change requires review again. Use a normal non-forced push; if it is rejected or the remote has unexpected changes, reconcile through the owning worker and re-review rather than overwrite remote work. Never force-push, delete branches, rewrite published history, or push secrets under this permission.

Verify the remote task branch contains the reviewed revision, retain the branch and commit or PR URL in the task record, and complete any required post-push checks before reporting delivery ready. If the branch is already current, verify it rather than manufacture another commit or push. A successful local commit alone is not GitHub delivery. Missing credentials or a rejected protected operation is a concrete blocker, not a reason to disable review.

Merging or pushing directly into the default branch still requires the user's explicit authorization. This publication permission does not grant merge, release, deployment, visibility-change, or unlanded-work cleanup authority.

## Size and cost

There is no fixed worker-count cap. The planner recommends task decomposition, dependencies, and useful parallel work; the manager chooses and adjusts active concurrency. Base the choice on independent ready tasks, overlapping files or components, current account quotas, machine resources, and the manager's capacity to supervise and personally review the results. Include planning and extra review workers in that assessment. Add workers when parallelism improves delivery; queue dependent or conflicting work and reduce concurrency when quota, resource, or review pressure makes it unhelpful. Briefly record the chosen concurrency and rationale in the task plan, and reassess as work changes. Keep one writer per isolated copy. Do not create secondmates or nested workers for this setup. This is an instruction policy, not an operating-system concurrency limiter.

Delegate genuinely independent work in parallel. Prefer one writer per isolated copy and short summaries between roles. Capture quota-axi's default TOON at each profile-array intake and follow the existing quota-array-dispatch contract. Model and effort are separate choices; the requested extra-high effort does not establish a price or quota guarantee. Preserve the requested reasoning class when choosing among available accounts. If no suitable route is usable, report it rather than adding paid API access or silently changing the tier.

## Accounts and tool choices

Use each native CLI's existing authentication. Use the authentication method supported by the local account and native CLI. Do not copy their tokens into another application or change account pins. Exact current models come from each CLI's own catalog and a live request, because catalog visibility does not by itself prove account access.

Cursor is excluded from automatic tiered dispatch by default. Enable a pinned route only after a live named-model probe succeeds for the local account. If the user explicitly requests Cursor Auto, disclose that the reasoning tier is not pinned. Do not silently substitute Auto for the requested worker profile. Restore pinned Cursor routes only after current account access and a live named-model probe establish that they work. No upgrade or paid overage is authorized by this setup.

The optional OpenCode helper uses official ChatGPT OAuth. Keep OpenCode outside automatic dispatch until its official OAuth login and GPT-6 Luna xhigh live probe pass. The companion enable command records success in state/opencode-verified.json and adds only a catalog-verified openai/gpt-6-luna profile with xhigh reasoning to crew-dispatch.json. Inspect current credentials and quota evidence when dispatching; a second client does not create another subscription allowance. The current Firstmate adapter maps xhigh for OpenAI-backed OpenCode models. Enable only the exact requested model and effort after its live probe passes; otherwise leave the route disabled.

Only act on user-requested tasks. The task-branch publication permission above applies only to requested work in the identified project. Project registration, other outward publication, merging, cleanup of unlanded work, and remaining authority boundaries continue to follow the normal Firstmate contracts.
