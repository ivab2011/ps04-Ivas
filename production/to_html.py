"""Render an approved article (package/articles/NN.md) as a simple HTML page to copy into Substack.
Claim markers like [01-c2] stay in the text; a note explains that they point to the Sources list."""
import sys, markdown

src, dst = sys.argv[1], sys.argv[2]
md = open(src, encoding="utf-8").read()
md = md.replace("## Sources", "## Sources\n\n*Bracketed references in the text, such as [01-c2], point to the "
                "numbered claims below; each lists its source, date and link (with a timestamp for audio and video).*", 1)
md += ("\n\n---\n\n*This article was drafted with AI assistance from a documented evidence pipeline "
       "and reviewed and edited by the author.*\n")
html = markdown.markdown(md, extensions=["extra"])
open(dst, "w", encoding="utf-8").write(f"<html><head><meta charset='utf-8'><style>body{{max-width:720px;"
                                       f"margin:40px auto;font-family:Georgia,serif;line-height:1.6}}</style>"
                                       f"</head><body>{html}</body></html>")
print("wrote", dst)
