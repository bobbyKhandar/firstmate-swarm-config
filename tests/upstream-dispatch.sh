#!/usr/bin/env bash
# Validate a crew-dispatch.json with the jq program from Firstmate's own
# crew_dispatch_validate (bin/fm-bootstrap.sh), as bootstrap runs it without
# typed dispatch resolution.
# Usage: tests/upstream-dispatch.sh <fm-bootstrap.sh> <crew-dispatch.json>
set -euo pipefail

bootstrap=$1
dispatch=$2
read_bootstrap() {
  python3 - "$bootstrap" "$1" <<'PY'
import re, sys
source = open(sys.argv[1]).read()
body = source[source.index("crew_dispatch_validate() {"):]
if sys.argv[2] == "program":
    start = body.rindex("'", 0, body.index("def verified($h)")) + 1
    print(body[start:body.index("' \"$file\" 2>/dev/null", start)])
else:
    print(re.search(r"verified_harnesses='(\[[^']*\])'", body).group(1))
PY
}
program=$(read_bootstrap program)
harnesses=$(read_bootstrap harnesses)
err=$(jq -r --argjson typed false --argjson verified_harnesses "$harnesses" \
  --arg provider_re '^[a-z0-9]+(-[a-z0-9]+)*\z' "$program" "$dispatch")
if [[ -n "$err" ]]; then
  printf 'CREW_DISPATCH: invalid %s - %s\n' "$dispatch" "$err"
  exit 1
fi
printf 'Firstmate validator: %s is valid\n' "$dispatch"
