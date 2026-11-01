# Backgrounds. The core has two: paper (PAPER with a faint dotted grid) and plain (no grid).
# Packs add more in backgrounds.py (BACKGROUNDS = {name: fn(t)}, ANIMATED = {names that move}).
#
#   from pixel_kit import bg
#   img = bg.get("tissue", t)        from the pack stack (a higher pack wins), in the active style
#   bg.names()                       names in the stack
#
# A background draws in base (paper) colors; the style's background filter makes it dark or keeps it.

from PIL import Image, ImageDraw
from .palette import B, PAPER, GRID_LINE
from . import frame

_cache = {}          # base drawings, by key
_styled = {}         # (style, format, name) -> filtered image of a static background


def cached(key, make):
    if key not in _cache:
        _cache[key] = make()
    return _cache[key].copy()


def clear():
    _styled.clear()


def paper(t=0, w=None, h=None, grid=True, step=16):
    """The default background: PAPER with a faint dotted grid."""
    w, h = w or frame.W, h or frame.H

    def make():
        img = Image.new("RGB", (w, h), B(PAPER))
        if grid:
            d = ImageDraw.Draw(img)
            for x in range(0, w, step):
                for y in range(0, h, 4):
                    d.line([x, y, x, y + 1], fill=GRID_LINE)
            for y in range(0, h, step):
                for x in range(0, w, 4):
                    d.line([x, y, x + 1, y], fill=GRID_LINE)
        return img
    return cached(("paper", w, h, grid, step), make)


def plain(t=0, w=None, h=None):
    """PAPER without a grid."""
    return paper(t, w, h, grid=False)


CORE = {"paper": paper, "plain": plain}


def _table():
    from . import sprites
    out = {n: (fn, False, None) for n, fn in CORE.items()}
    for p in sprites.stack():
        for n, fn in p.backgrounds().items():
            out[n] = (fn, n in p.bg_animated, p.name)
    return out


def names():
    return sorted(_table())


def get(name, t=0.0):
    from . import style
    tab = _table()
    if name not in tab:
        raise KeyError(f"unknown background {name!r}; backgrounds: {', '.join(sorted(tab))}")
    fn, moving, _ = tab[name]
    st = style.current()
    key = (st.name, frame.NAME, name)
    if not moving and key in _styled:
        return _styled[key].copy()
    with style.base():
        img = fn(t)
    img = st.filter_background(img)
    if not moving:
        _styled[key] = img
        return img.copy()
    return img
