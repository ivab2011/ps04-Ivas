#!/usr/bin/env bash
# Evidence store: the ONLY component that reads or writes data/evidence/.
# Commands:
#   bash data/store.sh init
#   bash data/store.sh upsert RUN_DIR   < items.jsonl  > changes.jsonl
#   bash data/store.sh list                            > corpus.jsonl
#   bash data/store.sh get ITEM_ID [VERSION_ID]
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1          # always work from the repository root
PY="python3 data/store_db.py"

case "${1:-}" in
  init)
    $PY init
    ;;
  upsert)
    RUN_DIR="${2:-}"
    [ -d "$RUN_DIR" ] || { echo "usage: store.sh upsert RUN_DIR (directory must exist)" >&2; exit 2; }
    RUN_ID=$(jq -r '.run_id // empty' "$RUN_DIR/run.json" 2>/dev/null)
    RUN_ID="${RUN_ID:-$(basename "$RUN_DIR")}"
    STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    COUNT_FILE=$(mktemp)
    $PY upsert "$RUN_ID" 2>"$COUNT_FILE"
    STATUS=$?
    N=$(tail -1 "$COUNT_FILE")
    if [ $STATUS -eq 0 ]; then
      python3 lib/receipt.py "$RUN_DIR" store_upsert completed "$N" "$N" "$STARTED" sqlite3 0
    else
      cat "$COUNT_FILE" >&2
      python3 lib/receipt.py "$RUN_DIR" store_upsert failed null null "$STARTED" sqlite3 0 "$(cat "$COUNT_FILE")"
    fi
    rm -f "$COUNT_FILE"
    exit $STATUS
    ;;
  list)
    $PY list
    ;;
  get)
    [ -n "${2:-}" ] || { echo "usage: store.sh get ITEM_ID [VERSION_ID]" >&2; exit 2; }
    $PY get "$2" ${3:+"$3"}
    ;;
  *)
    echo "usage: store.sh {init|upsert RUN_DIR|list|get ITEM_ID [VERSION_ID]}" >&2
    exit 2
    ;;
esac
