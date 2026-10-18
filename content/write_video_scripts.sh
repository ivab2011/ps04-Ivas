#!/usr/bin/env bash
# Generate three video_scripts drafts from the briefs (same briefs and evidence for video_scripts and scripts).
# Usage: bash content/write_video_scripts.sh RUN_DIR < briefs.jsonl > video_scripts.jsonl
# Side effects: RUN_DIR/video_scripts/01.md, 02.md, 03.md (claim markers inline, source notes appended by code)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/prompts/write_video_scripts.md" ] || { echo "usage: write_video_scripts.sh RUN_DIR < briefs.jsonl" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
USAGE=$(mktemp); INPUT=$(mktemp); cat > "$INPUT"
N_IN=$(grep -c . "$INPUT")
[ "$N_IN" -eq 3 ] || { echo "write_video_scripts: expected 3 briefs, got $N_IN" >&2; rm -f "$USAGE" "$INPUT"; exit 2; }
python3 content/generate.py "$RUN_DIR" video_scripts "$USAGE" < "$INPUT" > "$RUN_DIR/.video_scripts.tmp"
STATUS=$?
MODEL=$(jq -r .scripts.model "$RUN_DIR/config/models.json")
read -r CALLS TIN TOUT COST < "$USAGE" 2>/dev/null || COST=null
N_OUT=$(grep -c . "$RUN_DIR/.video_scripts.tmp")
if [ $STATUS -eq 0 ] && [ "$N_OUT" -eq 3 ]; then
  cat "$RUN_DIR/.video_scripts.tmp"
  python3 lib/receipt.py "$RUN_DIR" write_video_scripts completed 3 3 "$STARTED" "openai:$MODEL" "$COST"
else
  python3 lib/receipt.py "$RUN_DIR" write_video_scripts failed 3 "$N_OUT" "$STARTED" "openai:$MODEL" "${COST:-null}" "generation failed (exit $STATUS)"
  STATUS=1
fi
rm -f "$USAGE" "$INPUT" "$RUN_DIR/.video_scripts.tmp"
exit $STATUS
