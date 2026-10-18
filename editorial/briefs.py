"""Brief creation helper for editorial/create_briefs.sh.
Uses ONLY accepted items. Refuses (exit 1) when the accepted evidence cannot support the
series: fewer than 3 independent publishers, or a required input type (feed/youtube/podcast) missing."""
import json, sys
sys.path.insert(0, "lib")
import llm, evidence

RUN_DIR = sys.argv[1]
WORDS_PER_ITEM = 2500

decisions = [json.loads(l) for l in sys.stdin if l.strip()]
eligible = {json.loads(l)["item_id"]: json.loads(l) for l in open(f"{RUN_DIR}/eligible.jsonl") if l.strip()}
accepted = [eligible[d["item_id"]] for d in decisions if d["decision"] == "accept" and d["item_id"] in eligible]

publishers = {it["publisher_id"] for it in accepted}
kinds = {it["kind"] for it in accepted}
problems = []
if len(publishers) < 3:
    problems.append(f"only {len(publishers)} independent publishers accepted (need >= 3)")
for k in ("feed", "youtube", "podcast"):
    if k not in kinds:
        problems.append(f"no accepted {k} evidence")
if problems:
    print("briefs: INSUFFICIENT EVIDENCE: " + "; ".join(problems), file=sys.stderr)
    open(sys.argv[2], "w").write(llm.usage_summary())
    sys.exit(1)

sources = json.load(open(f"{RUN_DIR}/config/sources.json"))
blocks = [evidence.header(it, sources) + "\ncontent:\n" + evidence.body(it, WORDS_PER_ITEM) for it in accepted]
prompt = llm.render(f"{RUN_DIR}/prompts/create_briefs.md", {
    "PROJECT": open(f"{RUN_DIR}/config/project.json").read(),
    "POLICY": open(f"{RUN_DIR}/config/editorial_policy.md").read(),
    "AS_OF": json.load(open(f"{RUN_DIR}/run.json"))["as_of_date"],
    "EVIDENCE": "\n\n=====\n\n".join(blocks)})
result = llm.call(RUN_DIR, "briefs", prompt, label="briefs")

briefs = {b.get("piece_id"): b for b in result.get("briefs", [])}
if sorted(briefs) != ["01", "02", "03"]:
    print(f"briefs: model returned piece_ids {sorted(briefs)}, expected 01 02 03", file=sys.stderr)
    open(sys.argv[2], "w").write(llm.usage_summary())
    sys.exit(1)
versions = {it["item_id"]: it["version_id"] for it in accepted}
for pid in ("01", "02", "03"):
    b = briefs[pid]
    for c in b.get("claims", []):
        for ref in c.get("evidence", []):
            if ref.get("item_id") in versions:        # pin the exact stored version used
                ref["version_id"] = versions[ref["item_id"]]
    print(json.dumps({k: b.get(k) for k in
                      ("piece_id", "title", "question", "argument", "synthesis", "limitations", "claims")}))
open(sys.argv[2], "w").write(llm.usage_summary())
