#!/usr/bin/env bash
# Retrieve full text or transcripts for candidates and emit normalized item records.
# Usage: bash processing/extract_content.sh RUN_DIR < candidates.jsonl > items.jsonl
# Side effects: data/assets/text/, data/assets/segments/, data/media/ (audio, not in Git)
# Exit 0 = all items extracted, 1 = some items could not be processed (reported in the receipt).
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -d "$RUN_DIR" ] || { echo "usage: extract_content.sh RUN_DIR < candidates.jsonl" >&2; exit 2; }
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ERR=$(mktemp)
python3 processing/extract.py "$ERR"      # progress goes straight to the terminal
STATUS=$?
read -r _ N_IN N_OUT N_REUSED COST < <(grep '^COUNTS' "$ERR" || echo "COUNTS null null null null")
echo "extract: $N_IN candidates, $N_OUT items ($N_REUSED reused from store), Whisper cost \$$COST" >&2
if [ $STATUS -eq 0 ]; then RESULT=completed; else RESULT=incomplete; fi
python3 lib/receipt.py "$RUN_DIR" extract_content "$RESULT" "$N_IN" "$N_OUT" "$STARTED" \
  "trafilatura,yt-dlp,ffmpeg,openai:${WHISPER_MODEL:-whisper-1}" "$COST" "$(grep '^ERROR' "$ERR" | sed 's/^ERROR //')"
rm -f "$ERR"
exit $STATUS
