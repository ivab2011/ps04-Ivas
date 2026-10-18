#!/usr/bin/env bash
# Build exactly three editorial briefs (01, 02, 03) from ACCEPTED evidence only.
# Usage: bash editorial/create_briefs.sh RUN_DIR < decisions.jsonl > briefs.jsonl
# Exit 1 when accepted evidence is insufficient (reported, never filled with invented sources).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/eligible.jsonl" ] && [ -f "$RUN_DIR/prompts/create_briefs.md" ] \
  || { echo "usage: create_briefs.sh RUN_DIR < decisions.jsonl (needs eligible.jsonl and prompt snapshot)" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
USAGE=$(mktemp)
INPUT=$(mktemp); cat > "$INPUT"
N_IN=$(grep -c '"accept"' "$INPUT")
python3 editorial/briefs.py "$RUN_DIR" "$USAGE" < "$INPUT" > "$RUN_DIR/.briefs.tmp" 2> "$RUN_DIR/.briefs.err"
STATUS=$?
cat "$RUN_DIR/.briefs.err" >&2
MODEL=$(jq -r .briefs.model "$RUN_DIR/config/models.json")
read -r CALLS TIN TOUT COST < "$USAGE" 2>/dev/null || COST=null
if [ $STATUS -eq 0 ] && [ "$(grep -c . "$RUN_DIR/.briefs.tmp")" -eq 3 ]; then
  cat "$RUN_DIR/.briefs.tmp"
  echo "briefs: 3 briefs from $N_IN accepted items" >&2
  python3 lib/receipt.py "$RUN_DIR" create_briefs completed "$N_IN" 3 "$STARTED" "openai:$MODEL" "$COST"
  STATUS=0
else
  python3 lib/receipt.py "$RUN_DIR" create_briefs failed "$N_IN" 0 "$STARTED" "openai:$MODEL" "${COST:-null}" "$(cat "$RUN_DIR/.briefs.err")"
  STATUS=1
fi
rm -f "$USAGE" "$INPUT" "$RUN_DIR/.briefs.tmp" "$RUN_DIR/.briefs.err"
exit $STATUS
