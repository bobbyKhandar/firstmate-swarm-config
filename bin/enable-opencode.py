#!/usr/bin/env python3
"""Enable an OpenCode GPT-6 Luna xhigh route only after OAuth and a live probe succeed."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent.parent
home = root / "home"
EXECUTION = {"harness": "codex", "model": "gpt-6-luna", "effort": "xhigh"}

# The pinned Firstmate's bootstrap (crew_dispatch_validate in bin/fm-bootstrap.sh)
# reports every OpenCode profile that sets an effort as invalid, and a profile
# without one would not launch at xhigh.
if os.environ.get("SWARM_OPENCODE_FORCE") != "1":
    sys.exit("OpenCode routing stays disabled: the pinned Firstmate rejects any OpenCode profile that sets an effort, "
             "and without one the route would not run at xhigh. Set SWARM_OPENCODE_FORCE=1 only with a Firstmate "
             "version whose bootstrap accepts OpenCode efforts.")
if "--preflight" in sys.argv[1:]:
    sys.exit(0)

data_home = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
auth_path = data_home / "opencode/auth.json"
auth = json.loads(auth_path.read_text()) if auth_path.exists() else {}
if auth.get("openai", {}).get("type") != "oauth":
    sys.exit("OpenCode ChatGPT sign-in is pending. Run ./swarm --connect-opencode.")

try:
    result = subprocess.run(
        ["opencode", "models", "openai", "--pure"],
        text=True, capture_output=True, check=True, timeout=45,
    )
    catalog = set(re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", result.stdout).splitlines())
    model = next((item for item in (
        "openai/gpt-6-luna",
    ) if item in catalog), None)
    if model is None:
        sys.exit("The requested openai/gpt-6-luna model was not returned by OpenCode. Automatic routing remains disabled.")
    # Firstmate's worker launch passes the effort as the agent's configured variant
    # in OPENCODE_CONFIG_CONTENT, not as `opencode run --variant`, so probe that path.
    probe_config = {"agent": {"plan": {"model": model, "variant": "xhigh"}}}
    with tempfile.TemporaryDirectory(prefix="opencode-probe-", dir=home / "state") as scratch:
        probe = subprocess.run(
            ["opencode", "run", "--pure", "--format", "json", "--agent", "plan",
             "--model", model, "Reply exactly SWARM_OK. Do not use tools."],
            cwd=scratch, text=True, capture_output=True, timeout=90,
            env={**os.environ, "OPENCODE_CONFIG_CONTENT": json.dumps(probe_config)},
        )
    events = []
    for line in probe.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    errors = [event for event in events if event.get("type") == "error"]
    replies = [event.get("part", {}).get("text", "")
               for event in events if event.get("type") == "text"]
    if probe.returncode or errors or "".join(replies).strip() != "SWARM_OK":
        sys.exit("OpenCode's GPT-6 Luna xhigh live probe did not pass. Automatic routing remains disabled; no credentials were changed.")
except (subprocess.SubprocessError, OSError) as error:
    sys.exit(f"OpenCode verification could not finish ({type(error).__name__}). Automatic routing remains disabled.")

path = home / "config/crew-dispatch.json"
dispatch = json.loads(path.read_text())
profile = {"harness": "opencode", "model": model, "effort": "xhigh"}
for holder, key in [*((rule, "use") for rule in dispatch.get("rules", [])), (dispatch, "default")]:
    if isinstance(holder.get(key), dict):
        holder[key] = [holder[key]]
groups = [rule["use"] for rule in dispatch.get("rules", []) if EXECUTION in rule["use"]]
if EXECUTION in dispatch.get("default", []):
    groups.append(dispatch["default"])
if not groups:
    sys.exit(f"No dispatch rule in {path} uses the Codex gpt-6-luna xhigh execution profile; nothing was changed.")
for group in groups:
    group[:] = [candidate for candidate in group if candidate["harness"] != "opencode"]
    group.append(profile)
temporary = path.with_suffix(".json.tmp")
temporary.write_text(json.dumps(dispatch, indent=2) + "\n")
temporary.replace(path)
(home / "state/opencode-verified.json").write_text(json.dumps({
    "model": model, "effort": "xhigh", "auth": "ChatGPT OAuth", "probe": "SWARM_OK",
}, indent=2) + "\n")
print(f"OpenCode enabled: {model}, extra-high reasoning. It uses the connected ChatGPT allowance.")
