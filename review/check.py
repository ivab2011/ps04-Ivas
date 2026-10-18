"""Automated content checks for review/check_content.sh. Emits one JSON review object.
A machine check cannot judge whether an interpretation is sound: human review is still required."""
import json, os, re, sys, unicodedata
from datetime import date, timedelta
sys.path.insert(0, "lib")
import evidence, fingerprint, references

RUN_DIR = sys.argv[1]
issues = []


def issue(target, severity, text):
    issues.append({"target": target, "severity": severity, "explanation": text})


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return " ".join(s.split()).lower()


def jsonl(name):
    p = os.path.join(RUN_DIR, name)
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else None


run = json.load(open(os.path.join(RUN_DIR, "run.json")))
as_of = date.fromisoformat(run["as_of_date"])
start = as_of - timedelta(days=29)
briefs, articles, scripts = jsonl("briefs.jsonl"), jsonl("articles.jsonl"), jsonl("video_scripts.jsonl")

# 1. required files and exactly three distinct pieces
for name, rows in (("briefs.jsonl", briefs), ("articles.jsonl", articles), ("video_scripts.jsonl", scripts)):
    if rows is None:
        issue(name, "error", "missing")
    elif sorted(r.get("piece_id") for r in rows) != ["01", "02", "03"]:
        issue(name, "error", "must contain exactly pieces 01, 02, 03")
for folder in ("articles", "video_scripts"):
    for pid in ("01", "02", "03"):
        if not os.path.exists(os.path.join(RUN_DIR, folder, f"{pid}.md")):
            issue(f"{folder}/{pid}.md", "error", "missing draft")
briefs = briefs or []
args = [norm(b.get("argument") or "") for b in briefs]
if len(set(args)) < len(args) or len({norm(b.get("title") or "") for b in briefs}) < len(briefs):
    issue("briefs.jsonl", "error", "pieces are not distinct (duplicate title or argument)")

# 2. evidence: resolvable, verbatim quotes, valid segments, dates, independence, media coverage
series_kinds = set()
for b in briefs:
    pid = b["piece_id"]
    pubs = set()
    for field in ("argument", "synthesis", "limitations"):
        if not (b.get(field) or "").strip():
            issue(f"brief {pid}", "error", f"empty {field}")
    if not b.get("claims"):
        issue(f"brief {pid}", "error", "no claims")
    for c in b.get("claims", []):
        cid = c.get("claim_id")
        if c.get("type") not in ("reported_fact", "source_claim", "inference"):
            issue(cid, "error", f"invalid claim type {c.get('type')!r}")
        if not c.get("evidence"):
            issue(cid, "error", "claim has no evidence")
        for ref in c.get("evidence", []):
            item = references.get_item(ref.get("item_id", ""), ref.get("version_id", ""))
            if item is None:
                issue(cid, "error", f"evidence {ref.get('item_id')} @ {str(ref.get('version_id'))[:10]} not found in store")
                continue
            pubs.add(item["publisher_id"])
            series_kinds.add(item["kind"])
            pub = item.get("published_at")
            if not pub or not (start <= date.fromisoformat(pub[:10]) <= as_of):
                issue(cid, "error", f"{item['item_id']} published {pub} is outside the window {start}..{as_of}")
            loc = ref.get("locator", {})
            if loc.get("type") == "text":
                if not loc.get("quote") or norm(loc["quote"]) not in norm(evidence.load_text(item)):
                    issue(cid, "error", f"quote not found verbatim in {item['item_id']}: {str(loc.get('quote'))[:80]!r}")
            elif loc.get("type") == "segment":
                ids = {s["segment_id"] for s in (evidence.load_segments(item) or [])}
                if loc.get("segment_id") not in ids:
                    issue(cid, "error", f"segment {loc.get('segment_id')} not found in {item['item_id']}")
            else:
                issue(cid, "error", "locator must be type text (with quote) or segment (with segment_id)")
    if len(pubs) < 3:
        issue(f"brief {pid}", "error", f"only {len(pubs)} independent publishers ({sorted(pubs)}); need >= 3")
for k in ("feed", "youtube", "podcast"):
    if k not in series_kinds:
        issue("series", "error", f"no {k} evidence used across the three pieces")

# 3. drafts: markers resolve, all claims used, consistency article vs script, lengths
brief_claims = {b["piece_id"]: [c["claim_id"] for c in b.get("claims", [])] for b in briefs}


def body_of(path):
    text = open(path, encoding="utf-8").read()
    return re.split(r"\n## Sources", text)[0]


for pid in ("01", "02", "03"):
    known = set(brief_claims.get(pid, []))
    used = {}
    for folder, lo, hi in (("articles", 600, 900), ("video_scripts", 400, 750)):
        path = os.path.join(RUN_DIR, folder, f"{pid}.md")
        if not os.path.exists(path):
            continue
        body = body_of(path)
        markers = set(re.findall(r"\[(\d\d-c\d+)\]", body))
        used[folder] = markers
        for m in sorted(markers - known):
            issue(f"{folder}/{pid}.md", "error", f"marker [{m}] does not match any claim in brief {pid}")
        for m in sorted(known - markers):
            issue(f"{folder}/{pid}.md", "warning", f"claim {m} from the brief is not used")
        words = len(re.sub(r"\[[^\]]*\]", "", body).split())
        if not lo <= words <= hi:
            issue(f"{folder}/{pid}.md", "warning", f"{words} words; target {lo}-{hi}")
    if "articles" in used and "video_scripts" in used and used["articles"] != used["video_scripts"]:
        issue(f"piece {pid}", "warning", "article and video script cite different claims: "
              f"only article {sorted(used['articles'] - used['video_scripts'])}, "
              f"only script {sorted(used['video_scripts'] - used['articles'])}")
    issue(f"piece {pid}", "warning", "Human judgment required: check that interpretations are sound, "
          "fact/claim/inference labels are right, and the limitation is fairly stated.")

print(json.dumps({"review_id": fingerprint.review_id(RUN_DIR), "as_of_date": run["as_of_date"],
                  "passed": not any(i["severity"] == "error" for i in issues),
                  "error_count": sum(i["severity"] == "error" for i in issues),
                  "warning_count": sum(i["severity"] == "warning" for i in issues),
                  "issues": issues}, indent=2))
