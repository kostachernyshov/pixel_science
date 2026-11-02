# Effects: particles, hit flash, "!" before an attack, "z" for a blocked cell, drug wave,
# granule shot, chemokine trail, sparkle, Bayer dither transitions.
# Division and apoptosis are sprite animations ("divide", "death"), see sprites.py.

import math, random
import numpy as np
from PIL import ImageDraw
from .palette import *
from .font import text
from .timing import clamp, seg, ease, lerp
from . import sprites as S


def particles(img, x0, y0, t, seed, cols=(PINK, ORANGE, NAVY, PLUM), life=0.7, n=14):
    """Particles fly out. For a hit, a loss of molecules, a bonus."""
    if t < 0 or t > life:
        return
    rnd = random.Random(seed)
    for _ in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        v = rnd.uniform(25, 70)
        col = rnd.choice(cols)
        x = x0 + math.cos(a) * v * t
        y = y0 + math.sin(a) * v * t + 40 * t * t
        if rnd.random() < 1 - t / life:
            sz = 2 if t < life * 0.6 else 1
            ImageDraw.Draw(img).rectangle([int(x), int(y), int(x) + sz - 1, int(y) + sz - 1], fill=C(col))


def hit_flash(img, x, y, t, col=NAVY, r0=4, life=0.25):
    """Hit flash: a cross and a ring that grows, 0.25 s."""
    if t < 0 or t > life:
        return
    d = ImageDraw.Draw(img)
    k = t / life
    r = int(r0 + 10 * k)
    if k < 0.5:
        L = int(6 + 6 * k)
        d.line([x - L, y, x + L, y], fill=C(col))
        d.line([x, y - L, x, y + L], fill=C(col))
    d.ellipse([x - r, y - r, x + r, y + r], outline=C(col if k < 0.6 else LGREY))


def alert(img, x, y, t=0.0):
    """"!" above a cell before an attack (hold >= 0.4 s)."""
    text(img, int(x), int(y - 22 - (1 if int(t * 8) % 2 else 0)), "!", ORANGE, align="c", outline=True)


def zzz(img, x, y, t, col=DGREY):
    """"z" for a blocked immune cell. Not for senescent cells: they have a beard."""
    zt = t % 1.2
    text(img, int(x + 6 + zt * 6), int(y - 14 - zt * 10), "z", col, shadow=None)


def wave(img, cx, cy, t, speed=260, cols=(XBLUE, LAV, BLUE), maxr=520):
    """Drug or antiserum wave: three concentric rings."""
    r = t * speed
    if r <= 0 or r >= maxr:
        return
    d = ImageDraw.Draw(img)
    for i, col in enumerate(cols):
        rr = r - 4 * i
        if rr > 0:
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=C(col))


def shot(img, x0, y0, x1, y1, t, dur=0.35, kind="granule_blue"):
    """Granule shot (perforin, granzymes) from an immune cell to a target; True when it arrives."""
    if t < 0:
        return False
    k = clamp(t / dur)
    if k >= 1:
        return True
    x, y = lerp(x0, x1, ease(k)), lerp(y0, y1, ease(k)) - 6 * math.sin(math.pi * k)
    S.draw(img, kind, "idle", t, x, y)
    return False


def trail(img, pts, t, col=PLUM, gap=6, speed=20):
    """Chemokine trail (a "come here" signal): running dots along the polyline pts."""
    d = ImageDraw.Draw(img)
    segs = list(zip(pts, pts[1:]))
    total = sum(math.dist(a, b) for a, b in segs)
    off = (t * speed) % gap
    s = off
    while s < total:
        acc = 0
        for a, b in segs:
            L = math.dist(a, b)
            if acc + L >= s:
                k = (s - acc) / L
                x, y = lerp(a[0], b[0], k), lerp(a[1], b[1], k)
                d.point([int(x), int(y)], fill=C(col))
                break
            acc += L
        s += gap


def sparkle(img, x, y, t, col=ORANGE):
    """Sparkle: a blinking plus 5x5 (bonus, finding)."""
    if int(t * 6) % 2:
        return
    d = ImageDraw.Draw(img)
    d.line([x - 2, y, x + 2, y], fill=C(col))
    d.line([x, y - 2, x, y + 2], fill=C(col))
    d.point([x, y], fill=C(INK))


def border_flash(img, top=0, col=NAVY, width=3):
    """Frame border flash (the moment a drug is given)."""
    ImageDraw.Draw(img).rectangle([0, top, img.width, img.height], outline=C(col), width=width)


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])


def bayer(h, w):
    return np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]


_bayer_cache = {}


def dither_to(arr, a, col=PAPER):
    """Dissolve to one color with a Bayer matrix (a=0: none, a=1: all col). arr is HxWx3."""
    if a <= 0:
        return arr
    h, w = arr.shape[:2]
    if (h, w) not in _bayer_cache:
        _bayer_cache[(h, w)] = bayer(h, w)
    arr[_bayer_cache[(h, w)] < a * 16] = C(col)
    return arr


def dither_mix(arr_a, arr_b, k):
    """Stepped transition from frame A to frame B (k from 0 to 1), no transparency."""
    h, w = arr_a.shape[:2]
    if (h, w) not in _bayer_cache:
        _bayer_cache[(h, w)] = bayer(h, w)
    out = arr_a.copy()
    m = _bayer_cache[(h, w)] < k * 16
    out[m] = arr_b[m]
    return out
