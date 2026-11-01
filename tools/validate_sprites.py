# Checks the sprite library before a merge. CI runs it on each pull request.
#   python3 tools/validate_sprites.py
# Rules (see CONTRIBUTING.md):
#   - each PNG in sprites/ has an entry in sprites.json, and each entry has its PNG
#   - each entry has group, cell, anchor, anims; each animation row and frame fits the sheet
#   - colors are from the palette (pixel_kit/palette.py), alpha is 0 or 255 (no smoothing)
#   - each sprite has a row in sprites/CREDITS.csv with an author and an allowed license
import csv, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from PIL import Image
from pixel_kit.palette import P

SPR = os.path.join(ROOT, "sprites")
LICENSES = {"CC0-1.0", "CC-BY-4.0"}
GROUPS = {"hero", "villain", "civilian", "people", "prop", "badge"}


def main():
    out = []
    meta = json.load(open(os.path.join(SPR, "sprites.json")))
    credits = {r["sprite"]: r for r in csv.DictReader(open(os.path.join(SPR, "CREDITS.csv"), encoding="utf-8"))}
    pngs = {f for f in os.listdir(SPR) if f.endswith(".png")}
    files = {m.get("file") for m in meta.values()}
    for f in sorted(pngs - files):
        out.append(f"{f}: PNG without an entry in sprites.json")
    pal = {tuple(c) for c in P}
    for name, m in meta.items():
        for key in ("file", "group", "cell", "anchor", "anims"):
            if key not in m:
                out.append(f"{name}: no {key!r}")
        if m.get("group") not in GROUPS:
            out.append(f"{name}: group {m.get('group')!r} is not one of {', '.join(sorted(GROUPS))}")
        path = os.path.join(SPR, m.get("file", ""))
        if not os.path.exists(path):
            out.append(f"{name}: file {m.get('file')} not found")
            continue
        im = Image.open(path).convert("RGBA")
        cw, ch = m["cell"]
        for an, a in m["anims"].items():
            if (a["row"] + 1) * ch > im.height or a["frames"] * cw > im.width:
                out.append(f"{name}: animation {an} is outside the sheet ({im.width}x{im.height})")
        px = im.load()
        extra, soft = set(), 0
        for y in range(im.height):
            for x in range(im.width):
                r, g, b, al = px[x, y]
                if 0 < al < 255:
                    soft += 1
                elif al == 255 and (r, g, b) not in pal:
                    extra.add((r, g, b))
        if extra:
            out.append(f"{name}: {len(extra)} colors outside the palette, for example #{'%02x%02x%02x' % sorted(extra)[0]}")
        if soft:
            out.append(f"{name}: {soft} half-transparent pixels (use alpha 0 or 255)")
        c = credits.get(name)
        if not c:
            out.append(f"{name}: no row in sprites/CREDITS.csv")
        else:
            if c.get("license") not in LICENSES:
                out.append(f"{name}: license {c.get('license')!r} is not allowed; use {', '.join(sorted(LICENSES))}")
            if not c.get("author"):
                out.append(f"{name}: no author in CREDITS.csv")
    for name in sorted(set(credits) - set(meta)):
        out.append(f"CREDITS.csv: {name} is not in sprites.json")
    for p in out:
        print(" -", p)
    print(f"{len(meta)} sprites: " + ("VALID" if not out else f"{len(out)} PROBLEMS"))
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
