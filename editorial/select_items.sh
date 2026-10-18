#!/usr/bin/env bash
# AI editorial selection: one decision per eligible item, using the run's policy and prompt snapshot.
# Usage: bash editorial/select_items.sh RUN_DIR < eligible.jsonl > decisions.jsonl
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/config/editorial_policy.md" ] && [ -f "$RUN_DIR/prompts/select_items.md" ] \
  || { echo "usage: select_items.sh RUN_DIR (needs config and prompt snapshots)" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
USAGE=$(mktemp)
INPUT=$(mktemp); cat > "$INPUT"
N_IN=$(grep -c . "$INPUT")
python3 editorial/selection.py "$RUN_DIR" "$USAGE" < "$INPUT" > "$RUN_DIR/.decisions.tmp"
STATUS=$?
MODEL=$(jq -r .selection.model "$RUN_DIR/config/models.json")
if [ $STATUS -eq 0 ]; then
  cat "$RUN_DIR/.decisions.tmp"
  read -r CALLS TIN TOUT COST < "$USAGE"
  N_OUT=$(grep -c . "$RUN_DIR/.decisions.tmp")
  echo "select: $N_IN items -> $(grep -c '"accept"' "$RUN_DIR/.decisions.tmp") accept, $(grep -c '"reject"' "$RUN_DIR/.decisions.tmp") reject, $(grep -c '"defer"' "$RUN_DIR/.decisions.tmp") defer ($CALLS calls, $TIN/$TOUT tokens)" >&2
  python3 lib/receipt.py "$RUN_DIR" select_items completed "$N_IN" "$N_OUT" "$STARTED" "openai:$MODEL" "$COST"
else
  python3 lib/receipt.py "$RUN_DIR" select_items failed "$N_IN" null "$STARTED" "openai:$MODEL" null "selection model call failed (exit $STATUS)"
  STATUS=1
fi
rm -f "$USAGE" "$INPUT" "$RUN_DIR/.decisions.tmp"
exit $STATUS
