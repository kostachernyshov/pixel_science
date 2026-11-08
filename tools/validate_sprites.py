# Checks the sprites of every pack before a merge. CI runs it on each pull request.
#   python3 tools/validate_sprites.py
# Rules (see CONTRIBUTING.md), for packs/<pack>/sprites/:
#   - each PNG has an entry in sprites.json, and each entry has its PNG
#   - each entry has group, cell, anchor, anims; each animation row and frame fits the sheet
#   - colors are from the palette (pixel_kit/palette.py), alpha is 0 or 255 (no smoothing)
#   - each sprite has a row in CREDITS.csv with an author and an allowed license
import csv, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from PIL import Image
from pixel_kit.palette import SPRITE_PALETTES
from pixel_kit import packs
LICENSES = {"CC0-1.0", "CC-BY-4.0"}
GROUPS = {"hero", "villain", "civilian", "people", "prop", "badge"}


def is_local_pack(pack):
    """An ignored manifest marks a local pack outside the contribution checks."""
    manifest = os.path.abspath(os.path.join(pack.dir, "pack.yaml"))
    if os.path.commonpath((ROOT, manifest)) != ROOT:
        return False
    try:
        return subprocess.run(
            ["git", "check-ignore", "-q", "--", os.path.relpath(manifest, ROOT)],
            cwd=ROOT, stderr=subprocess.DEVNULL,
        ).returncode == 0
    except FileNotFoundError:
        return False


def main():
    out, total, seen = [], 0, {}
    for p in packs.find().values():
        if is_local_pack(p):
            print(f"Skipping local pack: {p.name}")
            continue
        if os.path.exists(os.path.join(p.sprites_dir, "sprites.json")):
            n, probs = check_pack(p.sprites_dir)
            total += n
            out += [f"{p.name}/{x}" for x in probs]
            for name in json.load(open(os.path.join(p.sprites_dir, "sprites.json"))):
                if name in seen:
                    out.append(f"{p.name}/{name}: the name is also in pack {seen[name]}")
                seen[name] = p.name
    for x in out:
        print(" -", x)
    print(f"{total} sprites: " + ("VALID" if not out else f"{len(out)} PROBLEMS"))
    return 1 if out else 0


def check_pack(SPR):
    out = []
    meta = json.load(open(os.path.join(SPR, "sprites.json")))
    credits = {r["sprite"]: r for r in csv.DictReader(open(os.path.join(SPR, "CREDITS.csv"), encoding="utf-8"))}
    pngs = {f for f in os.listdir(SPR) if f.endswith(".png")}
    files = {m.get("file") for m in meta.values()}
    for f in sorted(pngs - files):
        out.append(f"{f}: PNG without an entry in sprites.json")
    for name, m in meta.items():
        palette_name = m.get("palette", "PICO-8")
        if palette_name not in SPRITE_PALETTES:
            out.append(f"{name}: unknown palette {palette_name!r}")
        pal = set(SPRITE_PALETTES.get(palette_name, ()))
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
        source_cell = m.get("source_cell", m["cell"])
        if (not isinstance(source_cell, list) or len(source_cell) != 2
                or any(type(side) is not int or side < 1 for side in source_cell)):
            out.append(f"{name}: source cell must have two positive integer dimensions")
            continue
        cw, ch = source_cell
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
            out.append(f"{name}: no row in CREDITS.csv")
        else:
            if c.get("license") not in LICENSES:
                out.append(f"{name}: license {c.get('license')!r} is not allowed; use {', '.join(sorted(LICENSES))}")
            if not c.get("author"):
                out.append(f"{name}: no author in CREDITS.csv")
    for name in sorted(set(credits) - set(meta)):
        out.append(f"CREDITS.csv: {name} is not in sprites.json")
    return len(meta), out


if __name__ == "__main__":
    sys.exit(main())
