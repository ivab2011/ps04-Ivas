"""Packaging helper for publishing/prepare_package.sh. Requires a passing review whose review_id
still matches the current inputs, and a matching human approval. Never regenerates drafts."""
import json, os, shutil, sys
sys.path.insert(0, "lib")
import fingerprint

RUN_DIR = sys.argv[1]
PKG = os.path.join(RUN_DIR, "package")


def load(name):
    p = os.path.join(RUN_DIR, name)
    return json.load(open(p)) if os.path.exists(p) else None


review, approval = load("review.json"), load("approval.json")
current = fingerprint.review_id(RUN_DIR)
problems = []
if review is None:
    problems.append("review.json is missing: run review/check_content.sh")
else:
    if not review.get("passed"):
        problems.append("review did not pass: fix the errors listed in review.json")
    if review.get("review_id") != current:
        problems.append(f"review is stale: drafts or briefs changed since review {review.get('review_id')} (now {current})")
if approval is None:
    problems.append("approval.json is missing: the human reviewer must create it")
else:
    if approval.get("review_id") != current:
        problems.append(f"approval.json review_id {approval.get('review_id')} does not match current inputs {current}")
    if approval.get("decision") != "approve":
        problems.append(f"approval decision is {approval.get('decision')!r}, not 'approve'")
    for k in ("reviewer", "reviewed_at", "notes"):
        if not approval.get(k):
            problems.append(f"approval.json field {k!r} is empty")
if problems:
    for p in problems:
        print("package: " + p, file=sys.stderr)
    sys.exit(1)

old_links = None
if os.path.exists(os.path.join(PKG, "publication_links.json")):
    old_links = json.load(open(os.path.join(PKG, "publication_links.json")))
for sub in ("articles", "video_scripts", "sources"):
    os.makedirs(os.path.join(PKG, sub), exist_ok=True)
assets = []
for pid in ("01", "02", "03"):
    for kind in ("articles", "video_scripts"):
        dst = os.path.join(PKG, kind, f"{pid}.md")
        shutil.copyfile(os.path.join(RUN_DIR, kind, f"{pid}.md"), dst)
        assets.append({"piece_id": pid, "type": kind[:-1], "path": dst})
    article = open(os.path.join(RUN_DIR, "articles", f"{pid}.md"), encoding="utf-8").read()
    notes = "## Sources" + article.split("## Sources", 1)[1] if "## Sources" in article else "No sources found.\n"
    dst = os.path.join(PKG, "sources", f"{pid}.md")
    open(dst, "w", encoding="utf-8").write(f"# Source notes for piece {pid}\n\n" + notes)
    assets.append({"piece_id": pid, "type": "source_notes", "path": dst})

links = old_links or [{"piece_id": p, "substack_url": None, "youtube_url": None} for p in ("01", "02", "03")]
json.dump(links, open(os.path.join(PKG, "publication_links.json"), "w"), indent=2)
manual = [
    "Generate narration audio for each package/video_scripts/NN.md with text-to-speech (Chatterbox, own voice) and combine with a title slide using ffmpeg (3-5 min video).",
    "Upload each video to YouTube (public or unlisted); paste the article link and package/sources/NN.md into the description.",
    "Publish each package/articles/NN.md on Substack (free access); link the article to its video.",
    "Fill substack_url and youtube_url in package/publication_links.json.",
]
open(os.path.join(PKG, "MANUAL_STEPS.md"), "w").write("# Remaining manual steps\n\n" + "\n".join(f"{i}. {m}" for i, m in enumerate(manual, 1)) + "\n")
manifest = {"run_id": json.load(open(os.path.join(RUN_DIR, "run.json")))["run_id"], "review_id": current,
            "approved_by": approval["reviewer"], "assets": assets,
            "publication_links": os.path.join(PKG, "publication_links.json"),
            "manual_steps": manual, "published": False}
json.dump(manifest, open(os.path.join(PKG, "manifest.json"), "w"), indent=2)
print(json.dumps(manifest, indent=2))
