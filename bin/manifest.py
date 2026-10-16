#!/usr/bin/env python3
"""Check or regenerate manifest.json hashes for every tracked file."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
manifest_path = root / "manifest.json"


def tracked_files():
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True, check=True,
    )
    names = [name for name in result.stdout.decode().split("\0") if name]
    return sorted(name for name in names if name != "manifest.json")


def digest(name):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()


def check(manifest):
    recorded = manifest["files"]
    problems = []
    for name in tracked_files():
        if name not in recorded:
            problems.append(f"not in manifest: {name}")
        elif not (root / name).is_file():
            problems.append(f"missing file: {name}")
        elif digest(name) != recorded[name]:
            problems.append(f"hash mismatch: {name}")
    for name in sorted(set(recorded) - set(tracked_files())):
        problems.append(f"listed but not tracked: {name}")
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print("Run: python3 bin/manifest.py update", file=sys.stderr)
        return 1
    print(f"Manifest matches {len(recorded)} tracked files.")
    return 0


def update(manifest):
    manifest["files"] = {name: digest(name) for name in tracked_files()}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Manifest updated for {len(manifest['files'])} tracked files.")
    return 0


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", choices=["check", "update"])
args = parser.parse_args()
manifest = json.loads(manifest_path.read_text())
sys.exit(check(manifest) if args.command == "check" else update(manifest))
