# Sprites by name from the active pack stack, in the active style.
#
#   from pixel_kit import sprites as S
#   S.use(["biology"])                          the content packs, bottom -> top (plan "packs")
#   S.draw(img, "nk", "idle", t, x, y)           animation frame at time t (s)
#   S.draw(img, "tumor", "death", t - t0, x, y)  a one-shot animation stops on its last frame
#   S.frame("nk", "attack", 2)                   one frame (RGBA)
#   S.draw(..., flip=True, scale=3)              mirror / portrait x3
#   S.where("nk")                               which pack and which cascade level drew it
#
# (x, y) is the anchor (cell center = body center).
#
# The cascade, most specific first:
#   1. a PNG drawn for this style: <style pack>/sprites/<name>.png with an entry in its sprites.json
#   2. a code sprite (the pack's code/library.py) drawn again with the style's parameters
#      (only for a style with redraw: true; the base PNGs already are the code sprites in paper)
#   3. the base PNG of the pack, recolored with the style's sprite colors

from PIL import Image
from . import packs, sheet as SH

_stack = None          # content packs, bottom -> top
_meta = None           # name -> meta (with "pack")
_sheets = {}           # name -> (RGBA sheet, meta, level)
_frames = {}
_built = {}            # pack name -> {sprite name: spec} drawn in code in the current style


def use(names=None):
    """Sets the content packs (bottom -> top). None: every content pack, in name order."""
    global _stack, _meta
    _stack = packs.stack(names) if names is not None else sorted(packs.content(), key=lambda p: p.name)
    _meta = None
    clear()
    return _stack


def stack():
    if _stack is None:
        use()
    return _stack


def clear():
    _sheets.clear()
    _frames.clear()
    _built.clear()


def meta():
    """{name: meta} of the stack; a higher pack overrides a lower one. meta["pack"] names the pack."""
    global _meta
    if _meta is None:
        _meta = {}
        for p in stack():
            for n, m in p.sprites().items():
                _meta[n] = dict(m, pack=p.name)
    return _meta


def names(group=None):
    return [n for n, m in meta().items() if group is None or m["group"] == group]


def _pack(name):
    if name not in meta():
        raise KeyError(f"unknown sprite {name!r}; packs: {', '.join(p.name for p in stack())} "
                       f"(find one: pixsci find <word>)")
    return packs.get(meta()[name]["pack"])


def _resolve(name):
    if name in _sheets:
        return _sheets[name]
    from . import style
    st = style.current()
    pk = _pack(name)
    base = meta()[name]
    # 1. a PNG drawn for this style
    if st.pack is not None and name in st.pack.sprites():
        m = st.pack.sprites()[name]
        im = Image.open(f"{st.pack.sprites_dir}/{m['file']}").convert("RGBA")
        _sheets[name] = (im, m, 1)
        return _sheets[name]
    # 2. a code sprite drawn again with the style's parameters
    if st.redraw and base.get("source") == "code" and pk.code() is not None:
        if pk.name not in _built:
            _built[pk.name] = pk.code().build()
        spec = _built[pk.name].get(name)
        if spec is not None:
            arr, m = SH.assemble(spec)
            _sheets[name] = (st.finish_sprite(arr), dict(base, **m), 2)
            return _sheets[name]
    # 3. the base PNG, recolored
    im = Image.open(f"{pk.sprites_dir}/{base['file']}").convert("RGBA")
    if not st.is_base or st.glow:
        im = st.finish_sprite(SH.indices(im))
    _sheets[name] = (im, base, 3)
    return _sheets[name]


def where(name):
    """(pack, level): level 1 style PNG, 2 code redrawn in the style, 3 base PNG recolored."""
    return meta()[name]["pack"], _resolve(name)[2]


def info(name):
    """Meta used for drawing (cell, anchor, anims) in the current style."""
    return _resolve(name)[1]


def anims(name):
    return info(name)["anims"]


def cell(name):
    return info(name)["cell"]


def body_top(name):
    """Pixels from the anchor up to the top of the opaque body in the first idle frame (at scale 1)."""
    key = ("top", name)
    if key not in _frames:
        im = frame(name, "idle" if "idle" in anims(name) else next(iter(anims(name))), 0)
        box = im.getchannel("A").getbbox()
        _frames[key] = info(name)["anchor"][1] - (box[1] if box else 0)
    return _frames[key]


def frame(name, anim="idle", i=0, flip=False, scale=1):
    key = (name, anim, i, flip, scale)
    if key not in _frames:
        im_sheet, m, _ = _resolve(name)
        if anim not in m["anims"]:
            raise KeyError(f"sprite {name} has no animation {anim!r}; it has {', '.join(m['anims'])}")
        a = m["anims"][anim]
        cw, ch = m["cell"]
        i = max(0, min(a["frames"] - 1, i))
        im = im_sheet.crop((i * cw, a["row"] * ch, (i + 1) * cw, (a["row"] + 1) * ch))
        if flip:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        if scale > 1:
            im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
        _frames[key] = im
    return _frames[key]


def index(name, anim, t, fps=None):
    """Frame number at time t (s from the start of the animation). One-shot animations stop on the last frame."""
    a = anims(name)[anim]
    n = int(max(t, 0) * (fps or a["fps"]))
    return n % a["frames"] if a["loop"] else min(n, a["frames"] - 1)


def duration(name, anim, fps=None):
    a = anims(name)[anim]
    return a["frames"] / (fps or a["fps"])


def draw(img, name, anim, t, x, y, flip=False, scale=1, fps=None, i=None):
    im = frame(name, anim, index(name, anim, t, fps) if i is None else i, flip, scale)
    m = info(name)
    ax, ay = m["anchor"]
    if flip:
        ax = m["cell"][0] - ax
    img.paste(im, (int(round(x - ax * scale)), int(round(y - ay * scale))), im)
    return im


def idle(img, name, t, x, y, seed=0, flip=False, scale=1, blink_every=2.3):
    """Rest with a bob and a rare blink (if the sprite has "blink")."""
    a = anims(name)
    if "blink" in a and ((t + seed * 0.37) % blink_every) < 0.1:
        return draw(img, name, "blink", 0, x, y, flip, scale)
    return draw(img, name, "idle", t + seed * 0.17, x, y, flip, scale)
