#!/usr/bin/env bash
# Mechanical 30-day eligibility check. Editorial relevance is NOT decided here.
# Usage: bash processing/filter_items.sh RUN_DIR < corpus.jsonl > eligible.jsonl
# Side effect: RUN_DIR/exclusions.jsonl
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/run.json" ] || { echo "usage: filter_items.sh RUN_DIR (needs RUN_DIR/run.json)" >&2; exit 2; }
AS_OF=$(jq -r '.as_of_date // empty' "$RUN_DIR/run.json")
[ -n "$AS_OF" ] || { echo "filter: run.json has no as_of_date" >&2; exit 2; }

STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
COUNTS=$(mktemp)
python3 processing/filter_dates.py "$AS_OF" "$RUN_DIR/exclusions.jsonl" 2>"$COUNTS"
STATUS=$?
if [ $STATUS -eq 0 ]; then
  read -r N_IN N_OK N_EX < "$COUNTS"
  echo "filter: $N_IN items, $N_OK eligible, $N_EX excluded (as of $AS_OF)" >&2
  python3 lib/receipt.py "$RUN_DIR" filter_items completed "$N_IN" "$N_OK" "$STARTED" python3 0
else
  cat "$COUNTS" >&2
  python3 lib/receipt.py "$RUN_DIR" filter_items failed null null "$STARTED" python3 0 "$(cat "$COUNTS")"
  STATUS=2
fi
rm -f "$COUNTS"
exit $STATUS
