# Load sprites and animations by name from sprites/*.png + sprites/sprites.json.
#
#   from pixel_kit import sprites as S
#   S.draw(img, "nk", "idle", t, x, y)           animation frame at time t (s)
#   S.draw(img, "tumor", "death", t - t0, x, y)  a one-shot animation stops on its last frame
#   S.frame("nk", "attack", 2)                   one frame (RGBA)
#   S.draw(..., flip=True, scale=3)              mirror / portrait x3
#
# (x, y) is the anchor (cell center = body center).

import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPR_DIR = os.path.join(ROOT, "sprites")

_meta = None
_sheets = {}
_frames = {}


def meta():
    global _meta
    if _meta is None:
        _meta = json.load(open(os.path.join(SPR_DIR, "sprites.json")))
    return _meta


def names(group=None):
    return [n for n, m in meta().items() if group is None or m["group"] == group]


def anims(name):
    return meta()[name]["anims"]


def _sheet(name):
    if name not in _sheets:
        _sheets[name] = Image.open(os.path.join(SPR_DIR, meta()[name]["file"])).convert("RGBA")
    return _sheets[name]


def frame(name, anim="idle", i=0, flip=False, scale=1):
    key = (name, anim, i, flip, scale)
    if key not in _frames:
        m = meta()[name]
        a = m["anims"][anim]
        cw, ch = m["cell"]
        i = max(0, min(a["frames"] - 1, i))
        im = _sheet(name).crop((i * cw, a["row"] * ch, (i + 1) * cw, (a["row"] + 1) * ch))
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
