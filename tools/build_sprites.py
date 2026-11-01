# Builds sprites/*.png and sprites/sprites.json from pixel_kit/library.py.
#   python3 tools/build_sprites.py            all sprites
#   python3 tools/build_sprites.py nk tumor   only these (so that PNGs edited by hand stay)
# Sprites added as PNG (not in library.py) stay in sprites.json; see CONTRIBUTING.md.
# Sheet: row = animation, column = frame, all cells have one size, transparent background.
# Light theme: each frame gets a 1 px INK outline if it has none (white bodies on PAPER).
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from pixel_kit.library import build
from pixel_kit.pixdraw import Spr, pad, outline, has_outline
from pixel_kit.palette import INK

OUT = os.path.join(ROOT, "sprites")


def light(s):
    if has_outline(s, INK):
        return s
    p = pad(s, 1)
    outline(p, INK)
    return p


def main(only):
    os.makedirs(OUT, exist_ok=True)
    jpath = os.path.join(OUT, "sprites.json")
    meta = json.load(open(jpath)) if os.path.exists(jpath) else {}
    lib = build()
    # remove only sprites that this script drew before; PNG sprites added by hand stay
    for name in list(meta):
        if name not in lib and meta[name].get("source") == "code":
            del meta[name]
    for name, spec in lib.items():
        if only and name not in only:
            continue
        anims = {an: dict(a, frames=[(light(s), dx, dy) for (s, dx, dy) in a["frames"]])
                 for an, a in spec["anims"].items()}
        px, py = 4, 2
        fw = max(s.w for a in anims.values() for (s, _, _) in a["frames"])
        fh = max(s.h for a in anims.values() for (s, _, _) in a["frames"])
        cw, ch = fw + 2 * px, fh + 2 * py
        cols = max(len(a["frames"]) for a in anims.values())
        sheet = Spr(cw * cols, ch * len(anims))
        info = {}
        for r, (an, a) in enumerate(anims.items()):
            for i, (s, dx, dy) in enumerate(a["frames"]):
                sheet.stamp(s, i * cw + (cw - s.w) // 2 + dx, r * ch + (ch - s.h) // 2 + dy)
            info[an] = {"row": r, "frames": len(a["frames"]), "fps": a["fps"], "loop": a["loop"]}
        sheet.image().save(os.path.join(OUT, name + ".png"))
        meta[name] = {"file": name + ".png", "group": spec["group"], "cell": [cw, ch],
                      "anchor": [cw / 2, ch / 2], "anims": info, "source": "code"}
    json.dump(meta, open(jpath, "w"), indent=1, ensure_ascii=False)
    print(len(meta), "sprites ->", OUT)


if __name__ == "__main__":
    main(set(sys.argv[1:]))
