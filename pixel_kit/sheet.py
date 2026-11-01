# Sprite sheets: code sprites -> one index array (row = animation, column = frame), and back.
#
#   arr, info = sheet.assemble(spec)          spec = {"anims": {name: {"frames": [(Spr, dx, dy)], "fps", "loop"}}}
#   arr = sheet.indices(rgba_image)           PNG in the base palette -> index array (-1 transparent)
#   im = sheet.to_rgba(arr, colors)           index array -> RGBA with a list of RGB colors
#
# Sheet layout: all cells one size, 4 px of room left and right, 2 px top and bottom.

import numpy as np
from PIL import Image
from .palette import P, BLACK
from .pixdraw import Spr, pad, outline, has_outline

PAD_X, PAD_Y = 4, 2


def with_outline(s, col=BLACK):
    """Adds a 1 px outline if the shape has none (white bodies need it on a light background)."""
    if has_outline(s, col):
        return s
    p = pad(s, 1)
    outline(p, col)
    return p


def assemble(spec, outline_col=BLACK):
    anims = {an: dict(a, frames=[(with_outline(s, outline_col), dx, dy) for (s, dx, dy) in a["frames"]])
             for an, a in spec["anims"].items()}
    fw = max(s.w for a in anims.values() for (s, _, _) in a["frames"])
    fh = max(s.h for a in anims.values() for (s, _, _) in a["frames"])
    cw, ch = fw + 2 * PAD_X, fh + 2 * PAD_Y
    cols = max(len(a["frames"]) for a in anims.values())
    sh = Spr(cw * cols, ch * len(anims))
    info = {}
    for r, (an, a) in enumerate(anims.items()):
        for i, (s, dx, dy) in enumerate(a["frames"]):
            sh.stamp(s, i * cw + (cw - s.w) // 2 + dx, r * ch + (ch - s.h) // 2 + dy)
        info[an] = {"row": r, "frames": len(a["frames"]), "fps": a["fps"], "loop": a["loop"]}
    meta = {"cell": [cw, ch], "anchor": [cw / 2, ch / 2], "anims": info}
    return sh.a, meta


_KEYS = None


def indices(im):
    """RGBA image -> int16 index array. Colors outside the base palette become -2 (an error to report)."""
    global _KEYS
    if _KEYS is None:
        keys = np.array([(r << 16) | (g << 8) | b for r, g, b in P], np.int64)
        order = np.argsort(keys)
        _KEYS = (keys[order], order)
    a = np.asarray(im.convert("RGBA")).astype(np.int64)
    key = (a[..., 0] << 16) | (a[..., 1] << 8) | a[..., 2]
    sk, order = _KEYS
    pos = np.clip(np.searchsorted(sk, key), 0, len(sk) - 1)
    out = np.where(sk[pos] == key, order[pos], -2).astype(np.int16)
    out[a[..., 3] == 0] = -1
    return out


def to_rgba(arr, colors):
    rgba = np.zeros(arr.shape + (4,), np.uint8)
    for i, col in enumerate(colors):
        m = arr == i
        if m.any():
            rgba[m] = tuple(col[:3]) + (255,)
    return Image.fromarray(rgba, "RGBA")
