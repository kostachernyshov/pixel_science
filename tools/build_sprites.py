# Builds packs/<pack>/sprites/*.png and sprites.json from the pack's code/library.py.
#   python3 tools/build_sprites.py biology            all sprites of the pack
#   python3 tools/build_sprites.py biology nk tumor   only these (so that PNGs edited by hand stay)
# Sprites registered as PNG keep their art even when a legacy code drawing exists.
# Sheet: row = animation, column = frame, all cells have one size, transparent background.
# Light theme: each frame gets a 1 px INK outline if it has none (white bodies on PAPER).
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from pixel_kit import packs
from pixel_kit.pixdraw import Spr, pad, outline, has_outline
from pixel_kit.palette import INK

def light(s):
    if has_outline(s, INK):
        return s
    p = pad(s, 1)
    outline(p, INK)
    return p


def main(pack, only):
    p = packs.get(pack)
    if not p.code():
        sys.exit(f"pack {pack} has no code/library.py")
    build = p.code().build
    OUT = p.sprites_dir
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
        if meta.get(name, {}).get("source") == "png":
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
    with open(jpath, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1, ensure_ascii=False)
    print(len(meta), "sprites ->", OUT)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: build_sprites.py <pack> [sprite ...]")
    main(sys.argv[1], set(sys.argv[2:]))
