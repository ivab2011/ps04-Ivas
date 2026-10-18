"""Editorial selection helper for editorial/select_items.sh.
Sends eligible items in batches to the selection model with the policy and prompt snapshot,
and emits one decision per eligible item (accept / reject / defer, reason, piece_ids).

Robustness (added after live run 1, where the model returned 'lawfare-podcast:...' instead of
'podcast:lawfare-podcast:...'): returned IDs are matched back to the sent IDs when the match is
unique (recorded in id_repaired_from), and items still without a decision get one retry call.
Anything still missing is deferred for human review, never silently accepted or rejected."""
import json, sys
sys.path.insert(0, "lib")
import llm, evidence

RUN_DIR = sys.argv[1]
BATCH = 8
EXCERPT_WORDS = 500

project = open(f"{RUN_DIR}/config/project.json").read()
policy = open(f"{RUN_DIR}/config/editorial_policy.md").read()
sources = json.load(open(f"{RUN_DIR}/config/sources.json"))
items = [json.loads(l) for l in sys.stdin if l.strip()]
decisions = {}


def judge(batch, label):
    blocks = [evidence.header(it, sources) + "\nexcerpt:\n" + evidence.body(it, EXCERPT_WORDS) for it in batch]
    prompt = llm.render(f"{RUN_DIR}/prompts/select_items.md", {
        "PROJECT": project, "POLICY": policy, "ITEMS": "\n\n---\n\n".join(blocks)})
    result = llm.call(RUN_DIR, "selection", prompt, label=label)
    sent = [it["item_id"] for it in batch]
    for d in result.get("decisions", []):
        rid = d.get("item_id") or ""
        if rid not in sent:                       # model altered the ID: repair only if unambiguous
            matches = [s for s in sent if s.endswith(rid) or rid.endswith(s)] if rid else []
            if len(matches) != 1:
                continue
            d["id_repaired_from"] = rid
            rid = matches[0]
        decisions[rid] = d
    print(f"select: {label}: {len(batch)} items", file=sys.stderr)


for i in range(0, len(items), BATCH):
    judge(items[i:i + BATCH], f"batch{i // BATCH + 1:02d}")

missing = [it for it in items if it["item_id"] not in decisions]
if missing:
    print(f"select: retrying {len(missing)} items without a valid decision", file=sys.stderr)
    for i in range(0, len(missing), BATCH):
        judge(missing[i:i + BATCH], f"retry{i // BATCH + 1:02d}")

# Human overrides (config/editorial_overrides.json): the editor's final word, applied after the model.
# The model's own decision and reason are kept next to the human one.
try:
    overrides = json.load(open(f"{RUN_DIR}/config/editorial_overrides.json"))
except FileNotFoundError:
    overrides = {}

for it in items:
    d = decisions.get(it["item_id"])
    if d is None or d.get("decision") not in ("accept", "reject", "defer"):
        d = {"decision": "defer", "reason": "No valid decision returned by the model; needs human review.",
             "piece_ids": [], "relevance": None, "credibility_note": None}
    pieces = [p for p in d.get("piece_ids") or [] if p in ("01", "02", "03")] if d["decision"] == "accept" else []
    if d["decision"] == "accept" and not pieces:
        pieces = ["01"]
    rec = {"item_id": it["item_id"], "version_id": it["version_id"], "decision": d["decision"],
           "reason": d.get("reason", ""), "piece_ids": pieces, "relevance": d.get("relevance"),
           "credibility_note": d.get("credibility_note"), "kind": it["kind"],
           "publisher_id": it["publisher_id"], "title": it["title"]}
    if d.get("id_repaired_from"):
        rec["id_repaired_from"] = d["id_repaired_from"]
    rec["decided_by"] = "model"
    ov = overrides.get(it["item_id"])
    if ov and ov.get("decision") in ("accept", "reject", "defer"):
        rec["model_decision"], rec["model_reason"] = rec["decision"], rec["reason"]
        rec["decision"] = ov["decision"]
        rec["reason"] = "Human override: " + ov.get("reason", "")
        rec["piece_ids"] = ov.get("piece_ids", ["01"]) if ov["decision"] == "accept" else []
        rec["relevance"] = ov.get("relevance", rec["relevance"])
        rec["decided_by"] = "human"
    print(json.dumps(rec))

open(sys.argv[2], "w").write(llm.usage_summary())
