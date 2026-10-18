"""Build summary JSON for reporting/summarize_run.sh from saved run artifacts and receipts.
Works on incomplete runs: counts for stages that did not run are null, measured empties are 0."""
import glob, json, os, sys
from datetime import datetime

run_dir = sys.argv[1]


def jsonl(name):
    path = os.path.join(run_dir, name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def jdoc(name):
    path = os.path.join(run_dir, name)
    return json.load(open(path)) if os.path.exists(path) else None


def count(rows, pred=lambda r: True):
    return None if rows is None else sum(1 for r in rows if pred(r))


run = jdoc("run.json") or {}
candidates, items, changes = jsonl("candidates.jsonl"), jsonl("items.jsonl"), jsonl("changes.jsonl")
eligible, exclusions, decisions = jsonl("eligible.jsonl"), jsonl("exclusions.jsonl"), jsonl("decisions.jsonl")
articles, scripts = jsonl("articles.jsonl"), jsonl("video_scripts.jsonl")
review, approval = jdoc("review.json"), jdoc("approval.json")
collection = jdoc("collection_status.json")
manifest = jdoc("package/manifest.json")
links = jdoc("package/publication_links.json")

receipts = []
for p in sorted(glob.glob(os.path.join(run_dir, "logs", "*.json"))):
    try:
        receipts.append(json.load(open(p)))
    except json.JSONDecodeError:
        pass

# coverage: distinct eligible items by kind and by independent publisher
coverage = None
if eligible is not None:
    distinct = {r["item_id"]: r for r in eligible}
    coverage = {"distinct_items": len(distinct), "by_kind": {}, "independent_publishers": sorted(
        {r["publisher_id"] for r in distinct.values()})}
    for r in distinct.values():
        coverage["by_kind"][r["kind"]] = coverage["by_kind"].get(r["kind"], 0) + 1
    coverage["independent_publisher_count"] = len(coverage["independent_publishers"])
duplicates = None if candidates is None else len(candidates) - len({c["item_id"] for c in candidates})

failed = [{"stage": r["stage"], "status": r["status"], "errors": r.get("errors", [])}
          for r in receipts if r.get("status") != "completed"]
known = [r["cost_usd"] for r in receipts if r.get("cost_usd") is not None]
unknown = sorted({r["stage"] for r in receipts if r.get("cost_usd") is None})
tools = sorted({t for r in receipts for t in r.get("tools", [])})

started = run.get("started_at")
last = max([r.get("finished_at") for r in receipts if r.get("finished_at")] or [None], key=lambda x: x or "")
elapsed = None
if started and last:
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    elapsed = int((datetime.strptime(last, fmt) - datetime.strptime(started, fmt)).total_seconds())

drafts_ok = articles is not None and len(articles) == 3 and scripts is not None and len(scripts) == 3
if manifest is not None:
    status = "ready_for_production"
elif drafts_ok and review is not None:
    status = "awaiting_review"
else:
    status = "failed"

manual = []
if status == "awaiting_review":
    manual.append("Read drafts and review.json, fix issues, record decision in approval.json, then run: bash run.sh --package " + run_dir)
if status in ("awaiting_review", "ready_for_production"):
    manual += ["Produce 3 narrated videos (text-to-speech + ffmpeg) from package/video_scripts",
               "Publish 3 Substack articles and 3 YouTube videos, then fill package/publication_links.json"]
if status == "failed":
    manual.append("Inspect failed_stages and logs/ to repair the run")

published = None
if links is not None:
    published = [l for l in links if l.get("substack_url") or l.get("youtube_url")]

print(json.dumps({
    "run_id": run.get("run_id"), "status": status, "as_of_date": run.get("as_of_date"),
    "mode": run.get("mode"), "previous_run_id": run.get("previous_run_id"),
    "simulated_failure": run.get("simulated_failure"),
    "counts": {
        "discovered": count(candidates), "extracted": count(items),
        "new": count(changes, lambda r: r["change"] == "new"),
        "changed": count(changes, lambda r: r["change"] == "changed"),
        "unchanged": count(changes, lambda r: r["change"] == "unchanged"),
        "eligible": count(eligible), "excluded": count(exclusions),
        "accepted": count(decisions, lambda r: r["decision"] == "accept"),
        "rejected": count(decisions, lambda r: r["decision"] == "reject"),
        "deferred": count(decisions, lambda r: r["decision"] == "defer"),
        "articles": count(articles), "video_scripts": count(scripts),
        "duplicate_observations": duplicates},
    "coverage": coverage,
    "collection": collection,
    "failed_or_incomplete_stages": failed,
    "review_passed": None if review is None else review.get("passed"),
    "human_approval": None if approval is None else approval.get("decision"),
    "elapsed_seconds": elapsed,
    "tools_and_models": tools,
    "cost_usd_known": round(sum(known), 4) if known else None,
    "cost_note": "Whisper cost is computed from audio minutes; model costs are estimates from token counts",
    "stages_with_unknown_cost": unknown,
    "published_links": published,
    "remaining_manual_actions": manual,
}, indent=2))
