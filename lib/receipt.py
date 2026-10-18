"""Write one stage receipt to RUN_DIR/logs/ (shared helper used by every stage).

Usage: python3 lib/receipt.py RUN_DIR STAGE STATUS INPUT_COUNT OUTPUT_COUNT STARTED_AT [TOOLS] [COST_USD] [ERRORS]
"""
import json, os, sys, uuid
from datetime import datetime, timezone

run_dir, stage, status, n_in, n_out, started = sys.argv[1:7]
tools = sys.argv[7] if len(sys.argv) > 7 else ""
cost = sys.argv[8] if len(sys.argv) > 8 else ""
errors = sys.argv[9] if len(sys.argv) > 9 else ""

def num(x):
    try:
        return int(x)
    except ValueError:
        return None

finished = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
receipt = {
    "stage": stage,
    "status": status,
    "input_count": num(n_in),
    "output_count": num(n_out),
    "started_at": started,
    "finished_at": finished,
    "tools": [t for t in tools.split(",") if t],
    "cost_usd": float(cost) if cost not in ("", "null") else None,
    "errors": [e for e in errors.split("\n") if e.strip()],
}
os.makedirs(os.path.join(run_dir, "logs"), exist_ok=True)
name = f"{stage.replace('/', '_')}-{finished.replace(':', '')}-{uuid.uuid4().hex[:6]}.json"
with open(os.path.join(run_dir, "logs", name), "w") as f:
    json.dump(receipt, f, indent=2)
