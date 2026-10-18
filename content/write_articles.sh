#!/usr/bin/env bash
# Generate three articles drafts from the briefs (same briefs and evidence for articles and scripts).
# Usage: bash content/write_articles.sh RUN_DIR < briefs.jsonl > articles.jsonl
# Side effects: RUN_DIR/articles/01.md, 02.md, 03.md (claim markers inline, source notes appended by code)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/prompts/write_articles.md" ] || { echo "usage: write_articles.sh RUN_DIR < briefs.jsonl" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
USAGE=$(mktemp); INPUT=$(mktemp); cat > "$INPUT"
N_IN=$(grep -c . "$INPUT")
[ "$N_IN" -eq 3 ] || { echo "write_articles: expected 3 briefs, got $N_IN" >&2; rm -f "$USAGE" "$INPUT"; exit 2; }
python3 content/generate.py "$RUN_DIR" articles "$USAGE" < "$INPUT" > "$RUN_DIR/.articles.tmp"
STATUS=$?
MODEL=$(jq -r .articles.model "$RUN_DIR/config/models.json")
read -r CALLS TIN TOUT COST < "$USAGE" 2>/dev/null || COST=null
N_OUT=$(grep -c . "$RUN_DIR/.articles.tmp")
if [ $STATUS -eq 0 ] && [ "$N_OUT" -eq 3 ]; then
  cat "$RUN_DIR/.articles.tmp"
  python3 lib/receipt.py "$RUN_DIR" write_articles completed 3 3 "$STARTED" "openai:$MODEL" "$COST"
else
  python3 lib/receipt.py "$RUN_DIR" write_articles failed 3 "$N_OUT" "$STARTED" "openai:$MODEL" "${COST:-null}" "generation failed (exit $STATUS)"
  STATUS=1
fi
rm -f "$USAGE" "$INPUT" "$RUN_DIR/.articles.tmp"
exit $STATUS
