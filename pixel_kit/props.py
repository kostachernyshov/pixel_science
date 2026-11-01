# Props: syringe, vial, Petri dish, mouse (top and side), DNA, glucose, pill,
# granules (perforin), antibody. Lab and data props: tube, plate, sequencer, table.

import math
import numpy as np
from PIL import ImageDraw
from .palette import *
from .pixdraw import Spr, mask_circle, mask_radial, mask_superellipse, paint_body, outline


def syringe(liquid=BLUE):
    """Syringe from the side, needle to the right. 26x5."""
    s = Spr(26, 5)
    s.ascii(0, 0, [
        "L.........................",
        "L.WWWWWWWWWWWW............",
        "LLWccccccccccWLLLLLLLLLLL.",
        "L.WWWWWWWWWWWW............",
        "L.........................",
    ], {"L": LGREY, "W": WHITE, "c": liquid})
    return s


def vial(liquid=BLUE):
    """Vial (antiserum, drug), 8x10."""
    s = Spr(8, 10)
    s.ascii(0, 0, ["..5555..", "..6666..", "...77...", "..7..7..", ".7....7.",
                   ".7cccc7.", ".7cccc7.", ".7cccc7.", ".7cccc7.", "..7777.."],
            {"5": DGREY, "6": LGREY, "7": WHITE, "c": liquid})
    return s


def dish(cells=0):
    """Petri dish from the top, 24x24. cells: number of colony dots."""
    S = 24
    s = Spr(S, S)
    m = mask_circle(S, S, 12, 12, 11.5)
    s.a[m] = LGREY
    s.a[mask_circle(S, S, 12, 12, 10.5)] = DGREY
    s.a[mask_circle(S, S, 12, 12, 9.5)] = PEACH
    for (x, y) in [(7, 5), (6, 6), (5, 7)]:
        s.put(x, y, WHITE)
    for (x, y) in [(15, 10), (9, 15), (13, 16), (16, 14), (10, 9), (8, 12)][:cells]:
        s.put(x, y, PLUM); s.put(x + 1, y, PLUM)
    return s


def mouse_top():
    """Mouse from the top (head up), 18x34."""
    w, h = 18, 34
    s = Spr(w, h)
    for k in range(26, h):
        s.put(9 + round(1.5 * math.sin((k - 26) / 2.0)), k, PINK)
    for (x, y) in [(2, 12), (15, 12), (3, 22), (14, 22)]:
        s.rect(x, y, x, y + 1, PINK)
    m = mask_superellipse(w, h, 9, 17.5, 6.5, 9.0, n=2.2)
    paint_body(s, m, 9, 17.5, LGREY, DGREY, shade=None, hi=WHITE)
    for ex in (4, 14):
        e = mask_circle(w, h, ex + 0.5, 5.5, 2.6)
        s.a[e] = LGREY
        s.a[mask_circle(w, h, ex + 0.5, 5.5, 1.4)] = PINK
    hm = mask_radial(w, h, 9.0, 7.0, lambda a: 4.4 + 1.6 * np.maximum(0, -np.sin(a)) ** 4)
    paint_body(s, hm, 9.0, 7.0, LGREY, DGREY)
    s.put(7, 6, BLACK); s.put(11, 6, BLACK)
    s.put(9, 1, PINK)
    return s


def mouse_side():
    """Mouse from the side (nose to the right), 30x16."""
    w, h = 30, 16
    s = Spr(w, h)
    for k in range(8):
        s.put(k, 6 + round(4 * (k / 7) ** 2), PINK)
    for x in (10, 18):
        s.rect(x, 13, x + 1, 14, PINK)
    m = mask_superellipse(w, h, 15, 9, 8.5, 5.0, n=2.2)
    m |= mask_radial(w, h, 23.0, 8.0, lambda a: 4.0 + 2.0 * np.maximum(0, np.cos(a)) ** 6)
    paint_body(s, m, 15, 9, LGREY, DGREY, shade=None, hi=WHITE)
    s.a[mask_circle(w, h, 21.5, 3.5, 2.6)] = LGREY
    s.a[mask_circle(w, h, 21.5, 3.5, 1.4)] = PINK
    s.put(25, 7, BLACK)
    s.put(29, 8, PINK)
    return s


def dna(mutated=False):
    """Double helix, 9x16. mutated: one rung has a mutation mark."""
    s = Spr(9, 16)
    for y in range(16):
        k = math.sin(y * 0.55)
        x1, x2 = round(4 + 3.4 * k), round(4 - 3.4 * k)
        if y % 2 == 0 and abs(x1 - x2) > 1:
            for x in range(min(x1, x2) + 1, max(x1, x2)):
                s.put(x, y, ORANGE if (mutated and y == 8) else DGREY)
        front = k > 0
        s.put(x2, y, LAV if front else DGREY)
        s.put(x1, y, WHITE if front else LGREY)
    if mutated:
        s.put(0, 7, ORANGE); s.put(8, 9, ORANGE)
    return s


def glucose():
    """Glucose molecule: a resource. Hexagon 7x7."""
    s = Spr(7, 7)
    s.ascii(0, 0, ["..www..", ".w...w.", "w.....w", "w.....w", "w.....w", ".w...w.", "..www.."], {"w": WHITE})
    return s


def pill(col=ORANGE):
    """Pill (inhibitor), 10x5."""
    s = Spr(10, 5)
    s.ascii(0, 0, [".kkkkkkkk.", "kwwwwcccck", "kwwwwcccck", "kwwwwcccck", ".kkkkkkkk."],
            {"k": BLACK, "w": WHITE, "c": col})
    return s


def granule(col=BLUE, k=0):
    """Granule (perforin, granzymes): the shot of an immune cell. 3 pulse frames, 5x5."""
    s = Spr(5, 5)
    if k == 0:
        s.ascii(0, 0, [".....", "..c..", ".cwc.", "..c..", "....."], {"c": col, "w": WHITE})
    elif k == 1:
        s.ascii(0, 0, ["..c..", ".cwc.", "cwwwc", ".cwc.", "..c.."], {"c": col, "w": WHITE})
    else:
        s.ascii(0, 0, [".....", ".c.c.", "..w..", ".c.c.", "....."], {"c": col, "w": WHITE})
    return s


def antibody_bonus(k=0):
    """Antibody drug (checkpoint inhibitor) as a bonus item. 2 sparkle frames, 11x11."""
    s = Spr(11, 11)
    s.ascii(0, 0, [
        "w.......w..",
        "bw.....wb..",
        ".bw...wb...",
        "..bw.wb....",
        "...bwb.....",
        "....w......",
        "....w......",
        "....w......",
        "....b......",
        "...........",
        "...........",
    ], {"w": WHITE, "b": BLUE})
    if k == 0:
        s.put(8, 8, YELLOW); s.put(9, 7, YELLOW); s.put(9, 8, YELLOW); s.put(9, 9, YELLOW); s.put(10, 8, YELLOW)
    else:
        s.put(9, 8, WHITE)
    return s


def chromosome(kind="normal"):
    """Chromosome 5x11: normal; "ph": the small Philadelphia chromosome."""
    if kind == "ph":
        s = Spr(5, 6)
        s.ascii(0, 0, [".ll..", "llll.", ".ol..", "llll.", ".ll..", "....."], {"l": LGREY, "o": ORANGE})
        return s
    s = Spr(5, 11)
    s.ascii(0, 0, [".ll..", "llll.", "llll.", "llll.", ".ll..", ".ll..", "llll.", "llll.", "llll.", "llll.", ".ll.."],
            {"l": LGREY})
    return s


# ---------------------------------------------------------------- lab and data props

def tube(liquid=BLUE):
    """Sample tube with a cap, 7x16."""
    s = Spr(7, 16)
    s.rect(0, 0, 6, 2, DGREY)
    s.rect(1, 3, 5, 12, WHITE)
    s.rect(2, 13, 4, 14, WHITE)
    s.put(3, 15, WHITE)
    s.rect(1, 8, 5, 12, liquid)
    s.rect(2, 13, 4, 14, liquid)
    s.put(2, 4, LGREY); s.put(2, 5, LGREY)
    outline(s, BLACK)
    return s


def plate(filled=()):
    """Well plate from the top, 8x12 wells of 2 px, 37x27. filled: {(row, col): color}."""
    s = Spr(37, 27)
    s.rect(0, 0, 36, 26, LGREY)
    s.rect(1, 1, 35, 25, WHITE)
    fill = dict(filled)
    for r in range(8):
        for c in range(12):
            x, y = 2 + c * 3, 2 + r * 3
            s.rect(x, y, x + 1, y + 1, fill.get((r, c), LGREY))
    outline(s, BLACK)
    return s


def sequencer(on=True):
    """Sequencer: a box with a screen and a flow-cell slot, 24x18."""
    s = Spr(24, 18)
    s.rect(0, 0, 23, 17, WHITE)
    s.rect(0, 15, 23, 17, LGREY)
    s.rect(2, 2, 12, 8, NAVY)
    if on:
        for k, col in enumerate((XBLUE, GREEN, ORANGE, BLUE)):
            s.rect(3 + k * 2, 4 + (k % 2), 3 + k * 2, 7, col)
    s.rect(15, 4, 21, 5, DGREY)
    s.rect(15, 9, 21, 9, LGREY)
    s.put(20, 12, GREEN if on else DGREY)
    outline(s, BLACK)
    return s


def datasheet(rows=5):
    """Data table icon: header and rows, 17x13."""
    s = Spr(17, 13)
    s.rect(0, 0, 16, 12, WHITE)
    s.rect(0, 0, 16, 2, NAVY)
    for r in range(rows):
        y = 4 + r * 2
        if y > 11:
            break
        s.rect(1, y, 4, y, LGREY); s.rect(6, y, 10, y, LGREY); s.rect(12, y, 15, y, LGREY)
    outline(s, BLACK)
    return s
