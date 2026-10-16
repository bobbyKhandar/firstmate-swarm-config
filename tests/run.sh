#!/usr/bin/env bash
# shellcheck disable=SC2016 # check and bash -c take single-quoted code that runs later
# Fixture tests for the launcher, setup check, OpenCode helper, branch helper,
# and manifest. Native CLIs are stubs on a restricted PATH, so nothing here
# needs Herdr, Codex, Claude, OpenCode, GitHub, or network access.
# Set UPSTREAM_BOOTSTRAP to a pinned bin/fm-bootstrap.sh to also validate the
# committed dispatch file with Firstmate's own validator.
set -uo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
PASSED=0
FAILED=0

SYSBIN="$WORK/sysbin"
STUBS="$WORK/stubs"
mkdir -p "$SYSBIN" "$STUBS"
for tool in bash sh python3 git flock jq dirname readlink cat mkdir grep rm cp ls mktemp sed tr env xargs chmod cmp; do
  ln -s "$(command -v "$tool")" "$SYSBIN/$tool"
done
for tool in herdr claude quota-axi treehouse tasks-axi gh-axi; do
  printf '#!/bin/sh\nexit 0\n' > "$STUBS/$tool"
done
cat > "$STUBS/codex" <<'EOF'
#!/bin/sh
printf 'codex' > "$CODEX_LOG"
for arg in "$@"; do printf ' %s' "$arg" >> "$CODEX_LOG"; done
EOF
cat > "$STUBS/gh" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "$GH_LOG"
case "$*" in
  *"-X POST"*) exit 0 ;;
  *"/git/ref/heads/main "*) echo 0123456789abcdef0123456789abcdef01234567 ;;
  *) [ "${GH_EXISTING:-0}" = 1 ] && { echo fedcba9876543210fedcba9876543210fedcba98; exit 0; }; exit 1 ;;
esac
EOF
cat > "$STUBS/opencode" <<'EOF'
#!/bin/sh
printf '%s\n' "$*" >> "$OPENCODE_LOG"
case "$1" in
  models) echo openai/gpt-6-luna ;;
  run)
    for arg in "$@"; do [ "$arg" = --variant ] && exit 1; done
    printf '%s' "$OPENCODE_CONFIG_CONTENT" | grep -q '"variant": "xhigh"' || exit 1
    echo '{"type":"text","part":{"text":"SWARM_OK"}}' ;;
esac
EOF
chmod +x "$STUBS"/*
mkdir -p "$WORK/nostubs"
cp -a "$STUBS/opencode" "$WORK/nostubs/opencode"
export CODEX_LOG="$WORK/codex.log" GH_LOG="$WORK/gh.log" OPENCODE_LOG="$WORK/opencode.log"
export PATH="$STUBS:$SYSBIN" HOME="$WORK/user" XDG_DATA_HOME="$WORK/user/.local/share"
unset SWARM_MANAGER_APPROVAL SWARM_OPENCODE_FORCE SWARM_ALLOW_UNPINNED HERDR_ENV FM_SWARM_CODE_ROOT
mkdir -p "$XDG_DATA_HOME/opencode"
echo '{"openai":{"type":"oauth"}}' > "$XDG_DATA_HOME/opencode/auth.json"

report() {
  if [[ "$1" == ok ]]; then
    PASSED=$((PASSED + 1))
    printf 'ok   %s\n' "$2"
  else
    FAILED=$((FAILED + 1))
    printf 'FAIL %s\n' "$2"
    [[ -z "${3:-}" ]] || printf '%s\n' "$3" | sed 's/^/     /'
  fi
}

# expect NAME EXIT SUBSTRING COMMAND...: the command exits EXIT and prints SUBSTRING.
expect() {
  local name=$1 want=$2 needle=$3 out status
  shift 3
  out=$("$@" 2>&1)
  status=$?
  if [[ "$status" == "$want" && "$out" == *"$needle"* ]]; then
    report ok "$name"
  else
    report fail "$name" "exit $status (wanted $want), output:"$'\n'"$out"
  fi
}

check() {
  if eval "$2"; then report ok "$1"; else report fail "$1" "condition failed: $2"; fi
}

# fixture NAME [settings] [firstmate]: a fresh copy of the tracked files.
fixture() {
  local dir="$WORK/$1"
  mkdir -p "$dir"
  git -C "$ROOT" ls-files -z | (cd "$ROOT" && xargs -0 cp --parents -t "$dir") 2>/dev/null \
    || (cd "$ROOT" && git ls-files | while read -r file; do mkdir -p "$dir/$(dirname "$file")"; cp -p "$file" "$dir/$file"; done)
  chmod +x "$dir/swarm" "$dir/bin/herdr-shell"
  shift
  for part in "$@"; do
    case "$part" in
      firstmate)
        mkdir -p "$dir/home/bin" "$dir/home/state"
        printf '#!/bin/sh\n' > "$dir/home/bin/fm-spawn.sh"
        chmod +x "$dir/home/bin/fm-spawn.sh"
        git -C "$dir/home" init -q
        git -C "$dir/home" -c user.email=t@example.com -c user.name=t commit -q --allow-empty -m firstmate
        ;;
      settings)
        mkdir -p "$dir/home/config" "$dir/home/data" "$dir/home/state"
        cp -a "$dir/settings/config/." "$dir/home/config/"
        cp "$dir/settings/captain.md" "$dir/home/data/captain.md"
        ;;
    esac
  done
  printf '%s\n' "$dir"
}

edit_dispatch() {
  python3 - "$1/home/config/crew-dispatch.json" "$2" <<'PY'
import json, sys
path = sys.argv[1]
dispatch = json.load(open(path))
exec(sys.argv[2])
json.dump(dispatch, open(path, "w"), indent=2)
PY
}

echo "# swarm --check"
dir=$(fixture check-missing)
expect "reports missing commands together" 1 "Missing commands: herdr" env PATH="$SYSBIN" "$dir/swarm" --check
expect "names every missing command" 1 "codex claude quota-axi treehouse tasks-axi gh gh-axi" env PATH="$SYSBIN" "$dir/swarm" --check
expect "explains a missing Firstmate clone" 1 "Firstmate is not installed in $dir/home" "$dir/swarm" --check

dir=$(fixture check-settings firstmate)
expect "explains missing settings" 1 "cp -a settings/config/. home/config/" env SWARM_ALLOW_UNPINNED=1 "$dir/swarm" --check
expect "explains missing captain.md" 1 "cp settings/captain.md home/data/captain.md" env SWARM_ALLOW_UNPINNED=1 "$dir/swarm" --check

dir=$(fixture check-pin firstmate settings)
expect "refuses an unpinned Firstmate" 1 "not the pinned 42dd906d02f6" "$dir/swarm" --check
expect "accepts a reviewed unpinned Firstmate" 0 "Configuration valid" env SWARM_ALLOW_UNPINNED=1 "$dir/swarm" --check

dir=$(fixture check-nested settings)
mkdir -p "$dir/home/bin" && printf '#!/bin/sh\n' > "$dir/home/bin/fm-spawn.sh" && chmod +x "$dir/home/bin/fm-spawn.sh"
git -C "$dir" init -q && git -C "$dir" -c user.email=t@example.com -c user.name=t commit -q --allow-empty -m preset
expect "does not mistake the preset checkout for Firstmate" 1 "is not a Git checkout of Firstmate" "$dir/swarm" --check

dir=$(fixture check-routes firstmate settings)
edit_dispatch "$dir" 'dispatch["default"].append({"harness": "opencode", "model": "openai/gpt-6-luna", "effort": "xhigh"})'
expect "rejects an OpenCode effort like Firstmate does" 1 "sets opencode effort 'xhigh'" env SWARM_ALLOW_UNPINNED=1 "$dir/swarm" --check
edit_dispatch "$dir" 'dispatch["default"] = [{"harness": "codex", "model": "gpt-6-luna", "effort": "xhigh"}]; dispatch["rules"][0]["use"].append({"harness": "cursor", "model": "composer"})'
expect "requires cursor-agent only for a cursor route" 1 "Missing command: cursor-agent" env SWARM_ALLOW_UNPINNED=1 "$dir/swarm" --check
edit_dispatch "$dir" 'dispatch["rules"][0]["use"][0]["effort"] = "turbo"'
expect "rejects an unknown effort" 1 "sets codex effort 'turbo'" env SWARM_ALLOW_UNPINNED=1 "$dir/swarm" --check

echo "# manager launch"
dir=$(fixture manager firstmate settings)
export SWARM_ALLOW_UNPINNED=1
expect "refuses outside Herdr" 1 "Start the workspace with" "$dir/swarm" --manager
expect "defaults to automatic approval review" 0 "automatic review" env HERDR_ENV=1 "$dir/swarm" --manager
check "passes --approve-for-me by default" 'grep -q -- "--approve-for-me" "$CODEX_LOG"'
check "disables native Codex subagents" 'grep -q "features.multi_agent=false" "$CODEX_LOG"'
expect "manual mode skips automatic review" 0 "manual" env HERDR_ENV=1 SWARM_MANAGER_APPROVAL=manual "$dir/swarm" --manager
check "manual mode omits --approve-for-me" '! grep -q -- "--approve-for-me" "$CODEX_LOG"'
expect "remembers the recorded mode" 0 "manual" env HERDR_ENV=1 "$dir/swarm" --manager
expect "rejects an unknown approval mode" 2 "must be auto or manual" env HERDR_ENV=1 SWARM_MANAGER_APPROVAL=yes "$dir/swarm" --manager
expect "top-level launch records the mode" 0 "" env SWARM_MANAGER_APPROVAL=auto "$dir/swarm"
check "recorded mode is auto" '[[ $(cat "$dir/home/state/.swarm-manager-approval") == auto ]]'
unset SWARM_ALLOW_UNPINNED

echo "# OpenCode helper"
dir=$(fixture opencode firstmate settings)
cp "$dir/home/config/crew-dispatch.json" "$WORK/dispatch-before.json"
: > "$OPENCODE_LOG"
expect "connect refuses at the pinned Firstmate" 1 "OpenCode routing stays disabled" "$dir/swarm" --connect-opencode
check "connect never starts a login" '[[ ! -s "$OPENCODE_LOG" ]]'
check "connect leaves the dispatch file alone" 'cmp -s "$WORK/dispatch-before.json" "$dir/home/config/crew-dispatch.json"'
edit_dispatch "$dir" 'dispatch["rules"].reverse(); dispatch["default"] = dispatch["default"][0]'
expect "forced helper enables the route" 0 "OpenCode enabled" env SWARM_OPENCODE_FORCE=1 python3 "$dir/bin/enable-opencode.py"
check "probe passes xhigh through the agent config" 'grep -q "^run " "$OPENCODE_LOG" && ! grep -q -- "--variant" "$OPENCODE_LOG"'
python3 - "$dir/home/config/crew-dispatch.json" > "$WORK/routes.txt" <<'PY'
import json, sys
dispatch = json.load(open(sys.argv[1]))
for rule in dispatch["rules"]:
    print(rule["when"].split(":")[0][:30], "|", " ".join(f"{p['harness']}/{p.get('model')}/{p.get('effort')}" for p in rule["use"]))
print("default |", " ".join(p["harness"] for p in dispatch["default"]))
PY
check "OpenCode joins both execution rules" '[[ $(grep -c "opencode/openai/gpt-6-luna/xhigh" "$WORK/routes.txt") == 2 ]]'
check "OpenCode joins the default" 'grep -q "^default | codex opencode$" "$WORK/routes.txt"'
check "planning and escalation rules are untouched" '! grep -E "^(The task is a separate|First escalation|Second escalation).*opencode" "$WORK/routes.txt"'

echo "# swarm-branches"
SB="$ROOT/bin/swarm-branches"
chmod +x "$SB"
plans="$WORK/plans"
mkdir -p "$plans"
expect "init names the integration and worker branches" 0 "integration login, workers login-worker-1, login-worker-2" \
  "$SB" init "$plans/login.json" --project acme/app --name login --workers 2
expect "init refuses to overwrite a plan" 1 "plan already exists" "$SB" init "$plans/login.json" --project acme/app --name login --workers 2
expect "init rejects a name with a space" 1 "name must be" "$SB" init "$plans/bad.json" --project acme/app --name "bad name" --workers 1
expect "init with a prefix" 0 "integration fm/login" "$SB" init "$plans/prefixed.json" --project acme/app --name login --workers 1 --prefix fm/
expect "check allows workers with no declared paths" 0 "works in any path" "$SB" check "$plans/login.json"
set_plan() {
  python3 - "$1" "$2" <<'PY'
import json, sys
path = sys.argv[1]
plan = json.load(open(path))
exec(sys.argv[2])
json.dump(plan, open(path, "w"), indent=2)
PY
}
set_plan "$plans/login.json" 'w = plan["workers"]; w[0]["owns"] = ["src/auth", "package.json"]; w[1]["owns"] = ["src/ui/"]; w[1]["depends_on"] = ["login-worker-1"]'
expect "check prints the merge order" 0 "2. login-worker-2 on login-worker-2 works in src/ui; after login-worker-1" "$SB" check "$plans/login.json"
cp "$plans/login.json" "$plans/overlap.json"
set_plan "$plans/overlap.json" 'plan["workers"][1]["owns"] = ["src/auth/session.ts"]'
expect "check allows a shared path" 0 "src/auth and src/auth/session.ts: login-worker-1, login-worker-2" "$SB" check "$plans/overlap.json"
cp "$plans/login.json" "$plans/cycle.json"
set_plan "$plans/cycle.json" 'plan["workers"][0]["depends_on"] = ["login-worker-2"]'
expect "check rejects dependency cycles" 1 "dependency cycle" "$SB" check "$plans/cycle.json"
cp "$plans/login.json" "$plans/glob.json"
set_plan "$plans/glob.json" 'plan["workers"][1]["owns"] = ["src/*.ts"]'
expect "check rejects globs" 1 "globs are not supported" "$SB" check "$plans/glob.json"
cp "$plans/login.json" "$plans/escape.json"
set_plan "$plans/escape.json" 'plan["workers"][1]["owns"] = ["../outside"]'
expect "check rejects paths outside the repository" 1 "without '..'" "$SB" check "$plans/escape.json"

repo="$WORK/project"
git init -q --bare "$repo.git"
git clone -q "$repo.git" "$repo" 2>/dev/null
git -C "$repo" config user.email t@example.com
git -C "$repo" config user.name t
mkdir -p "$repo/src/auth" "$repo/src/ui"
echo a > "$repo/src/auth/a.ts"; echo u > "$repo/src/ui/login.tsx"; echo '{}' > "$repo/package.json"
git -C "$repo" add . && git -C "$repo" commit -qm base
git -C "$repo" push -q origin HEAD:refs/heads/main HEAD:refs/heads/login
git -C "$repo" fetch -q origin
git -C "$repo" checkout -q -b one origin/login
echo a2 >> "$repo/src/auth/a.ts"; git -C "$repo" commit -qam one; git -C "$repo" push -q origin HEAD:refs/heads/login-worker-1
git -C "$repo" checkout -q -b two origin/login
echo u2 >> "$repo/src/ui/login.tsx"; echo '{"a":1}' > "$repo/package.json"; git -C "$repo" mv src/auth/a.ts src/ui/a.ts
git -C "$repo" commit -qam two; git -C "$repo" push -q origin HEAD:refs/heads/login-worker-2
expect "boundary accepts a worker inside its paths" 0 "login-worker-1 stayed within its boundary" "$SB" boundary "$plans/login.json" login-worker-1 --repo "$repo"
expect "boundary flags another worker's file" 1 "package.json (owned by login-worker-1)" "$SB" boundary "$plans/login.json" login-worker-2 --repo "$repo"
expect "boundary flags a file moved out of another worker's area" 1 "src/auth/a.ts (owned by login-worker-1)" "$SB" boundary "$plans/login.json" login-worker-2 --repo "$repo"
expect "boundary reads a file list from stdin" 1 "README.md (owned by no worker)" \
  bash -c 'printf "src/ui/x.ts\nREADME.md\n" | "$0" boundary "$1" login-worker-2 --files -' "$SB" "$plans/login.json"
expect "overlap lists files changed by two workers" 0 "src/auth/a.ts: login-worker-1, login-worker-2" "$SB" overlap "$plans/login.json" --repo "$repo"
git -C "$repo" checkout -q one
echo '{"b":2}' > "$repo/package.json"
git -C "$repo" commit -qam both
git -C "$repo" push -q origin HEAD:refs/heads/login-worker-1
expect "conflicts shows every side of a real merge conflict" 1 "Conflict merging login-worker-2" "$SB" conflicts "$plans/login.json" --repo "$repo" --no-fetch
expect "conflicts includes both workers' edits" 1 "login-worker-1 changed package.json" "$SB" conflicts "$plans/login.json" --repo "$repo" --no-fetch
set_plan "$plans/prefixed.json" 'plan["workers"][0]["owns"] = ["src"]'
expect "boundary explains an unpushed branch" 1 "branch fm/login is not on origin yet" "$SB" boundary "$plans/prefixed.json" login-worker-1 --repo "$repo"

: > "$GH_LOG"
expect "create-integration refuses an existing branch" 1 "already exists" env GH_EXISTING=1 "$SB" create-integration "$plans/login.json"
check "create-integration did not post" '! grep -q "POST" "$GH_LOG"'
expect "create-integration creates the branch from base" 0 "Created login at 0123456789ab" "$SB" create-integration "$plans/login.json"
check "create-integration posts the right ref" 'grep -q "POST repos/acme/app/git/refs -f ref=refs/heads/login -f sha=0123456789abcdef0123456789abcdef01234567" "$GH_LOG"'

echo "# manifest and dispatch"
expect "manifest matches the tracked files" 0 "Manifest matches" python3 "$ROOT/bin/manifest.py" check
if [[ -n "${UPSTREAM_BOOTSTRAP:-}" ]]; then
  expect "Firstmate's own validator accepts the dispatch file" 0 "valid" \
    bash "$ROOT/tests/upstream-dispatch.sh" "$UPSTREAM_BOOTSTRAP" "$ROOT/settings/config/crew-dispatch.json"
else
  echo "skip Firstmate validator (set UPSTREAM_BOOTSTRAP to a pinned bin/fm-bootstrap.sh)"
fi

printf '\n%d passed, %d failed\n' "$PASSED" "$FAILED"
[[ "$FAILED" == 0 ]]
