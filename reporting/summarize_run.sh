#!/usr/bin/env bash
# Report run status, counts, coverage, failures, time, tools and costs from saved artifacts.
# Usage: bash reporting/summarize_run.sh RUN_DIR > RUN_DIR/summary.json   (works for incomplete runs)
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
RUN_DIR="${1:-}"
[ -d "$RUN_DIR" ] || { echo "usage: summarize_run.sh RUN_DIR" >&2; exit 2; }
python3 reporting/summary.py "$RUN_DIR"
