# Load sprites and animations by name from the packs: packs/<pack>/sprites/*.png + sprites.json.
# All packs are loaded; S.use(["biology"]) limits them to the plan's packs (later packs win on a name).
#
#   from pixel_kit import sprites as S
#   S.draw(img, "nk", "idle", t, x, y)           animation frame at time t (s)
#   S.draw(img, "tumor", "death", t - t0, x, y)  a one-shot animation stops on its last frame
#   S.frame("nk", "attack", 2)                   one frame (RGBA)
#   S.draw(..., flip=True, scale=3)              mirror / portrait x3
#
# (x, y) is the anchor (cell center = body center).

import json, os
from PIL import Image, ImageOps
from . import packs

_use = None            # pack names, or None for all packs
_meta = None
_sheets = {}
_frames = {}


def use(names=None):
    """Load sprites only from these packs (bottom -> top). None: all packs."""
    global _use, _meta
    _use = list(names) if names else None
    _meta = None
    _sheets.clear()
    _frames.clear()


def in_use():
    """Names of the packs sprites load from: those of use(), else all packs."""
    return _use or sorted(packs.find())


def meta():
    """{name: entry} from the sprites.json of each pack; each entry also gets "pack" and "_dir"."""
    global _meta
    if _meta is None:
        _meta = {}
        for name in in_use():
            p = packs.get(name)
            j = os.path.join(p.sprites_dir, "sprites.json")
            if os.path.exists(j):
                for k, m in json.load(open(j, encoding="utf-8")).items():
                    _meta[k] = dict(m, pack=p.name, _dir=p.sprites_dir)
    return _meta


def names(group=None):
    return [n for n, m in meta().items() if group is None or m["group"] == group]


def anims(name):
    return meta()[name]["anims"]


def _sheet(name):
    if name not in _sheets:
        _sheets[name] = Image.open(os.path.join(meta()[name]["_dir"], meta()[name]["file"])).convert("RGBA")
    return _sheets[name]


def frame(name, anim="idle", i=0, flip=False, scale=1):
    key = (name, anim, i, flip, scale)
    if key not in _frames:
        m = meta()[name]
        a = m["anims"][anim]
        cw, ch = m.get("source_cell", m["cell"])
        i = max(0, min(a["frames"] - 1, i))
        im = _sheet(name).crop((i * cw, a["row"] * ch, (i + 1) * cw, (a["row"] + 1) * ch))
        k = scale if scale > 1 else 1
        w, h = m["cell"]
        size = (w * k, h * k)
        if im.size != size:
            im = ImageOps.fit(im, size, Image.Resampling.NEAREST)
        if flip:
            im = im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
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
    ax, ay = meta()[name]["anchor"]
    if flip:
        ax = meta()[name]["cell"][0] - ax
    img.paste(im, (int(round(x - ax * scale)), int(round(y - ay * scale))), im)
    return im


def idle(img, name, t, x, y, seed=0, flip=False, scale=1, blink_every=2.3):
    """Rest with a bob and a rare blink (if the sprite has "blink")."""
    a = anims(name)
    if "blink" in a and ((t + seed * 0.37) % blink_every) < 0.1:
        return draw(img, name, "blink", 0, x, y, flip, scale)
    return draw(img, name, "idle", t + seed * 0.17, x, y, flip, scale)


def ghost(rgba, k=1, origin=(0, 0)):
    """The ghost of drawn sprites (an RGBA array, transparent around them): a pale silhouette, half see-through
    (a checker of LGREY on the grid of sprite pixels, k frame pixels each, from origin: the corner of the sprite),
    with a DGREY outline k pixels wide.
    Any sprite has one; no ghost frames are drawn by hand."""
    import numpy as np
    from .palette import C, LGREY, DGREY
    a = rgba[..., 3] > 0
    inner = a.copy()
    for _ in range(max(1, k)):                       # erode by k: what stays is inside the outline
        e = inner.copy()
        e[1:] &= inner[:-1]; e[:-1] &= inner[1:]; e[:, 1:] &= inner[:, :-1]; e[:, :-1] &= inner[:, 1:]
        e[0] = e[-1] = False; e[:, 0] = e[:, -1] = False
        inner = e
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    out = np.zeros_like(rgba)
    k1 = max(1, k)
    out[inner & (((xx - origin[0]) // k1 + (yy - origin[1]) // k1) % 2 == 0)] = (*C(LGREY), 255)
    out[a & ~inner] = (*C(DGREY), 255)
    return out
