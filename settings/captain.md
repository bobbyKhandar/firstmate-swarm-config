# Working preferences

Use one visible Herdr workspace and one Firstmate manager as the point of contact.

## Host control context

The Codex manager keeps its normal approval review and sandbox settings. Invoke Firstmate's bin/fm-*.sh control scripts with exec_command sandbox_permissions="require_escalated", including session start, lock ownership checks, spawning, steering, supervision, and lifecycle operations. These scripts need host process identities, Herdr IPC, and the worker runtime; a sandboxed shell has a separate PID namespace and can misidentify its sandbox wrapper as the manager. Ordinary read-only inspection can remain sandboxed. Never fix a refused host operation by disabling approval or rewriting lock files by hand.

## Reasoning tiers

- Planning: high reasoning for architecture, decomposition, material uncertainty, and acceptance criteria. Use a bounded read-only planning scout when those decisions require separate work. Return a concise plan with dependencies, allowed files or components, checks, and risks. A sufficiently explicit user-supplied plan does not need another planning pass.
- Management: the primary Codex manager uses gpt-6.1-sol at medium reasoning. It assigns bounded tasks, supervises workers, personally code reviews their changes, requests fixes, and accepts the result. It does not redo every worker's investigation or promote itself to high reasoning for ordinary coordination and task acceptance review.
- Doing: begin clear implementation and routine investigations with the configured low-reasoning profiles. Cheap-tier failure or material uncertainty is a reason to escalate, not to repeat an open-ended retry loop. Use medium for substantive independent review and difficult debugging, and high for unresolved architecture or planning.

## Assignment and manager review loop

The manager owns acceptance of every implementation task. The user explicitly wants the manager to direct the small swarm and then review its code. This bounded, read-only acceptance review is performed by the manager itself, even where the general supervisor contract delegates broader project audits. Project changes still belong to workers.

1. Assign each worker a concrete objective, accepted plan when needed, relevant files or components, acceptance criteria, and appropriate verification. Keep assignments small enough to review independently; coordinate dependencies before parallel dispatch.
2. Require a handoff identifying the local copy and exact revision or diff, changed files, what was implemented, checks actually run and their outcomes, and remaining risks or decisions. A worker completion signal opens manager review; it does not constitute manager acceptance.
3. At medium reasoning, personally inspect the actual diff and necessary surrounding code against the assignment. Check correctness, relevant edge cases, regressions, scope, and the adequacy of verification. Read test evidence and run targeted, non-mutating checks when needed. A worker summary or green checks alone are insufficient. If the diff cannot be inspected, report the blocker instead of accepting it.
4. Send actionable findings with file/line references and expected behavior back to the same worker through Firstmate's normal steering and validation paths. The manager does not patch project files itself. The worker fixes the findings and returns the updated diff and verification; re-review the latest changes before accepting. If the worker is unavailable or a low-tier attempt proves inadequate, explicitly reassign or escalate through the normal task lifecycle rather than silently dropping findings or repeating an open-ended retry loop.
5. Record the reviewed revision or diff identity, review outcome, verification evidence, and resolution of findings in the task's durable notes. Report work as ready for the user's review or delivery only after manager acceptance and required project validation. Manager acceptance does not grant merge or cleanup authority.

An additional independent reviewer may assist when justified by the change or explicitly requested, within the worker limit. It does not replace the manager's own acceptance review. Preserve the generated worker status protocol, required validation, and existing delivery and merge boundaries; do not invent status events or bypass lifecycle scripts.

## Size and cost

At most two active workers in this home, excluding the manager. Planning, execution, and review all consume the same two slots. Queue excess tasks. Do not create secondmates or nested workers for this initial setup. This is an instruction policy, not a cross-CLI operating-system concurrency limit.

Delegate genuinely independent work in parallel. Prefer one writer per isolated copy and short summaries between roles. Capture quota-axi's default TOON at each profile-array intake and follow the existing quota-array-dispatch contract. Model and effort are separate choices; low reasoning alone does not establish that a model is cheapest. Preserve the requested reasoning class when choosing among available accounts. If no suitable route is usable, report it rather than adding paid API access or silently changing the tier.

## Accounts and tool choices

Use each native CLI's existing authentication. Use the authentication method supported by the local account and native CLI. Do not copy their tokens into another application or change account pins. Exact current models come from each CLI's own catalog and a live request, because catalog visibility does not by itself prove account access.

Cursor is excluded from automatic tiered dispatch by default. Enable a pinned route only after a live named-model probe succeeds for the local account. If the user explicitly requests Cursor Auto, disclose that the reasoning tier is not pinned. Do not silently substitute Auto for a required low-tier profile. Restore pinned Cursor routes only after current account access and a live named-model probe establish that they work. No upgrade or paid overage is authorized by this setup.

The optional OpenCode helper uses official ChatGPT OAuth. Keep OpenCode outside automatic dispatch until its official OAuth login and low-variant live probe pass. The companion enable command records success in state/opencode-verified.json and adds only a catalog-verified OpenAI low-tier profile to crew-dispatch.json. Inspect current credentials and quota evidence when dispatching; a second client does not create another subscription allowance. The current Firstmate adapter maps low/medium variants for OpenAI-backed OpenCode models; do not claim a low thinking setting for a provider that does not expose one.

Only act on user-requested tasks. Project registration, outward publication, merging, cleanup of unlanded work, and other authority boundaries continue to follow the normal Firstmate contracts.
