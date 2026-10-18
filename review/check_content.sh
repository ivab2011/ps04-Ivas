#!/usr/bin/env bash
# Automated checks of briefs, drafts, scripts and evidence references. Emits review JSON.
# Usage: bash review/check_content.sh RUN_DIR > RUN_DIR/review.json
# Exit 0 whenever the assessment ran (even if "passed": false); 1 only if it could not run.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/run.json" ] || { echo "usage: check_content.sh RUN_DIR" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUT=$(python3 review/check.py "$RUN_DIR")
STATUS=$?
if [ $STATUS -ne 0 ]; then
  python3 lib/receipt.py "$RUN_DIR" check_content failed null null "$STARTED" python3 0 "assessment could not run"
  exit 1
fi
echo "$OUT"
echo "check: passed=$(echo "$OUT" | jq .passed), $(echo "$OUT" | jq .error_count) errors, $(echo "$OUT" | jq .warning_count) warnings" >&2
python3 lib/receipt.py "$RUN_DIR" check_content completed 1 "$(echo "$OUT" | jq '.issues | length')" "$STARTED" python3 0
