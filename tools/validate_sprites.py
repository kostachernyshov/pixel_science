# Checks the sprites of every pack before a merge. CI runs it on each pull request.
#   python3 tools/validate_sprites.py            all packs
#   python3 tools/validate_sprites.py biology    one pack
# Rules (see CONTRIBUTING.md):
#   - each PNG in a pack's sprites/ has an entry in sprites.json, and each entry has its PNG
#   - each entry has group, cell, anchor, anims, tags; each animation row and frame fits the sheet
#   - colors are from the base palette (pixel_kit/palette.py), alpha is 0 or 255 (no smoothing)
#   - each sprite has a row in the pack's CREDITS.csv with an author and an allowed license
#   - a sprite name is unique across content packs, unless the higher pack says "overrides: true"
#   - a style pack's sprite has the name of a sprite in a content pack (it is that sprite, redrawn)
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image
from pixel_kit import packs, sheet as SH

LICENSES = {"CC0-1.0", "CC-BY-4.0"}
GROUPS = {"hero", "villain", "civilian", "people", "prop", "badge", "particle", "machine", "field", "body"}


def check_pack(p, out):
    meta = p.sprites()
    if not meta:
        return 0
    credits = p.credits()
    d = p.sprites_dir
    pngs = {f for f in os.listdir(d) if f.endswith(".png")}
    files = {m.get("file") for m in meta.values()}
    for f in sorted(pngs - files):
        out.append(f"{p.name}/{f}: PNG without an entry in sprites.json")
    for name, m in meta.items():
        where = f"{p.name}/{name}"
        for key in ("file", "group", "cell", "anchor", "anims"):
            if key not in m:
                out.append(f"{where}: no {key!r}")
        if not m.get("tags"):
            out.append(f"{where}: no tags (pixsci find uses them)")
        if m.get("group") not in GROUPS:
            out.append(f"{where}: group {m.get('group')!r} is not one of {', '.join(sorted(GROUPS))}")
        path = os.path.join(d, m.get("file", ""))
        if not os.path.exists(path):
            out.append(f"{where}: file {m.get('file')} not found")
            continue
        im = Image.open(path).convert("RGBA")
        cw, ch = m["cell"]
        for an, a in m["anims"].items():
            if (a["row"] + 1) * ch > im.height or a["frames"] * cw > im.width:
                out.append(f"{where}: animation {an} is outside the sheet ({im.width}x{im.height})")
        if "idle" not in m["anims"]:
            out.append(f"{where}: no 'idle' animation")
        idx = SH.indices(im)
        alpha = np.asarray(im)[..., 3]
        soft = int(((alpha > 0) & (alpha < 255)).sum())
        extra = int((idx == -2).sum())
        if extra:
            out.append(f"{where}: {extra} pixels in colors outside the palette")
        if soft:
            out.append(f"{where}: {soft} half-transparent pixels (use alpha 0 or 255)")
        c = credits.get(name)
        if not c:
            out.append(f"{where}: no row in CREDITS.csv")
        else:
            if c.get("license") not in LICENSES:
                out.append(f"{where}: license {c.get('license')!r} is not allowed; use {', '.join(sorted(LICENSES))}")
            if not c.get("author"):
                out.append(f"{where}: no author in CREDITS.csv")
    for name in sorted(set(credits) - set(meta)):
        out.append(f"{p.name}/CREDITS.csv: {name} is not in sprites.json")
    return len(meta)


def main(only):
    out, n = [], 0
    allp = sorted(packs.find().values(), key=lambda p: p.name)
    owner = {}
    for p in allp:
        if only and p.name not in only:
            continue
        n += check_pack(p, out)
    for p in allp:
        if p.kind != "content":
            continue
        for name, m in p.sprites().items():
            if name in owner and not m.get("overrides"):
                out.append(f"{p.name}/{name}: the name is taken by pack {owner[name]} (set \"overrides\": true to replace it)")
            owner.setdefault(name, p.name)
    for p in allp:
        if p.kind == "style":
            for name in p.sprites():
                if name not in owner:
                    out.append(f"{p.name}/{name}: a style sprite redraws a content sprite; no content pack has {name!r}")
    for x in out:
        print(" -", x)
    print(f"{n} sprites: " + ("VALID" if not out else f"{len(out)} PROBLEMS"))
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
