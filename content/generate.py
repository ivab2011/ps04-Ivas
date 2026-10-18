"""Shared generator for content/write_articles.sh and content/write_video_scripts.sh.
Usage: python3 content/generate.py RUN_DIR articles|video_scripts USAGE_FILE < briefs.jsonl
Writes RUN_DIR/<kind>/<piece>.md and prints manifest JSONL (piece_id, path, claim_ids)."""
import json, os, re, sys
sys.path.insert(0, "lib")
import llm, references

RUN_DIR, KIND, USAGE_FILE = sys.argv[1], sys.argv[2], sys.argv[3]
CFG = {"articles": ("write_articles.md", "articles", "## Sources"),
       "video_scripts": ("write_video_scripts.md", "scripts", "## Sources (for the video description)")}
prompt_file, stage, heading = CFG[KIND]
project = open(f"{RUN_DIR}/config/project.json").read()
policy = open(f"{RUN_DIR}/config/editorial_policy.md").read()
as_of = json.load(open(f"{RUN_DIR}/run.json"))["as_of_date"]
os.makedirs(f"{RUN_DIR}/{KIND}", exist_ok=True)

for line in sys.stdin:
    if not line.strip():
        continue
    brief = json.loads(line)
    pid = brief["piece_id"]
    prompt = llm.render(f"{RUN_DIR}/prompts/{prompt_file}", {
        "PROJECT": project, "POLICY": policy, "AS_OF": as_of, "PART": str(int(pid)),
        "BRIEF": json.dumps(brief, indent=1, ensure_ascii=False),
        "EVIDENCE": references.evidence_for_prompt(brief)})
    draft = llm.call(RUN_DIR, stage, prompt, want_json=False, label=pid).strip()
    draft = re.split(r"\n#+\s*(Sources|References)\b", draft)[0].rstrip()   # code owns the source list
    path = f"{RUN_DIR}/{KIND}/{pid}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(draft + "\n\n" + references.source_notes(brief, heading))
    known = [c["claim_id"] for c in brief["claims"]]
    used = [c for c in known if f"[{c}]" in draft]
    print(json.dumps({"piece_id": pid, "path": path, "claim_ids": used}))
    print(f"{KIND}: wrote {path} ({len(draft.split())} words, {len(used)}/{len(known)} claims marked)", file=sys.stderr)

open(USAGE_FILE, "w").write(llm.usage_summary())
