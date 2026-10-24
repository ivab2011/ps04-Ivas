"""Turn an approved video script (package/video_scripts/NN.md) into plain narration text for TTS.
Removes: the Sources section, [VISUAL: ...] directions, claim markers like [02-c3], Markdown symbols.
Keeps the title as the first spoken sentence.
Usage: python production/narration.py package/video_scripts/01.md > production/out/narration_01.txt"""
import re, sys

text = open(sys.argv[1], encoding="utf-8").read()
text = re.split(r"\n##\s*Sources", text)[0]                     # drop the source list
lines = []
for line in text.splitlines():
    s = line.strip()
    if not s or s.startswith("[VISUAL") or s.startswith("*As of") or s == "---":
        continue
    s = re.sub(r"\[\d\d-c\d+\]", "", s)                          # claim markers
    s = re.sub(r"\[VISUAL:[^\]]*\]", "", s)                      # inline visual directions
    s = re.sub(r"^#+\s*", "", s)                                 # headings become sentences
    s = re.sub(r"[*_`>]", "", s)                                 # markdown emphasis
    s = re.sub(r"^\s*[-•]\s+", "", s)                            # bullets
    s = re.sub(r"\s+", " ", s).strip()
    if s and s[-1] not in ".?!:":
        s += "."
    if s:
        lines.append(s)
print("\n".join(lines))
