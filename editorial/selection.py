"""Editorial selection helper for editorial/select_items.sh.
Sends eligible items in batches to the selection model with the policy and prompt snapshot,
and emits one decision per eligible item (accept / reject / defer, reason, piece_ids)."""
import json, os, sys
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
for i in range(0, len(items), BATCH):
    batch = items[i:i + BATCH]
    blocks = [evidence.header(it, sources) + "\nexcerpt:\n" + evidence.body(it, EXCERPT_WORDS) for it in batch]
    prompt = llm.render(f"{RUN_DIR}/prompts/select_items.md", {
        "PROJECT": project, "POLICY": policy, "ITEMS": "\n\n---\n\n".join(blocks)})
    result = llm.call(RUN_DIR, "selection", prompt, label=f"batch{i // BATCH + 1:02d}")
    for d in result.get("decisions", []):
        decisions[d.get("item_id")] = d
    print(f"select: batch {i // BATCH + 1}: {len(batch)} items", file=sys.stderr)

for it in items:
    d = decisions.get(it["item_id"])
    if d is None or d.get("decision") not in ("accept", "reject", "defer"):
        d = {"decision": "defer", "reason": "No valid decision returned by the model; needs human review.",
             "piece_ids": [], "relevance": None, "credibility_note": None}
    pieces = [p for p in d.get("piece_ids") or [] if p in ("01", "02", "03")] if d["decision"] == "accept" else []
    if d["decision"] == "accept" and not pieces:
        pieces = ["01"]
    print(json.dumps({"item_id": it["item_id"], "version_id": it["version_id"], "decision": d["decision"],
                      "reason": d.get("reason", ""), "piece_ids": pieces, "relevance": d.get("relevance"),
                      "credibility_note": d.get("credibility_note"), "kind": it["kind"],
                      "publisher_id": it["publisher_id"], "title": it["title"]}))

open(sys.argv[2], "w").write(llm.usage_summary())
