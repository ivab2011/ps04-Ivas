#!/usr/bin/env bash
# Series workflow: selection -> briefs -> articles + video scripts -> content checks.
# Coordination only. Saves each artifact before continuing; stops and reports on failure.
# Usage: bash workflows/create_series.sh RUN_DIR
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/eligible.jsonl" ] || { echo "usage: create_series.sh RUN_DIR (needs eligible.jsonl)" >&2; exit 2; }
stop() { echo "series: STOPPED at $1. See $RUN_DIR/logs/ and repair before continuing." >&2; exit 1; }

echo "== 1/5 editorial selection" >&2
bash editorial/select_items.sh "$RUN_DIR" < "$RUN_DIR/eligible.jsonl" > "$RUN_DIR/decisions.jsonl" || stop "selection"

echo "== 2/5 editorial briefs" >&2
bash editorial/create_briefs.sh "$RUN_DIR" < "$RUN_DIR/decisions.jsonl" > "$RUN_DIR/briefs.jsonl" \
  || stop "briefs (insufficient accepted evidence or model error)"

echo "== 3/5 article drafts" >&2
bash content/write_articles.sh "$RUN_DIR" < "$RUN_DIR/briefs.jsonl" > "$RUN_DIR/articles.jsonl" || stop "articles"

echo "== 4/5 video scripts" >&2
bash content/write_video_scripts.sh "$RUN_DIR" < "$RUN_DIR/briefs.jsonl" > "$RUN_DIR/video_scripts.jsonl" || stop "video scripts"

echo "== 5/5 content checks" >&2
bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/review.json" || stop "content checks"
echo "series: drafts ready; review.json passed=$(jq .passed "$RUN_DIR/review.json"). Awaiting human review."
exit 0
