# The catalog: every sprite, background and style of every pack, so that an agent can find what to use.
#
#   from pixel_kit import catalog
#   cat = catalog.build()                    {"packs": [...], "sprites": [...], "backgrounds": [...], "styles": [...]}
#   catalog.find("immune killer")            entries whose name, tags, group, pack or description match every word
#   catalog.write()                          packs/catalog.json (committed; CI checks that it is fresh)
#   catalog.sheet("out/sheet.png", style="arcade")   the cast sheet for people, from the same catalog

import json, os
from . import packs

PATH = os.path.join(packs.PACKS_DIR, "catalog.json")


def _rel(p):
    return os.path.relpath(p, packs.ROOT).replace(os.sep, "/")


def build():
    cat = {"version": 1, "packs": [], "sprites": [], "backgrounds": [], "styles": []}
    for p in sorted(packs.find().values(), key=lambda p: p.name):
        cat["packs"].append({"name": p.name, "kind": p.kind, "version": p.meta.get("version"),
                             "description": p.description, "license": p.meta.get("license"),
                             "path": _rel(p.dir), "bible": _rel(p.bible) if p.bible else None})
        cr = p.credits()
        for n, m in sorted(p.sprites().items()):
            first = next(iter(m["anims"].values()))
            cw, ch = m["cell"]
            c = cr.get(n, {})
            cat["sprites"].append({
                "name": n, "pack": p.name, "group": m.get("group"), "tags": m.get("tags", []),
                "description": m.get("description", ""), "anims": list(m["anims"]),
                "size": [cw, ch], "source": m.get("source", "png"),
                "license": c.get("license"), "author": c.get("author"),
                "thumbnail": {"file": _rel(os.path.join(p.sprites_dir, m["file"])),
                              "box": [0, first["row"] * ch, cw, (first["row"] + 1) * ch]},
                "for_style": p.style["name"] if p.kind == "style" and p.style else None})
        for n in sorted(p.backgrounds()):
            cat["backgrounds"].append({"name": n, "pack": p.name, "tags": p.bg_tags.get(n, []),
                                       "animated": n in p.bg_animated})
        if p.kind == "style" and p.style:
            cat["styles"].append({"name": p.style["name"], "pack": p.name,
                                  "description": p.style.get("description", p.description),
                                  "dark": bool(p.style.get("dark", False))})
    for n in ("paper", "plain"):
        cat["backgrounds"].append({"name": n, "pack": None, "tags": ["core", "plain"], "animated": False})
    return cat


def write(path=PATH):
    """Writes the catalog; returns the path relative to the repo."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build(), f, indent=1, ensure_ascii=False)
        f.write("\n")
    return _rel(path)


def is_fresh(path=PATH):
    return os.path.exists(path) and json.load(open(path, encoding="utf-8")) == json.loads(json.dumps(build()))


def _score(e, term):
    t = term.lower()
    name = e["name"].lower()
    tags = [x.lower() for x in e.get("tags", [])]
    s = 0
    if name == t:
        s += 10
    elif t in name.replace("_", " ").split() or t in name:
        s += 5
    if t in tags:
        s += 4
    elif any(x.startswith(t) for x in tags):
        s += 2
    if t in (e.get("group") or "", e.get("pack") or ""):
        s += 3
    if t in (e.get("description") or "").lower():
        s += 1
    return s


def find(query, kind=None, pack=None, group=None, cat=None):
    """Entries that match every word of the query (any word for an empty query), best first."""
    cat = cat or build()
    terms = [w for w in str(query or "").split() if w]
    out = []
    for k in ("sprites", "backgrounds", "styles"):
        if kind and not k.startswith(kind):
            continue
        for e in cat[k]:
            if pack and e.get("pack") != pack:
                continue
            if group and e.get("group") != group:
                continue
            scores = [_score(e, t) for t in terms]
            if terms and not all(scores):
                continue
            out.append(dict(e, kind=k[:-1], score=sum(scores)))
    return sorted(out, key=lambda e: (-e["score"], e["kind"], e["name"]))


# ---------------------------------------------------------------- cast sheet for people

def sheet(out, style_name="paper", pack=None):
    """First frame of each sprite x4, by pack and group, in a style."""
    from PIL import Image, ImageDraw
    from . import sprites as S, style
    from .font import text, title_text
    from .palette import C, PAPER, INK, ACCENT, PLATE, PLATE_INK, DIM, LGREY, XBLUE
    cat = build()
    sel = [e for e in cat["sprites"] if e["for_style"] is None and (pack is None or e["pack"] == pack)]
    S.use(sorted({e["pack"] for e in sel}))
    style.use(style_name)
    COLS, TW, TH, K = 8, 116, 118, 4
    order = ["hero", "villain", "civilian", "people", "prop", "badge"]
    by = {}
    for e in sel:
        by.setdefault((e["pack"], e["group"]), []).append(e["name"])
    groups = sorted(by.items(), key=lambda g: (g[0][0], order.index(g[0][1]) if g[0][1] in order else 99, str(g[0][1])))
    rows = sum((len(n) + COLS - 1) // COLS for _, n in groups)
    w = COLS * TW + 16
    h = 70 + len(groups) * 28 + rows * (TH + 6) + len(groups) * 4 + 16
    img = Image.new("RGB", (w, h), C(PAPER))
    d = ImageDraw.Draw(img)
    title_text(img, w // 2, 12, "PIXEL SCIENCE", 4, XBLUE, ACCENT)
    text(img, w // 2, 46, f"SPRITES x4 . STYLE {style_name.upper()}", DIM, align="c")
    y = 74
    for (pk, grp), names in groups:
        d.rectangle([8, y, w - 9, y + 19], fill=C(PLATE))
        text(img, 16, y + 2, f"{pk.upper()} . {str(grp).upper()}", PLATE_INK)
        y += 26
        for i, n in enumerate(names):
            if i and i % COLS == 0:
                y += TH + 6
            x0 = 8 + (i % COLS) * TW
            d.rectangle([x0 + 2, y, x0 + TW - 4, y + TH], outline=C(LGREY))
            first = next(iter(S.anims(n)))
            k = K
            im = S.frame(n, first, 0, scale=k)
            while im.height > 92 and k > 1:
                k -= 1
                im = S.frame(n, first, 0, scale=k)
            img.paste(im, (x0 + (TW - 2 - im.width) // 2, y + 46 - im.height // 2), im)
            text(img, x0 + TW // 2 - 1, y + TH - 20, n.upper().replace("_", " ")[:13], INK, align="c")
        y += TH + 10
    import numpy as np
    img = Image.fromarray(style.current().filter_frame(np.asarray(img)))
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out)
    return out
