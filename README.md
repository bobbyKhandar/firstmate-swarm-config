# Firstmate Swarm Config

A reusable settings preset for [Firstmate](https://github.com/kunchenguid/firstmate), using Herdr as the workspace and native coding CLIs as workers.

**High reasoning plans → a medium-reasoning manager splits the task into workers with exclusive file ownership → each GPT-6 Luna extra-high worker pushes its own branch and opens a PR → the manager approves, requests changes, or rejects on the PR → approved PRs merge one at a time into the task's integration branch → you merge that branch into `main` if you want it.**

This repository contains configuration and small launch helpers. Firstmate itself is downloaded separately from upstream and lives in an ignored `home/` directory. It is not vendored here.
