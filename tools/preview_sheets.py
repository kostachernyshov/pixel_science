# Check sheet: all sprite sheets of a group with animation names, x4, on PAPER.
#   python3 tools/preview_sheets.py hero out.png [extra_name ...]
# Groups: hero, villain, civilian, prop, badge, people.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from PIL import Image, ImageDraw, ImageFont
from pixel_kit.palette import C, PAPER, INK, DGREY, GRID_LINE
F = ImageFont.truetype(os.path.join(ROOT, "fonts", "unifont.otf"), 16)
meta = json.load(open(os.path.join(ROOT, "sprites", "sprites.json")))
group, out = sys.argv[1], sys.argv[2]
names = [n for n, m in meta.items() if m["group"] == group or n in sys.argv[3:]]
K = 4
blocks = []
for n in names:
    m = meta[n]; im = Image.open(os.path.join(ROOT, "sprites", m["file"])).convert("RGBA")
    im = im.resize((im.width * K, im.height * K), Image.NEAREST)
    blocks.append((n, m, im))
W = max(220 + im.width for _, _, im in blocks) + 10
H = sum(im.height + 24 for _, _, im in blocks) + 10
canvas = Image.new("RGB", (W, H), C(PAPER)); d = ImageDraw.Draw(canvas)
y = 5
for n, m, im in blocks:
    d.text((6, y), n, font=F, fill=C(INK))
    ch = m["cell"][1] * K
    for an, a in m["anims"].items():
        d.text((10, y + 20 + a["row"] * ch + ch // 2 - 8), f"{an} ({a['frames']})", font=F, fill=C(DGREY))
    cw = m["cell"][0] * K
    for c in range(im.width // cw):
        for r in range(im.height // ch):
            d.rectangle([220 + c * cw, y + 20 + r * ch, 220 + c * cw + cw - 1, y + 20 + r * ch + ch - 1], outline=GRID_LINE)
    canvas.paste(im, (220, y + 20), im)
    y += im.height + 24
canvas.save(out); print(out, canvas.size)
