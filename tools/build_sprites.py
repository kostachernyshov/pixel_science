# Builds a pack's code sprites into PNG sheets (the base style, paper) and sprites.json.
#   python3 tools/build_sprites.py biology            all code sprites of the pack
#   python3 tools/build_sprites.py biology nk tumor   only these (PNGs edited by hand stay)
# Sprites added as PNG (not in code) stay in sprites.json. Tags and descriptions in sprites.json stay.
# Sheet: row = animation, column = frame, all cells one size, transparent background, 1 px outline.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from pixel_kit import packs, style, sheet as SH
from pixel_kit.palette import P

KEEP = ("tags", "description")


def main(pack_name, only):
    style.use("paper")
    pk = packs.get(pack_name)
    lib = pk.code()
    if lib is None:
        sys.exit(f"pack {pack_name} has no code/library.py")
    out = pk.sprites_dir
    os.makedirs(out, exist_ok=True)
    jpath = os.path.join(out, "sprites.json")
    meta = json.load(open(jpath)) if os.path.exists(jpath) else {}
    built = lib.build()
    for name in list(meta):
        if name not in built and meta[name].get("source") == "code":
            del meta[name]
    for name, spec in built.items():
        if only and name not in only:
            continue
        arr, m = SH.assemble(spec)
        SH.to_rgba(arr, P).save(os.path.join(out, name + ".png"))
        old = meta.get(name, {})
        meta[name] = {"file": name + ".png", "group": spec["group"], **m, "source": "code",
                      **{k: old[k] for k in KEEP if k in old}, **{k: spec[k] for k in KEEP if k in spec}}
    json.dump(meta, open(jpath, "w"), indent=1, ensure_ascii=False)
    print(len(meta), "sprites ->", out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__ or "usage: build_sprites.py PACK [names]")
    main(sys.argv[1], set(sys.argv[2:]))
