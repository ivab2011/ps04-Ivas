#!/usr/bin/env bash
# Entry point. Coordination only.
#   bash run.sh                      new live run: collect -> series -> checks, stops for human review
#   bash run.sh --package runs/ID    rerun checks, package after matching human approval
set -uo pipefail
cd "$(dirname "$0")" || exit 1

summarize() {   # always save the summary last and print it
  bash reporting/summarize_run.sh "$1" > "$1/summary.json"
  cat "$1/summary.json"
}

# ---------------- package mode ----------------
if [ "${1:-}" = "--package" ]; then
  RUN_DIR="${2:-}"
  [ -f "$RUN_DIR/run.json" ] || { echo "usage: bash run.sh --package runs/RUN_ID" >&2; exit 2; }
  bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/review.json"
  bash publishing/prepare_package.sh "$RUN_DIR" > /dev/null
  S=$?
  summarize "$RUN_DIR"
  exit $S
fi
[ $# -eq 0 ] || { echo "usage: bash run.sh | bash run.sh --package runs/RUN_ID" >&2; exit 2; }

# ---------------- validate configuration ----------------
fail_config() { echo "config error: $1" >&2; exit 2; }
jq -e '[.publication_name, .topic, .audience, .central_question] | all(type == "string" and length > 0)' \
  config/project.json > /dev/null 2>&1 || fail_config "config/project.json needs 4 nonempty strings"
jq -e 'type == "array" and length > 0 and all(.[]; (.source_id|type)=="string" and (.publisher_id|type)=="string"
  and (.kind == "feed" or .kind == "youtube" or .kind == "podcast") and (.url|type)=="string")' \
  config/sources.json > /dev/null 2>&1 || fail_config "config/sources.json has invalid source definitions"
for f in config/editorial_policy.md prompts/select_items.md prompts/create_briefs.md \
         prompts/write_articles.md prompts/write_video_scripts.md; do
  [ -s "$f" ] || fail_config "$f is empty"
done

# ---------------- create the run ----------------
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
AS_OF=$(date -u +%Y-%m-%d)                      # captured once, at the start
RUN_ID="live-$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="runs/$RUN_ID"
PREV=$(ls -d runs/live-* 2>/dev/null | sort | tail -1)
PREV_ID=$([ -n "$PREV" ] && basename "$PREV" || echo "")
mkdir -p "$RUN_DIR/logs"
jq -n --arg id "$RUN_ID" --arg s "$STARTED" --arg d "$AS_OF" --arg p "$PREV_ID" \
  '{run_id: $id, started_at: $s, as_of_date: $d, mode: "live", previous_run_id: (if $p == "" then null else $p end)}' \
  > "$RUN_DIR/run.json"
cp -R config "$RUN_DIR/config"                  # exact configuration and prompts used
cp -R prompts "$RUN_DIR/prompts"
echo "run: $RUN_ID (as of $AS_OF, previous: ${PREV_ID:-none})" >&2

bash data/store.sh init || { echo "run: store init failed" >&2; summarize "$RUN_DIR"; exit 1; }

# ---------------- workflows ----------------
bash workflows/collect_sources.sh "$RUN_DIR"
COLLECT=$?
if [ $COLLECT -le 1 ] && [ -s "$RUN_DIR/eligible.jsonl" ]; then
  bash workflows/create_series.sh "$RUN_DIR"
  SERIES=$?
else
  echo "run: no eligible evidence; series not created" >&2
  SERIES=1
fi

summarize "$RUN_DIR"
[ $SERIES -eq 0 ] && exit 0 || exit 1
