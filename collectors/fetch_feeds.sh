#!/usr/bin/env bash
# Discover feed items from the sources configured in RUN_DIR/config/sources.json.
# Usage: bash collectors/fetch_feeds.sh RUN_DIR > RUN_DIR/candidates/feeds.jsonl
# Exit 0 = all sources read, 1 = some source failed (partial output kept), 2 = bad arguments/config.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/config/sources.json" ] || { echo "usage: fetch_feeds.sh RUN_DIR (needs RUN_DIR/config/sources.json)" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ERR=$(mktemp)
python3 collectors/collect.py feed "$RUN_DIR" 2>"$ERR"
STATUS=$?
grep -v "^COUNTS" "$ERR" >&2        # show progress and errors
read -r _ N_SRC N_OUT N_FAIL < <(grep '^COUNTS' "$ERR" || echo "COUNTS null null null")
if [ $STATUS -eq 0 ]; then RESULT=completed; elif [ $STATUS -eq 1 ]; then RESULT=incomplete; else RESULT=failed; fi
python3 lib/receipt.py "$RUN_DIR" fetch_feeds "$RESULT" "$N_SRC" "$N_OUT" "$STARTED" python3-urllib 0 "$(grep '^ERROR' "$ERR" | sed 's/^ERROR //')"
rm -f "$ERR"
exit $STATUS
