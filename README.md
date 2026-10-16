# Firstmate Swarm Config

A reusable settings preset for [Firstmate](https://github.com/kunchenguid/firstmate), using Herdr as the workspace and native coding CLIs as workers.

**High reasoning plans → a medium-reasoning manager opens fresh GitHub branches `name-worker-N` → workers may edit the same file, and the branch is the saved copy → the manager approves, requests changes, or rejects each PR → a conflict helper reads every side and resolves merge conflicts → you merge the integration branch into `main` if you want it.**

This repository contains configuration and small launch helpers. Firstmate itself is downloaded separately from upstream and lives in an ignored `home/` directory. It is not vendored here.

## Where the agents run

Herdr provides the visible workspace. The manager is a Codex session following Firstmate's instructions; Firstmate launches and supervises the planner and worker sessions through their native CLIs. The same medium-reasoning manager coordinates assignments, personally reviews every worker PR, and merges approved work into the task's integration branch. It never edits or pushes project code itself.

## Workflow

```mermaid
flowchart TD
    U["You: project + desired outcome"] --> M["Manager understands the task"]
    M --> P{"Needs planning?"}
    P -- Yes --> H["High-reasoning planner<br/>Split, shared paths allowed, dependencies, acceptance criteria"]
    H --> K
    P -- Clear existing plan --> K

    K["Manager proposes the swarm contract<br/>Integration branch name, fresh branches name-worker-N"]
    K --> OK{"You approve this task?"}
    OK -- No --> STD["Normal Firstmate delivery<br/>No extra review gate"]
    OK -- Yes --> I["Manager creates branch name from main"]

    I --> W["GPT-6 Luna workers, extra-high reasoning<br/>Each pushes name-worker-N, even on the same file<br/>The GitHub branch is the saved copy"]
    W --> R["Manager reviews the actual diff"]
    R --> Q{"Verdict comment on the PR"}
    Q -- "CHANGES REQUESTED or REJECTED, with reasons" --> W
    Q -- "APPROVED at head SHA" --> MG["Merge that PR into name<br/>One at a time, green and conflict-free"]
    MG --> X{"Does the next merge conflict?"}
    X -- Yes --> HLP["Conflict helper, gpt-6.1-sol high<br/>Reads every side, pushes name-resolve-N"]
    HLP --> R
    X -- No --> N{"All workers merged?"}
    N -- No --> R
    N -- Yes --> FPR["Manager opens PR name into main<br/>Reports it to you"]
    FPR --> Y{"You merge into main?"}
    Y -- Not yet --> WAIT["Integration branch stays ready"]
    Y -- Yes --> MERGE["You merge"]
```

A task is not a two-worker unit. The manager numbers workers `name-worker-1` through `name-worker-N`, and N is however many pieces the plan has. Workers may edit the same file or function; each one's saved copy is its own GitHub branch, not a directory on the PC. The CLI still uses a temporary checkout, and that checkout is scratch. There is no fixed worker cap. Any code change after an approval needs a new review.

## What it configures

| Role | Default profiles | Responsibility |
| --- | --- | --- |
| Planner | Codex `gpt-6.1-sol` high; Claude `sonnet` high alternative | Resolve architecture and uncertainty; return a bounded plan. |
| Manager | Codex `gpt-6.1-sol` medium | Propose the per-task swarm contract, assign workers and their paths, review every worker PR, post verdicts, merge approved PRs into the integration branch, and open the final PR into `main`. |
| Workers | Codex `gpt-6-luna`, **extra-high** (`xhigh`) | Implement small, clear tasks and run relevant checks. |
| Extra review | Claude `sonnet` medium; Codex `gpt-6-luna` medium | An additional reviewer when you ask for one or the change justifies it; the manager's own review still applies. |
| Conflict helper | Codex `gpt-6.1-sol` **high**, then **extra-high** if rejected | Reads every side of a merge conflict and pushes a fresh `<name>-resolve-N` branch. |
| Escalation | Codex `gpt-6.1-sol` **high**, then `gpt-6.1-sol` **extra-high** | When the manager rejects a worker's attempt, or the same finding survives two rounds of requested changes, the task is relaunched one step up, keeping its branch and PR. After the extra-high attempt, the manager reports to you instead of retrying. |

Model identifiers are a snapshot of the original setup, not a guarantee of availability for your account. Edit `settings/config/crew-dispatch.json` and the manager model in `swarm` for models your CLI supports; keep `settings/captain.md` and `manager-start.md` consistent with those choices. Reasoning effort and model cost are separate choices. The execution default is GPT-6 Luna xhigh for routine work too; quota pressure must not silently change the model or effort. This preset does not make a pricing or quota guarantee.

- No fixed worker-count cap: the planner recommends the task split; the manager chooses concurrency based on dependencies, current quota, machine resources, and supervision/review capacity. Workers may edit the same file on separate branches. Planning, conflict-helper, and extra review runs count toward this assessment. The manager records the rationale in the task plan and adjusts concurrency as work changes.
- One manager; no nested swarms or native Codex subagents.
- Worker reports must identify the changes and checks actually run.
- The manager reads the actual diff, posts its verdict on the PR, sends findings to the worker, and reviews every updated head before approving.
- Project validation applies, and merging into `main` stays with you.

The review loop and conflict helper are agent instructions backed by `bin/swarm-branches` checks and Firstmate's merge guards, not by repository permissions. A full swarm task has not yet been run end to end; see the checklist under Verification.

## Branches, review, and merging

Firstmate only lets a current, explicit, concrete instruction from you relax its standing rules, so the manager's authority is granted per task. At intake it proposes a contract like this and waits for your go-ahead (a task message that already says this counts):

> Task `login` in `acme/app`: I create `login` from `main` and use as many workers as the split needs. This one has three fresh branches: `login-worker-1`, `login-worker-2`, and `login-worker-3`. They may edit the same file. Each pushes only its own branch and opens a PR into `login`. I comment APPROVED, CHANGES REQUESTED, or REJECTED on each PR. If a merge conflicts, a conflict helper reads every side and pushes `login-resolve-1`. I then open a PR from `login` into `main` for you.

How the same file can be edited twice:

- **The branch is the saved copy.** Each worker's result is the GitHub branch `<name>-worker-N`, created fresh from the integration branch. The PC checkout is scratch the coding CLI needs. A worker is not done until that branch is pushed.
- **Shared edits are allowed.** `owns` in the plan file records where a worker expects to work. It may be empty, and two workers may list the same path. `bin/swarm-branches check` rejects dependency cycles and prints shared paths; it does not reject them.
- **Conflicts are a separate task.** `bin/swarm-branches conflicts` tries the merges with `git merge-tree` (no checkout) and prints every worker's edit of each conflicted file. The conflict helper is Codex `gpt-6.1-sol` at high reasoning. It keeps each intended behavior, pushes a fresh `<name>-resolve-N` branch, and opens a PR into the integration branch. The manager reviews that PR and does not edit it. A rejected resolution is relaunched at `gpt-6.1-sol` extra-high.
- **One merge at a time.** Clean merges go through Firstmate's `bin/fm-pr-merge.sh`, which refuses unless the PR is mergeable, conflict-free, and green at its exact head. Workers do not resolve each other's conflicts, rebase a pushed branch, or force-push.

All agents share your GitHub login, and GitHub does not let an account approve or request changes on its own pull request, so verdicts are PR comments (`Manager review: APPROVED at <sha>`) rather than formal reviews. For the same reason GitHub cannot tell the agents' merges from yours: a branch rule on `main` that requires a pull request stops direct pushes, but only a separate GitHub account for the swarm, plus a rule requiring your approval on `main`, enforces that only you merge into it.

The manager never edits, commits, or pushes project code. It creates the integration branch, comments, merges approved worker PRs into that branch, and opens the final PR. Force pushes, branch deletion, remote or visibility changes, releases, deployments, and anything into `main` are outside the contract. If you decline the contract, or the task must ship through Firstmate's `no-mistakes` pipeline, Firstmate delivers it the normal way without the extra review gate.

## Requirements

This preset targets Linux with Bash, Git, Python 3 (`python3`), `flock`, `jq`, and `readlink -f`.

Install Firstmate's prerequisites and these CLIs separately:

- `herdr`, `codex`, `claude`
- `quota-axi`, `treehouse`, `tasks-axi`
- `gh` and `gh-axi`, signed in to the GitHub account the swarm should use
- `cursor-agent` or `opencode` only if you add a route that uses them

`./swarm --check` names every missing command and setup step at once. It also checks that `home/` is at the pinned Firstmate commit; set `SWARM_ALLOW_UNPINNED=1` only after reviewing upstream's changes.

Authenticate the native CLIs you intend to use. No credentials, tokens, task history, project files, or running-session records are included. A subscription or login in one CLI does not create access or additional allowance in another.

The manager runs Firstmate's process and Herdr control commands through Codex's host-context escalation. Read [Security posture](#security-posture) for who approves those commands and how workers run.

## Security posture

Nothing in this preset runs workers in a sandbox. Know what each agent can do before pointing it at a real repository:

| Agent | How it runs | Who approves its commands |
| --- | --- | --- |
| Manager (Codex) | Codex workspace-write sandbox; Firstmate control scripts run in the host context through escalation | Default `SWARM_MANAGER_APPROVAL=auto`: Codex's automatic reviewer (`--approve-for-me`). `manual`: you, through your Codex approval policy. |
| Codex workers | Firstmate launches them with `--dangerously-bypass-approvals-and-sandbox` | Nobody; no sandbox |
| OpenCode workers (when enabled) | Firstmate launches them with every permission set to allow | Nobody |
| Claude workers | `--permission-mode auto`, set by this preset's `claude-permission-mode` | Claude Code's permission classifier |

Choose the manager mode when you start the workspace, for example `SWARM_MANAGER_APPROVAL=manual ./swarm`. The launcher records it in `home/state/` and prints it when the manager starts; it applies from the next manager launch.

Workers run unsandboxed in their own worktrees with your GitHub login, so this preset's limits on pushing and merging are instructions, not enforcement. Before using it on a real repository:

- Protect `main` on GitHub with a rule that requires a pull request, so nothing is pushed to it directly. Because the agents use your login, that rule does not stop them merging; run the swarm under a separate GitHub account and require your approval on `main` if you need that enforced.
- Prefer a GitHub credential limited to the repositories the swarm works on.
- Keep unrelated secrets out of the workers' environment; Firstmate's `config/launch-env-allowlist` limits what new workers inherit.

## Set up a fresh instance

```sh
git clone https://github.com/bobbyKhandar/firstmate-swarm-config.git
cd firstmate-swarm-config

git clone https://github.com/kunchenguid/firstmate.git home
git -C home checkout 42dd906d02f672652606057a193a6386b956c3f3
mkdir -p home/config home/data home/state
cp -a settings/config/. home/config/
cp settings/captain.md home/data/captain.md
chmod +x swarm bin/herdr-shell bin/*.py bin/swarm-branches

./swarm --check
./swarm
```

The source commit pins the Firstmate version used for this preset. Review upstream migration guidance before using a newer version. Use a fresh `home/`; do not overwrite a home with active work.

The launcher opens the persistent Herdr session `firstmate-tiered` and starts one manager. Run `./swarm` again to reconnect. If another instance uses that session name, choose a different name in `swarm` first. Tell the manager which repository to work on and the outcome you want; it begins with an empty task queue.

### Optional OpenCode route

OpenCode stays out of automatic routing with the pinned Firstmate. Its bootstrap reports any OpenCode profile that sets an effort as an invalid `crew-dispatch.json` (`crew_dispatch_validate` in `bin/fm-bootstrap.sh`), and a profile without an effort would not run at `xhigh`. Upstream `main` still behaves this way. `./swarm --connect-opencode` therefore refuses before starting any login.

Once you use a Firstmate version whose bootstrap accepts OpenCode efforts, enable it with:

```sh
SWARM_OPENCODE_FORCE=1 ./swarm --connect-opencode
```

This uses the local OpenCode credential store. It does not copy credentials from Codex. The helper considers only the exact `openai/gpt-6-luna` model, probes it at `xhigh` through the same agent `variant` setting Firstmate's worker launch uses, and leaves routing disabled if the probe fails. Account access and shared allowance still apply. After successful verification it adds the OpenCode profile next to every Codex `gpt-6-luna` `xhigh` profile in the active `home/config/crew-dispatch.json`, not the committed template.

Cursor is excluded from automatic routing by default. Add a route only after verifying account access to a named model and the requested reasoning tier. Auto does not provide a pinned reasoning tier.

## Files and customization

| Path | Purpose |
| --- | --- |
| `settings/config/crew-dispatch.json` | Task-to-model routing rules. |
| `settings/captain.md` | Manager role, cost policy, and assignment/review loop. |
| `settings/config/brief-include.md` | Standing worker scope and handoff instructions. |
| `manager-start.md` | Manager startup instructions. |
| `swarm` | Workspace and medium-reasoning manager launcher. |
| `bin/herdr-shell` | Starts the manager in the initial workspace pane. |
| `bin/enable-opencode.py` | Optional OAuth check and live probe before enabling OpenCode. |
| `manifest.json` | Source version and hashes of distributed files. |
| `bin/manifest.py` | Checks `manifest.json` against the tracked files, or regenerates it. |
| `bin/swarm-branches` | Creates the plan and integration branch, allows shared paths, and prints every side of a merge conflict. |
| `bin/check-setup.py` | The configuration, pin, and route checks behind `./swarm --check`. |
| `tests/run.sh` | Fixture tests with stub CLIs; set `UPSTREAM_BOOTSTRAP` to a pinned `bin/fm-bootstrap.sh` to also run Firstmate's own dispatch validator. |
| `.github/workflows/ci.yml` | Runs ShellCheck, the Python compile check, the manifest check, and the fixture tests on every push. |

Settings are copied into `home/` during setup. Changes later made there are ignored by Git: copy intended, sanitized changes back into `settings/` before committing them. Review model and account claims for your machine before dispatching work.

After changing any tracked file, stage it and run `python3 bin/manifest.py update`, then commit `manifest.json` with the change. `python3 bin/manifest.py check` reports any file whose hash no longer matches.

Firstmate remains a separate upstream project with its own license and update process. This repository does not automatically update it or install dependencies.

## Verification

CI runs ShellCheck, a Python compile check, `python3 bin/manifest.py check`, and `bash tests/run.sh`, which exercises the launcher, `--check`, the manager approval switch, the OpenCode helper, and `bin/swarm-branches` against stub CLIs, and validates the dispatch file with the pinned Firstmate's own validator. Run the same tests locally with `bash tests/run.sh`. These checks do not establish a complete project workflow or every account's access to the configured models.

Before relying on the swarm workflow, run one small task that uses several workers, not a pair, in a test repository and confirm each step:

1. The manager proposes a swarm contract and waits for your go-ahead.
2. `home/data/swarm/<name>.json` exists and `bin/swarm-branches check` passes on it.
3. The integration branch appears on GitHub, created from `main`.
4. Each worker pushes `<name>-worker-N` and opens its PR into the integration branch, not `main`.
5. The manager posts a `Manager review:` verdict on each PR; a `CHANGES REQUESTED` round produces new commits and a new review.
6. Approved PRs merge one at a time into the integration branch. A conflicting merge is given to the conflict helper, which pushes `<name>-resolve-N` after reading every side.
7. The manager opens a PR from the integration branch into `main`, reports it, and does not merge it.
8. Nothing was force-pushed, and nothing landed on `main` without you.

## License

The configuration and launch helpers in this repository are available under the MIT license. Firstmate and the native CLI tools retain their own licenses.
