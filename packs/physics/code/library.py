# Physics sprites drawn in code: particles with faces, a detector. build() -> {name: spec}.
# Same rules as every pack: palette indices only, 1 px outline added by the sheet builder,
# one row per animation. Colors and roles: packs/physics/bible.md.

import math
import numpy as np
from pixel_kit.palette import *
from pixel_kit.pixdraw import Spr, mask_circle, paint_body, scale, silhouette, polar


def F(s, dx=0, dy=0):
    return (s, dx, dy)


def anim(frames, fps=6, loop=True):
    return {"frames": frames, "fps": fps, "loop": loop}


def face(s, cx, cy, gap=4, blink=False, wow=False, brow=None):
    """Two eyes of one pixel column; wow: open mouth (surprise)."""
    for ex in (cx - gap // 2 - 1, cx + gap // 2):
        if brow is not None:
            s.put(ex, cy - 2, brow)
        if blink:
            s.put(ex, cy + 1, BLACK)
        else:
            s.put(ex, cy, BLACK)
            s.put(ex, cy + 1, BLACK)
    if wow:
        s.put(cx - 1 + (gap % 2 == 0), cy + 3, BLACK)


def ball(size, r, body, rim, shade=None, hi=WHITE, blink=False, wow=False, gap=4, brow=None, dots=()):
    s = Spr(size, size)
    c = size / 2
    m = mask_circle(size, size, c, c, r)
    paint_body(s, m, c, c, body, rim, shade=shade, hi=hi)
    for (x, y, col) in dots:
        s.put(x, y, col)
    face(s, int(c), int(c) - 1, gap=gap, blink=blink, wow=wow, brow=brow)
    return s


def proton(blink=False, wow=False):
    # three quarks inside: two up (PINK), one down (GREEN)
    return ball(20, 7.6, WHITE, ORANGE, shade=LGREY, blink=blink, wow=wow, gap=5, brow=BROWN,
                dots=[(6, 13, PINK), (13, 13, PINK), (10, 15, GREEN)])


def electron(blink=False, wow=False):
    return ball(14, 5.4, WHITE, BLUE, shade=LGREY, blink=blink, wow=wow, gap=3)


def top_quark(blink=False, wow=False):
    """A heavy particle (the top quark): large, plum rim."""
    return ball(26, 10.6, WHITE, PLUM, shade=LGREY, blink=blink, wow=wow, gap=6, brow=PLUM)


def higgs(blink=False, wow=False, glow=False):
    s = ball(22, 8.6, YELLOW, ORANGE, shade=ORANGE if not glow else YELLOW, hi=WHITE, blink=blink, wow=wow, gap=5,
             brow=BROWN)
    if glow:
        for k in range(8):
            x, y = polar(11, 11, k * math.pi / 4, 10.5)
            s.put(x, y, YELLOW)
    return s


def photon(k=0):
    """A wave packet: a short yellow zigzag with a bright head. No face: light is not a character."""
    s = Spr(14, 7)
    for x in range(12):
        y = 3 + int(round(2 * math.sin((x + k * 2) * math.pi / 3)))
        s.put(x, y, YELLOW if x < 10 else WHITE)
    s.rect(11, 2, 13, 4, YELLOW)
    s.put(12, 3, WHITE)
    return s


def flash(k):
    """Collision flash: a star that grows and fades."""
    size = 24
    s = Spr(size, size)
    c = size // 2
    r = [3, 7, 10, 6][k]
    col = [WHITE, YELLOW, ORANGE, ORANGE][k]
    for a in range(8):
        for t in range(r):
            x, y = polar(c, c, a * math.pi / 4, t)
            s.put(x, y, col if t < r - 1 else ORANGE)
    s.a[mask_circle(size, size, c, c, max(1.5, r / 3))] = WHITE if k < 3 else YELLOW
    return s


def detector(lit=None):
    """Cross-section of a detector: beam pipe, tracker, calorimeter, muon layer (rings).
    lit: index of a lit calorimeter cell (0-11) or None."""
    S_ = 64
    s = Spr(S_, S_)
    c = S_ / 2
    ys, xs = np.mgrid[0:S_, 0:S_]
    d = np.hypot(xs + 0.5 - c, ys + 0.5 - c)
    ang = (np.arctan2(ys + 0.5 - c, xs + 0.5 - c) + 2 * np.pi) % (2 * np.pi)
    s.a[(d <= 31) & (d > 27)] = DGREY                      # muon layer
    seg_ = (ang // (np.pi / 12)).astype(int) % 2 == 0
    s.a[(d <= 27) & (d > 26)] = BLACK
    s.a[(d <= 26) & (d > 19) & seg_] = LAV                 # calorimeter cells
    s.a[(d <= 26) & (d > 19) & ~seg_] = NAVY
    if lit is not None:
        cell = (ang // (np.pi / 6)).astype(int) == lit
        s.a[(d <= 26) & (d > 19) & cell] = YELLOW
    s.a[(d <= 19) & (d > 18)] = BLACK
    s.a[(d <= 18) & (d > 3)] = LGREY                       # tracker
    for r in (6, 10, 14):
        s.a[(np.abs(d - r) < 0.5)] = DGREY
    s.a[d <= 3] = WHITE                                    # beam pipe
    s.a[(d <= 3) & (d > 2)] = DGREY
    return s


SPRITES = {}


def register(name, anims, group):
    SPRITES[name] = {"anims": anims, "group": group}


def character(gen, extra=None):
    d = {
        "idle": anim([F(gen()), F(gen(), 0, -1)], fps=3),
        "blink": anim([F(gen(blink=True))], fps=1),
        "wow": anim([F(gen(wow=True)), F(gen(wow=True), 0, -1)], fps=4),
        "hit": anim([F(silhouette(gen(), NAVY)), F(gen())], fps=15, loop=False),
    }
    d.update(extra or {})
    return d


def build():
    SPRITES.clear()
    register("proton", character(proton), "particle")
    register("electron", character(electron), "particle")
    register("top_quark", character(top_quark), "particle")
    register("higgs", character(higgs, {
        "appear": anim([F(flash(1)), F(scale(higgs(), 0.5)), F(higgs(wow=True)), F(higgs(glow=True))], fps=6, loop=False),
        "glow": anim([F(higgs(glow=True)), F(higgs())], fps=4),
        "decay": anim([F(higgs(wow=True)), F(silhouette(higgs(), WHITE)), F(flash(2)), F(flash(3))], fps=8, loop=False),
    }), "particle")
    register("photon", {"idle": anim([F(photon(k)) for k in range(3)], fps=12)}, "particle")
    register("flash", {"idle": anim([F(flash(k)) for k in range(4)], fps=10, loop=False)}, "particle")
    register("detector", {
        "idle": anim([F(detector())], fps=1),
        "hit": anim([F(detector(k)) for k in (0, 6)] + [F(detector())], fps=4, loop=False),
        "two_photons": anim([F(detector(0)), F(detector(6))], fps=3),
    }, "machine")
    return SPRITES
