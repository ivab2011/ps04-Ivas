#!/usr/bin/env bash
# Collection workflow: collectors -> extraction -> evidence store -> 30-day filter.
# Coordination only; each step's logic lives in its own component.
# Usage: bash workflows/collect_sources.sh RUN_DIR
# Exit 0 = complete coverage, 1 = incomplete coverage (usable results kept), 2 = bad arguments.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -f "$RUN_DIR/run.json" ] || { echo "usage: collect_sources.sh RUN_DIR" >&2; exit 2; }
mkdir -p "$RUN_DIR/candidates"
INCOMPLETE=()

echo "== 1/4 collectors (running in parallel)" >&2
bash collectors/fetch_feeds.sh    "$RUN_DIR" > "$RUN_DIR/candidates/feeds.jsonl"    & P_FEEDS=$!
bash collectors/fetch_youtube.sh  "$RUN_DIR" > "$RUN_DIR/candidates/youtube.jsonl"  & P_YT=$!
bash collectors/fetch_podcasts.sh "$RUN_DIR" > "$RUN_DIR/candidates/podcasts.jsonl" & P_POD=$!
wait $P_FEEDS; S=$?; [ $S -ne 0 ] && INCOMPLETE+=("fetch_feeds:exit_$S")
wait $P_YT;    S=$?; [ $S -ne 0 ] && INCOMPLETE+=("fetch_youtube:exit_$S")
wait $P_POD;   S=$?; [ $S -ne 0 ] && INCOMPLETE+=("fetch_podcasts:exit_$S")

# combine only valid JSON records (jq -c drops nothing silently: invalid lines make jq fail)
cat "$RUN_DIR"/candidates/{feeds,youtube,podcasts}.jsonl | jq -c . > "$RUN_DIR/candidates.jsonl" \
  || INCOMPLETE+=("combine_candidates:invalid_json")
echo "collect: $(wc -l < "$RUN_DIR/candidates.jsonl" | tr -d ' ') candidates" >&2

echo "== 2/4 extraction" >&2
bash processing/extract_content.sh "$RUN_DIR" < "$RUN_DIR/candidates.jsonl" > "$RUN_DIR/items.jsonl"
S=$?; [ $S -ne 0 ] && INCOMPLETE+=("extract_content:exit_$S")

echo "== 3/4 evidence store" >&2
bash data/store.sh upsert "$RUN_DIR" < "$RUN_DIR/items.jsonl" > "$RUN_DIR/changes.jsonl"
S=$?; [ $S -ne 0 ] && { echo "collect: store upsert failed" >&2; exit 1; }

echo "== 4/4 export corpus and apply 30-day window" >&2
# a real pipe between two components: store list -> filter
bash data/store.sh list | tee "$RUN_DIR/corpus.jsonl" | bash processing/filter_items.sh "$RUN_DIR" > "$RUN_DIR/eligible.jsonl"
S=$?; [ $S -ne 0 ] && { echo "collect: filter failed" >&2; exit 1; }

# record coverage status for the summary
printf '%s\n' "${INCOMPLETE[@]:-}" | jq -R . | jq -s '{complete: (map(select(. != "")) | length == 0),
  problems: map(select(. != ""))}' > "$RUN_DIR/collection_status.json"
if [ ${#INCOMPLETE[@]} -gt 0 ]; then
  echo "collect: INCOMPLETE coverage: ${INCOMPLETE[*]} (continuing with usable results)" >&2
  exit 1
fi
echo "collect: complete" >&2
exit 0
