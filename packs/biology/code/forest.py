# Forest: tree seedlings (paper birch, Douglas fir, western redcedar), their roots with or without a
# fungal mantle, a strand of fungal threads, a tracer gas puff, a shade cloth, and tracer tags.
# Trees have no faces: the story is about carbon, not about what a tree wants.
# A tree sprite stands on its bottom row (the ground line); its roots are a separate sprite.

import math
import numpy as np
from pixel_kit.palette import *
from pixel_kit.pixdraw import Spr, mask_circle

TW, TH = 20, 36          # tree canvas


def _trunk(s, x0, x1, y0, y1, body, mark=None, every=3):
    s.rect(x0, y0, x1, y1, body)
    if mark is not None:
        for y in range(y0 + 1, y1, every):
            s.put(x0 + (y // every) % 2, y, mark)


def birch(sway=0):
    """Paper birch: a white trunk with dark marks, a round light-green crown."""
    s = Spr(TW, TH)
    _trunk(s, 9, 10, 14, TH - 1, WHITE, BLACK)
    s.put(8, 19, WHITE); s.put(7, 18, WHITE)               # a twig
    for cx, cy, r in ((10 + sway, 9, 6.5), (6 + sway, 12, 4.5), (14 + sway, 12, 4.5), (10 + sway, 14, 4.2)):
        s.a[mask_circle(TW, TH, cx, cy, r)] = GREEN
    ys, xs = np.mgrid[0:TH, 0:TW]
    crown = s.a == GREEN
    s.a[crown & ((xs + ys) > 24 + sway) & (ys > 9)] = DGREEN
    for x, y in ((8, 5), (11, 4), (6, 9), (12, 8), (9, 11), (15, 11), (5, 13)):
        if s.get(x + sway, y) == GREEN:
            s.put(x + sway, y, YELLOW)
    return s


def fir(sway=0):
    """Douglas fir: a dark-green cone in tiers, a brown trunk."""
    s = Spr(TW, TH)
    _trunk(s, 9, 10, 26, TH - 1, BROWN)
    tiers = [(1, 8, 4), (6, 15, 6), (12, 22, 8), (18, 28, 9)]   # top row, bottom row, half width at the bottom
    for i, (y0, y1, hw) in enumerate(tiers):
        for y in range(y0, y1 + 1):
            k = (y - y0 + 1) / (y1 - y0 + 1)
            w = max(1, round(hw * k))
            off = round(sway * (1 - y / TH))
            s.rect(10 - w + off, y, 9 + w + off, y, DGREEN)
            s.put(10 - w + off, y, DGREEN)
            if w > 2:
                s.put(9 + w + off, y, NAVY if y == y1 else DGREEN)
        for x in range(10 - hw, 10 + hw, 3):                  # light tips at the lower edge of a tier
            if s.get(x, y1) == DGREEN:
                s.put(x, y1, GREEN)
    s.put(10 + round(sway), 0, DGREEN); s.put(9 + round(sway), 0, DGREEN)
    return s


def cedar(sway=0):
    """Western redcedar: a broad, soft cone of drooping light-green sprays, a red-brown trunk at the base."""
    s = Spr(TW, TH)
    _trunk(s, 9, 10, 27, TH - 1, ORANGE, BROWN, every=2)
    for y in range(2, 29):
        k = (y - 1) / 28
        hw = max(1, round(1 + 8.5 * k ** 0.8))
        off = round(sway * (1 - y / TH))
        s.rect(10 - hw + off, y, 9 + hw + off, y, GREEN)
    for y0 in range(6, 29, 5):                                  # drooping spray tips on each side
        k = (y0 - 1) / 28
        hw = max(1, round(1 + 8.5 * k ** 0.8))
        for side in (-1, 1):
            x = (10 - hw - 1) if side < 0 else (9 + hw + 1)
            s.put(x, y0, GREEN); s.put(x, y0 + 1, DGREEN)
        for x in range(10 - hw + 1, 9 + hw, 2):                 # a darker band under each layer
            s.put(x, y0, DGREEN)
    s.put(10 + sway, 1, GREEN)
    return s


def bag(tree):
    """A sealed clear bag over the tree: a thin pale rim, two glints, a tie near the ground."""
    s = Spr(TW + 6, TH + 2)
    s.stamp(tree, 3, 2)
    x0, x1, y0, y1 = 0, TW + 5, 0, TH - 1
    for x in range(x0 + 2, x1 - 1):
        s.put(x, y0, LGREY)
    for y in range(y0 + 2, y1 - 4):
        s.put(x0, y, LGREY); s.put(x1, y, LGREY)
    s.put(x0 + 1, y0 + 1, LGREY); s.put(x1 - 1, y0 + 1, LGREY)
    for k in range(5):                                         # the bag narrows to the tie
        s.put(x0 + 1 + k * 2, y1 - 4 + k, LGREY); s.put(x0 + 2 + k * 2, y1 - 4 + k, LGREY)
        s.put(x1 - 1 - k * 2, y1 - 4 + k, LGREY); s.put(x1 - 2 - k * 2, y1 - 4 + k, LGREY)
    s.rect(11, y1 + 1, 14, y1 + 1, DGREY)                      # the tie
    for x, y in ((3, 4), (3, 5), (4, 3), (21, 8), (21, 9)):
        s.put(x, y, WHITE)
    return s


def roots(mantle=True, h=18):
    """Roots below the trunk. mantle: white fungal sheaths (ectomycorrhiza) on the root tips;
    else bare peach root tips with small lavender dots inside (another kind of fungus)."""
    w = 28
    s = Spr(w, h)
    s.rect(13, 0, 14, h - 5, BROWN)
    tips = [(13, h - 3)]
    for side in (-1, 1):
        for k, (dx, dy) in enumerate(((11, 5), (6, 11))):
            x0 = 13.5 + side * 0.5
            for j in range(0, 25):
                f = j / 24
                s.put(x0 + side * dx * f, 1 + k * 3 + dy * f * f + 1.5 * f, BROWN)
            tips.append((round(x0 + side * dx), round(1 + k * 3 + dy + 1.5)))
    for x, y in tips:
        if mantle:
            s.rect(x - 1, y, x + 1, y + 2, WHITE)
        else:
            s.rect(x - 1, y, x + 1, y + 1, PEACH)
            s.put(x, y + 1, LAV)
    return s


def hyphae(length=64, grow=1.0, seed=3):
    """A strand of fungal threads, wavy white lines with branches; grow: 0..1 reveals it from the middle."""
    h = 12
    s = Spr(length, h)
    rnd = np.random.default_rng(seed)
    mid = length / 2
    for line in range(3):
        ph = rnd.random() * 6.3
        amp = 1.5 + line * 0.8
        y0 = 4 + line * 2
        for x in range(length):
            if abs(x - mid) > mid * grow:
                continue
            y = y0 + amp * math.sin(x / (5 + line) + ph)
            s.put(x, round(y), WHITE if line != 1 else LGREY)
        for x in range(4 + line * 5, length - 2, 14):
            if abs(x - mid) > mid * grow:
                continue
            y = y0 + amp * math.sin(x / (5 + line) + ph)
            for j in range(1, 3):
                s.put(x + j, round(y) + (j if line % 2 else -j), LGREY)
    return s


def gas(col, k=0):
    """A puff of tracer gas: three round blobs in one color; k: 0..1 frame of a slow drift."""
    s = Spr(14, 10)
    for cx, cy, r in ((4, 6, 3.2), (8, 4, 3.6), (10, 6.5, 2.6)):
        s.a[mask_circle(14, 10, cx + k, cy, r)] = col
    s.put(7 + k, 2, WHITE); s.put(6 + k, 3, WHITE)
    return s


def shade_cloth():
    """A shade frame: two posts and a dark mesh roof over a small tree."""
    w, h = 30, 40
    s = Spr(w, h)
    for x in (1, w - 2):
        s.rect(x, 2, x, h - 1, BROWN)
    for y in range(0, 6):
        for x in range(0, w):
            if (x + y) % 2 == 0:
                s.put(x, y, DGREY)
            elif y in (0, 5):
                s.put(x, y, NAVY)
    for y in range(6, 14):                                   # the cloth hangs down at the sides
        for x in (0, 2, w - 3, w - 1):
            if (x + y) % 2 == 0:
                s.put(x, y, DGREY)
    return s


_DIGITS = {"1": ["X", "X", "X", "X", "X"], "3": ["XX", ".X", "XX", ".X", "XX"], "4": ["X.X", "X.X", "XXX", "..X", "..X"],
           "C": ["XX", "X.", "X.", "X.", "XX"], "+": ["...", ".X.", "XXX", ".X.", "..."]}


def tag(text, col, big=False, faint=False):
    """A tracer tag: a rounded label with the isotope (14C, 13C). big: a "+" mark; faint: a pale tag (a trace)."""
    glyphs = [_DIGITS[ch] for ch in text + ("+" if big else "")]
    tw = sum(len(g[0]) + 1 for g in glyphs) - 1
    w, h = tw + 4, 9
    s = Spr(w, h)
    fill = LGREY if faint else col
    ink = col if faint else WHITE
    s.rect(1, 0, w - 2, h - 1, fill)
    s.rect(0, 1, w - 1, h - 2, fill)
    x = 2
    for g in glyphs:
        for j, row in enumerate(g):
            for i, ch in enumerate(row):
                if ch == "X":
                    s.put(x + i, 2 + j, ink)
        x += len(g[0]) + 1
    return s
