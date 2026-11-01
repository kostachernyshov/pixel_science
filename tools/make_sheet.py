# Cast sheet: the first frame of each sprite, x4, by group, on PAPER. Use it to choose sprites
# and to review a new or redrawn sprite.
#   python3 tools/make_sheet.py out.png
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from PIL import Image, ImageDraw
from pixel_kit import sprites as S
from pixel_kit.font import text, title_text
from pixel_kit.palette import *

GROUPS = [("hero", "IMMUNE CELLS"), ("villain", "TUMOR CELLS"), ("civilian", "BODY CELLS"),
          ("people", "PEOPLE"), ("prop", "PROPS"), ("badge", "MOLECULES")]
COLS, TW, TH, K = 8, 116, 118, 4


def build(out):
    rows = sum((len(S.names(g)) + COLS - 1) // COLS for g, _ in GROUPS)
    w = COLS * TW + 16
    h = 70 + len(GROUPS) * 28 + rows * (TH + 6) + 16
    img = Image.new("RGB", (w, h), C(PAPER))
    d = ImageDraw.Draw(img)
    title_text(img, w // 2, 12, "PIXEL KIT", 5, XBLUE, NAVY)
    text(img, w // 2, 50, "SPRITES x4 . LIGHT THEME", DGREY, align="c")
    y = 74
    for g, label in GROUPS:
        names = S.names(g)
        d.rectangle([8, y, w - 9, y + 19], fill=C(NAVY))
        text(img, 16, y + 2, label, WHITE)
        y += 26
        for i, n in enumerate(names):
            if i and i % COLS == 0:
                y += TH + 6
            x0 = 8 + (i % COLS) * TW
            d.rectangle([x0 + 2, y, x0 + TW - 4, y + TH], outline=C(LGREY))
            k = K if g != "people" else 3
            im = S.frame(n, "idle", 0, scale=k)
            if im.height > 92:
                im = S.frame(n, "idle", 0, scale=k - 1)
            img.paste(im, (x0 + (TW - 2 - im.width) // 2, y + 46 - im.height // 2), im)
            text(img, x0 + TW // 2 - 1, y + TH - 20, n.upper().replace("_", " ")[:13], INK, align="c")
        y += TH + 10
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save(out)
    print(out, img.size)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "sheet.png")
