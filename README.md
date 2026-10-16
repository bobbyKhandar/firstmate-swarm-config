# Firstmate Swarm Config

A reusable settings preset for [Firstmate](https://github.com/kunchenguid/firstmate), using Herdr as the workspace and native coding CLIs as workers.

**High reasoning plans → a medium-reasoning manager splits the task into workers with exclusive file ownership → each GPT-6 Luna extra-high worker pushes its own branch and opens a PR → the manager approves, requests changes, or rejects on the PR → approved PRs merge one at a time into the task's integration branch → you merge that branch into `main` if you want it.**

This repository contains configuration and small launch helpers. Firstmate itself is downloaded separately from upstream and lives in an ignored `home/` directory. It is not vendored here.

## Where the agents run

Herdr provides the visible workspace. The manager is a Codex session following Firstmate's instructions; Firstmate launches and supervises the planner and worker sessions through their native CLIs. The same medium-reasoning manager coordinates assignments, personally reviews every worker PR, and merges approved work into the task's integration branch. It never edits or pushes project code itself.

## Workflow

```mermaid
flowchart TD
    U["You: project + desired outcome"] --> M["Manager understands the task"]
    M --> P{"Needs planning?"}
    P -- Yes --> H["High-reasoning planner<br/>Split, owned paths, dependencies, acceptance criteria"]
    H --> K
    P -- Clear existing plan --> K

    K["Manager proposes the swarm contract<br/>Integration branch name, workers name-worker-N, owned paths"]
    K --> OK{"You approve this task?"}
    OK -- No --> STD["Normal Firstmate delivery<br/>No extra review gate"]
    OK -- Yes --> I["Manager creates branch name from main"]

    I --> W["GPT-6 Luna workers, extra-high reasoning<br/>Each on name-worker-N, only its own paths<br/>Implement, run checks, push, open PR into name"]
    W --> B["Boundary check<br/>Changes outside the worker's paths are findings"]
    B --> R["Manager reviews the actual diff"]
    R --> Q{"Verdict comment on the PR"}
    Q -- "CHANGES REQUESTED or REJECTED, with reasons" --> W
    Q -- "APPROVED at head SHA" --> MG["Merge that PR into name<br/>One at a time, green and conflict-free"]
    MG --> X{"Other open PRs now conflict?"}
    X -- Yes --> SYNC["Owning worker merges name into its branch<br/>Manager reviews again"]
    SYNC --> R
    X -- No --> N{"All workers merged?"}
    N -- No --> R
    N -- Yes --> FPR["Manager opens PR name into main<br/>Reports it to you"]
    FPR --> Y{"You merge into main?"}
    Y -- Not yet --> WAIT["Integration branch stays ready"]
    Y -- Yes --> MERGE["You merge"]
```

A task is not a two-worker unit. The manager numbers workers `name-worker-1` through `name-worker-N`, and N is however many independent pieces the plan has. The planner recommends that split; the manager adjusts how many of those workers run at once based on dependencies, quota, machine resources, and review capacity. There is no fixed worker cap. Any code change after an approval needs a new review.
