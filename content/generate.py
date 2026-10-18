"""Shared generator for content/write_articles.sh and content/write_video_scripts.sh.
Usage: python3 content/generate.py RUN_DIR articles|video_scripts USAGE_FILE < briefs.jsonl
Writes RUN_DIR/<kind>/<piece>.md and prints manifest JSONL (piece_id, path, claim_ids).
Length is checked by code; a draft outside the target gets one revision call (the
'## Revision instruction' section of the prompt file), kept only if no claim marker is lost."""
import json, os, re, sys
sys.path.insert(0, "lib")
import llm, references

RUN_DIR, KIND, USAGE_FILE = sys.argv[1], sys.argv[2], sys.argv[3]
CFG = {"articles": ("write_articles.md", "articles", "## Sources", 650, 850),
       "video_scripts": ("write_video_scripts.md", "scripts", "## Sources (for the video description)", 450, 650)}
prompt_file, stage, heading, MIN_W, MAX_W = CFG[KIND]
TEMPLATE_PATH = f"{RUN_DIR}/prompts/{prompt_file}"
MAIN_PROMPT, _, REVISION_PROMPT = open(TEMPLATE_PATH, encoding="utf-8").read().partition("## Revision instruction")


def count_words(text):
    """Words excluding the title line and claim markers / visual directions."""
    body = "\n".join(l for l in text.splitlines() if not l.startswith("# "))
    body = re.sub(r"\[[^\]]*\]", "", body)
    return len(body.split())


def fill(template, values):
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    return template


project = open(f"{RUN_DIR}/config/project.json").read()
policy = open(f"{RUN_DIR}/config/editorial_policy.md").read()
as_of = json.load(open(f"{RUN_DIR}/run.json"))["as_of_date"]
os.makedirs(f"{RUN_DIR}/{KIND}", exist_ok=True)

for line in sys.stdin:
    if not line.strip():
        continue
    brief = json.loads(line)
    pid = brief["piece_id"]
    prompt = fill(MAIN_PROMPT, {
        "PROJECT": project, "POLICY": policy, "AS_OF": as_of, "PART": str(int(pid)),
        "BRIEF": json.dumps(brief, indent=1, ensure_ascii=False),
        "EVIDENCE": references.evidence_for_prompt(brief)})
    draft = llm.call(RUN_DIR, stage, prompt, want_json=False, label=pid).strip()
    draft = re.split(r"\n#+\s*(Sources|References)\b", draft)[0].rstrip()   # code owns the source list
    for attempt in (1, 2):                                          # up to two length revisions, checked by code
        words = count_words(draft)
        if not REVISION_PROMPT or MIN_W <= words <= MAX_W:
            break
        target = (MIN_W + MAX_W) // 2
        print(f"{KIND}: {pid} has {words} words (target {MIN_W}-{MAX_W}); revision {attempt}", file=sys.stderr)
        revised = llm.call(RUN_DIR, stage, fill(REVISION_PROMPT, {
            "WORDS": str(words), "MIN": str(MIN_W), "MAX": str(MAX_W),
            "CUT": str(max(words - target, 0)), "TARGET": str(target), "DRAFT": draft}),
            want_json=False, label=f"{pid}-revise{attempt}").strip()
        revised = re.split(r"\n#+\s*(Sources|References)\b", revised)[0].rstrip()
        before = set(re.findall(r"\[(\d\d-c\d+)\]", draft))
        after = set(re.findall(r"\[(\d\d-c\d+)\]", revised))
        if not before <= after:                                     # never lose a claim to save words
            print(f"{KIND}: {pid} revision dropped claims {sorted(before - after)}; keeping previous draft", file=sys.stderr)
            break
        draft = revised
    path = f"{RUN_DIR}/{KIND}/{pid}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(draft + "\n\n" + references.source_notes(brief, heading))
    known = [c["claim_id"] for c in brief["claims"]]
    used = [c for c in known if f"[{c}]" in draft]
    print(json.dumps({"piece_id": pid, "path": path, "claim_ids": used}))
    print(f"{KIND}: wrote {path} ({count_words(draft)} words, {len(used)}/{len(known)} claims marked)", file=sys.stderr)

open(USAGE_FILE, "w").write(llm.usage_summary())
