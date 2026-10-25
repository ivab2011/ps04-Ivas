"""Build a YouTube description for a piece from the approved package.
Usage: python production/yt_description.py RUN_DIR 01 ARTICLE_URL > production/out/youtube_01.txt"""
import re, sys

run, pid, url = sys.argv[1], sys.argv[2], sys.argv[3]
title = open(f"{run}/package/video_scripts/{pid}.md", encoding="utf-8").readline().lstrip("# ").strip()
notes = open(f"{run}/package/sources/{pid}.md", encoding="utf-8").read()
notes = notes.split("## Sources", 1)[1] if "## Sources" in notes else notes
lines = []
for raw in notes.splitlines():
    s = raw.strip()
    if not s or s.startswith("*Bracketed"):
        continue
    s = s.replace("**", "")
    if s.startswith("- ["):
        lines.append("")
        lines.append(s[2:])                      # "[01-c1] Reported fact: ..."
    else:
        lines.append("  • " + s)                 # one evidence reference
desc = "\n".join([
    title,
    f"Part {int(pid)} of 3 in the Agentic GRC series: governing agentic AI in critical infrastructure.",
    "",
    f"Read the full article with all references: {url}",
    "",
    "Narration: AI text-to-speech (Chatterbox) using my own voice. The script was drafted with AI assistance",
    "from a documented evidence pipeline and reviewed and edited by me (Iva Biscanic).",
    "",
    "SOURCES: each claim in the video, with its evidence (timestamps point to the passage in audio/video sources)",
] + lines).strip() + "\n"
if len(desc) > 4900:                             # YouTube limit is 5000 characters
    desc = desc[:4800].rsplit("\n", 1)[0] + f"\n\n(Full source list in the article: {url})\n"
sys.stdout.write(desc)
print(f"youtube_description {pid}: {len(desc)} characters", file=sys.stderr)
