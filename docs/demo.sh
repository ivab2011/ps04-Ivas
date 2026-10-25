#!/usr/bin/env bash
# Technical demo helper: press Enter to show each part. Run from the repo root.
cd "$(dirname "$0")/.."
R1=runs/live-20261018T193123Z; R2=runs/live-20261019T140450Z; RF=runs/live-20261019T143701Z; RA=runs/replay-20261018T205452Z
step() { read -r -p $'\n[Enter] ' _; clear; echo -e "\033[1;34m== $1\033[0m\n"; }

step "1. Architecture: 16 required scripts, one entry point"
ls run.sh workflows/*.sh collectors/*.sh processing/*.sh data/store.sh editorial/*.sh content/*.sh review/*.sh publishing/*.sh reporting/*.sh
echo; sed -n '2,6p' run.sh

step "2. A live run: artifacts and summary"
ls $R1
jq '{run_id, status, counts: (.counts|{discovered,new,eligible,excluded,accepted,rejected,deferred}), coverage: .coverage.by_kind, publishers: .coverage.independent_publisher_count}' $R1/summary.json

step "3. Trace: published sentence -> brief claim -> decision -> stored version -> exact passage"
sed -n '1,45p' docs/claim_trace.md

step "4. Second run (new day): new / changed / unchanged, reuse"
cat docs/run_table.md | sed -n '5,12p'
grep -h "reused" /dev/null $R2/logs/extract_content-*.json 2>/dev/null
jq -c '{stage,status,input_count,output_count,cost_usd}' $R2/logs/extract_content-*.json

step "5. Labelled simulated failure: reported, run continues"
jq '{simulated_failure, collection, failed: [.failed_or_incomplete_stages[] | {stage, errors}]}' $RF/summary.json

step "6. Human correction: model decision kept next to mine"
jq -c 'select(.decided_by=="human") | {title: .title[0:45], model: .model_decision, human: .decision}' $RA/decisions.jsonl
echo; sed -n '/## Change log/,$p' config/editorial_policy.md

step "7. Tradeoff: references built by code, quotes verified, approval bound to a fingerprint"
jq '{review_id, passed, error_count, warning_count}' $RA/review.json
jq '{review_id, decision, reviewer}' $RA/approval.json
sed -n '/## Sources/,+6p' $RA/package/articles/02.md

step "8. Published series"
jq -r '.[] | "\(.piece_id)  \(.substack_url)\n    \(.youtube_url)"' $RA/package/publication_links.json
echo; echo "End of demo."
