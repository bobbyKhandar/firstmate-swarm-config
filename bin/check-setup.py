#!/usr/bin/env python3
"""Validate a swarm home before launch; print every problem found."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

swarm_dir, home, code_root = (Path(arg) for arg in sys.argv[1:4])
problems = []
setup_hint = "Follow \"Set up a fresh instance\" in README.md."

# Mirrors effort_ok in the pinned Firstmate's crew_dispatch_validate
# (bin/fm-bootstrap.sh) for the harnesses this preset routes to.
EFFORTS = {
    "codex": {"low", "medium", "high", "xhigh"},
    "claude": {"low", "medium", "high", "xhigh", "max"},
    "cursor": set(),
    "opencode": set(),
}
if os.environ.get("SWARM_OPENCODE_FORCE") == "1":
    EFFORTS["opencode"] = {"low", "medium", "high", "xhigh"}
CLIS = {"cursor": "cursor-agent", "opencode": "opencode"}


def profiles(value, where):
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
        return value
    problems.append(f"crew-dispatch.json: {where} must be a profile object or a non-empty list of them")
    return []


def check_profile(profile, where):
    harness = profile.get("harness")
    if harness not in EFFORTS:
        problems.append(f"crew-dispatch.json: {where} uses harness {harness!r}; expected one of {', '.join(sorted(EFFORTS))}")
        return None
    effort = profile.get("effort")
    if effort is None:
        return harness
    if harness == "codex" and effort == "max" and profile.get("model") == "gpt-5.6-luna":
        return harness
    if effort not in EFFORTS[harness]:
        reason = "Firstmate rejects an effort on this harness" if not EFFORTS[harness] else \
            f"allowed: {', '.join(sorted(EFFORTS[harness]))}"
        if harness == "opencode":
            reason += "; see \"Optional OpenCode route\" in README.md"
        problems.append(f"crew-dispatch.json: {where} sets {harness} effort {effort!r} ({reason})")
    return harness


dispatch_path = home / "config/crew-dispatch.json"
used = set()
if not dispatch_path.is_file():
    problems.append(f"Missing {dispatch_path}. Copy the settings: cp -a settings/config/. home/config/")
else:
    try:
        dispatch = json.loads(dispatch_path.read_text())
    except ValueError as error:
        problems.append(f"crew-dispatch.json is not valid JSON: {error}")
        dispatch = None
    if isinstance(dispatch, dict) and not isinstance(dispatch.get("rules", []), list):
        problems.append("crew-dispatch.json: rules must be a list")
    elif isinstance(dispatch, dict):
        for index, rule in enumerate(dispatch.get("rules", []), 1):
            for profile in profiles(rule.get("use") if isinstance(rule, dict) else None, f"rule {index} use"):
                used.add(check_profile(profile, f"rule {index}"))
        if "default" in dispatch:
            for profile in profiles(dispatch["default"], "default"):
                used.add(check_profile(profile, "default"))
    elif dispatch is not None:
        problems.append("crew-dispatch.json must contain a JSON object")

for harness, cli in CLIS.items():
    if harness in used and shutil.which(cli) is None:
        problems.append(f"Missing command: {cli} (crew-dispatch.json routes work to {harness})")

backend_path = home / "config/backend"
if not backend_path.is_file():
    problems.append(f"Missing {backend_path}. Copy the settings: cp -a settings/config/. home/config/")
elif backend_path.read_text().strip() != "herdr":
    problems.append(f"{backend_path} must contain herdr")

if not (home / "data/captain.md").is_file():
    problems.append(f"Missing {home / 'data/captain.md'}. Copy it: cp settings/captain.md home/data/captain.md")

pinned = json.loads((swarm_dir / "manifest.json").read_text())["source_commit"]
top = subprocess.run(["git", "-C", str(code_root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
head = subprocess.run(["git", "-C", str(code_root), "rev-parse", "HEAD"], capture_output=True, text=True)
if top.returncode or head.returncode or Path(top.stdout.strip()).resolve() != code_root.resolve():
    problems.append(f"{code_root} is not a Git checkout of Firstmate. {setup_hint}")
elif head.stdout.strip() != pinned and os.environ.get("SWARM_ALLOW_UNPINNED") != "1":
    problems.append(f"Firstmate in {code_root} is at {head.stdout.strip()[:12]}, not the pinned {pinned[:12]}. "
                    f"Run: git -C {code_root} checkout {pinned} (or set SWARM_ALLOW_UNPINNED=1 after reviewing upstream changes)")

for problem in problems:
    print(problem, file=sys.stderr)
if problems:
    sys.exit(1)
print("Configuration valid: high planning, medium management, GPT-6 Luna xhigh execution.")
