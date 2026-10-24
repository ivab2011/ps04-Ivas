"""Make a simple 1920x1080 title slide (PNG) for a video.
Usage: python production/slide.py "Part 1 of 3" "Title text" production/out/slide_01.png"""
import sys, textwrap
from PIL import Image, ImageDraw, ImageFont

part, title, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1920, 1080
img = Image.new("RGB", (W, H), (16, 32, 56))
d = ImageDraw.Draw(img)


def font(size):
    for path in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Helvetica.ttc",
                 "/Library/Fonts/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


d.text((120, 120), "AGENTIC GRC", font=font(54), fill=(120, 190, 255))
d.text((120, 200), part, font=font(40), fill=(200, 210, 225))
y = 380
for line in textwrap.wrap(title, width=34):
    d.text((120, y), line, font=font(84), fill=(255, 255, 255))
    y += 110
d.text((120, H - 150), "Governing agentic AI in critical infrastructure", font=font(36), fill=(200, 210, 225))
d.text((120, H - 95), "Narrated with AI text-to-speech (my own voice). Sources in the description.",
       font=font(30), fill=(150, 165, 185))
img.save(out)
print(f"slide: wrote {out}")
