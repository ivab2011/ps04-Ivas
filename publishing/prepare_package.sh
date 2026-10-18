#!/usr/bin/env bash
# Assemble the production package after a passing, current review and matching human approval.
# Usage: bash publishing/prepare_package.sh RUN_DIR > RUN_DIR/package/manifest.json (also written directly)
# Exit 1 with an explanation when the review or approval is missing, failing or stale.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/run.json" ] || { echo "usage: prepare_package.sh RUN_DIR" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ERR=$(mktemp)
python3 publishing/package.py "$RUN_DIR" 2> "$ERR"
STATUS=$?
cat "$ERR" >&2
if [ $STATUS -eq 0 ]; then
  python3 lib/receipt.py "$RUN_DIR" prepare_package completed 6 9 "$STARTED" python3 0
else
  python3 lib/receipt.py "$RUN_DIR" prepare_package failed 6 0 "$STARTED" python3 0 "$(cat "$ERR")"
  STATUS=1
fi
rm -f "$ERR"
exit $STATUS
