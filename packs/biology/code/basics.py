"""Shared base drawings for molecules, organelles, labs, organs, and organisms.

PICO-8 indices, binary transparency, and the same detail scale as the original cast.
Shapes are schematic identifiers, not atomic structures or anatomical measurements.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

from pixel_kit.palette import *
from pixel_kit.pixdraw import (Spr, mask_circle, mask_superellipse, mask_radial,
                               mask_capsule, paint_body, outline)
from . import props


def _line(s, points, col, width=1):
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        n = max(1, int(max(abs(x1-x0), abs(y1-y0))))
        for j in range(n+1):
            x, y = round(x0+(x1-x0)*j/n), round(y0+(y1-y0)*j/n)
            s.rect(x-width//2, y-width//2, x+(width-1)//2, y+(width-1)//2, col)


def _poly(s, points, col):
    mask = Image.new('1', (s.w, s.h))
    ImageDraw.Draw(mask).polygon(points, fill=1)
    s.a[np.asarray(mask, dtype=bool)] = col


def protein():
    s = Spr(22, 20)
    m = mask_radial(22, 20, 11, 10, lambda a: 7+np.sin(3*a)+.7*np.cos(5*a))
    paint_body(s, m, 11, 10, GREEN, DGREEN, shade=DGREEN, hi=LGREY)
    outline(s)
    return s


def rna():
    s = Spr(24, 15)
    points = [(x, round(7+3*math.sin(x*.42))) for x in range(2, 22)]
    _line(s, points, LAV, 2)
    for i in range(2, len(points)-2, 4):
        x, y = points[i]
        s.rect(x, y+2, x+1, y+3, (BLUE, ORANGE)[(i//4)%2])
    outline(s)
    return s


def lipid():
    s = Spr(16, 22)
    _line(s, [(6, 9), (5, 13), (6, 16), (4, 20)], ORANGE, 2)
    _line(s, [(10, 9), (11, 13), (10, 16), (12, 20)], ORANGE, 2)
    m = mask_circle(16, 22, 8, 6, 4)
    paint_body(s, m, 8, 6, BLUE, NAVY, hi=WHITE)
    outline(s)
    return s


def plasmid():
    s = Spr(26, 26)
    outer = mask_circle(26, 26, 13, 13, 10)
    inner = mask_circle(26, 26, 13, 13, 7)
    s.a[outer & ~inner] = LAV
    for j in range(12):
        a = j*math.tau/12
        _line(s, [(13+7*math.cos(a), 13+7*math.sin(a)),
                  (13+10*math.cos(a), 13+10*math.sin(a))], LGREY)
    for j in range(8):
        a = -.7+j*.08
        for r in (8, 9):
            s.put(round(13+r*math.cos(a)), round(13+r*math.sin(a)), ORANGE)
    outline(s)
    return s


def dna_fragment():
    # Reuse the helix drawing rather than inventing another DNA vocabulary.
    src = props.dna()
    s = Spr(src.w+2, 14)
    s.a[2:12, 1:src.w+1] = src.a[3:13]
    return s


def peptide(mutant=False):
    s = Spr(22, 10)
    for i, (x, y) in enumerate(((3, 5), (7, 4), (11, 5), (15, 4), (19, 5))):
        col = ORANGE if mutant and i == 2 else BLUE
        if i:
            _line(s, [(x-3, y), (x, y)], LGREY)
        s.a[mask_circle(22, 10, x, y, 2)] = col
    outline(s)
    if mutant:
        s.put(11, 1, ORANGE)  # A shape cue accompanies the color change.
    return s


def proteasome():
    s = Spr(26, 30)
    s.a[mask_superellipse(26, 30, 13, 15, 9, 12, n=4)] = LAV
    for y in (6, 11, 17, 23):
        s.rect(5, y, 20, y+1, PLUM)
    for x in (8, 13, 18):
        s.rect(x, 7, x, 22, LGREY)
    s.a[mask_superellipse(26, 30, 13, 5, 8, 3, n=2)] = LGREY
    s.a[mask_superellipse(26, 30, 13, 5, 4, 1.5, n=2)] = NAVY
    outline(s)
    return s


def vesicle():
    s = Spr(24, 24)
    outer = mask_circle(24, 24, 12, 12, 9)
    paint_body(s, outer, 12, 12, WHITE, LAV, shade=LGREY)
    for x, y in ((9, 9), (15, 12), (10, 15)):
        s.a[mask_circle(24, 24, x, y, 1.6)] = BLUE
    outline(s)
    return s


def nucleus():
    s = Spr(30, 28)
    m = mask_circle(30, 28, 15, 14, 11, sx=1.07)
    paint_body(s, m, 15, 14, LAV, PLUM, shade=LGREY, hi=WHITE)
    for points in ([(8, 13), (10, 10), (13, 12)], [(17, 8), (20, 10), (18, 13)],
                   [(10, 18), (13, 20), (16, 18)]):
        _line(s, points, PLUM)
    s.a[mask_circle(30, 28, 17, 15, 3)] = PLUM
    outline(s)
    return s


def mitochondrion():
    s = Spr(34, 22)
    m = mask_superellipse(34, 22, 17, 11, 14, 8, n=2.3)
    paint_body(s, m, 17, 11, PEACH, BROWN, hi=WHITE)
    s.a[mask_superellipse(34, 22, 17, 11, 11, 5.5, n=2.3)] = ORANGE
    _line(s, [(7, 11), (10, 7), (12, 14), (15, 7), (18, 14), (21, 7), (24, 14), (27, 11)], BROWN)
    outline(s)
    return s


def ribosome():
    s = Spr(25, 22)
    s.a[mask_superellipse(25, 22, 12, 8, 9, 6, n=2.5)] = LAV
    s.a[mask_superellipse(25, 22, 12, 17, 7, 3, n=2.4)] = PLUM
    _line(s, [(2, 13), (22, 13)], ORANGE)
    _line(s, [(12, 5), (15, 3), (18, 4)], LGREY)
    outline(s)
    return s


def chloroplast():
    s = Spr(34, 22)
    m = mask_superellipse(34, 22, 17, 11, 14, 8, n=2.2)
    paint_body(s, m, 17, 11, GREEN, DGREEN, hi=WHITE)
    for x in (9, 16, 23):
        for y in (7, 10, 13):
            s.rect(x-2, y, x+2, y+1, DGREEN)
    _line(s, [(11, 11), (21, 11)], DGREEN)
    outline(s)
    return s


def bacterium():
    s = Spr(32, 24)
    m = mask_capsule(32, 24, 10, 9, 21, 14, 5.5)
    paint_body(s, m, 16, 12, GREEN, DGREEN, shade=DGREEN, hi=WHITE)
    _line(s, [(11, 11), (14, 9), (17, 13), (21, 12)], DGREEN)
    _line(s, [(26, 15), (29, 18), (27, 21), (30, 22)], DGREEN)
    outline(s)
    return s


def virus():
    """A generic enveloped particle, not a representation of every virus."""
    s = Spr(28, 28)
    for i in range(8):
        a = i*math.tau/8
        _line(s, [(14+9*math.cos(a), 14+9*math.sin(a)),
                  (14+12*math.cos(a), 14+12*math.sin(a))], PINK, 2)
    m = mask_circle(28, 28, 14, 14, 9)
    paint_body(s, m, 14, 14, LAV, PLUM, hi=PINK)
    _line(s, [(11, 10), (16, 12), (12, 16), (17, 18)], PLUM)
    outline(s)
    return s


def pipette():
    s = Spr(12, 34)
    s.ascii(2, 1, [
        '..www...', '..www...', '...k....', '..www...', '.wwwww..',
        '.wcccw..', '.wcccw..', '.wcccw..', '.wcccw..', '.wcccw..',
        '.wcccw..', '.wcccw..', '.wcccw..', '.wwwww..', '..www...',
        '..www...', '..www...', '..www...', '..www...', '...w....',
        '...w....', '...w....', '...w....', '...w....', '...w....',
        '...w....', '...w....',
    ], {'w': WHITE, 'k': DGREY, 'c': BLUE})
    outline(s)
    return s


def microscope():
    s = Spr(30, 34)
    _line(s, [(11, 29), (22, 24), (25, 15), (21, 8)], LGREY, 4)
    _line(s, [(11, 5), (18, 11)], WHITE, 4)
    s.rect(8, 3, 12, 5, NAVY)
    s.rect(16, 11, 20, 13, DGREY)
    s.rect(7, 20, 23, 22, DGREY)
    s.rect(10, 18, 19, 19, BLUE)
    s.rect(12, 26, 18, 28, WHITE)
    s.rect(5, 29, 25, 31, LGREY)
    s.a[mask_circle(30, 34, 24, 19, 2.6)] = NAVY
    outline(s)
    return s


def centrifuge():
    """A small open microcentrifuge, rotor visible for recognition."""
    s = Spr(34, 30)
    s.rect(4, 13, 29, 26, LGREY)
    s.rect(6, 24, 27, 27, DGREY)
    s.a[mask_superellipse(34, 30, 17, 13, 13, 6, n=2.5)] = WHITE
    s.a[mask_superellipse(34, 30, 17, 13, 9, 4, n=2.2)] = NAVY
    for x, y in ((11, 12), (17, 10), (23, 12), (17, 15)):
        s.rect(x-1, y, x+1, y+1, BLUE)
    s.rect(7, 3, 27, 6, WHITE)
    _line(s, [(6, 6), (4, 10)], LGREY, 2)
    s.rect(20, 21, 26, 23, NAVY)
    s.put(26, 19, GREEN)
    outline(s)
    return s


def pcr_machine():
    s = Spr(34, 30)
    s.rect(4, 7, 29, 26, WHITE)
    s.rect(5, 22, 28, 26, LGREY)
    s.rect(7, 3, 26, 10, LGREY)
    s.rect(9, 5, 24, 8, DGREY)
    s.rect(7, 13, 17, 19, NAVY)
    s.rect(9, 15, 14, 16, BLUE)
    for x in (22, 25):
        for y in (14, 18):
            s.rect(x, y, x+1, y+1, DGREY)
    s.put(25, 23, GREEN)
    outline(s)
    return s


def gel(progress=1):
    """Schematic electrophoresis lanes; positions do not encode measured sizes."""
    s = Spr(30, 34)
    s.rect(3, 2, 26, 31, LGREY)
    s.rect(5, 4, 24, 29, NAVY)
    for x in (7, 12, 17, 22):
        s.rect(x-1, 5, x+1, 6, WHITE)
    for lane, rows in enumerate(((10, 15, 21, 26), (13, 22), (10, 18), (16, 25))):
        for row in rows:
            y = 7+round((row-7)*progress)
            x = 7+lane*5
            s.rect(x-1, y, x+1, y, GREEN)
    outline(s)
    return s


def heart():
    """Simplified anatomical organ silhouette, not a valentine symbol."""
    s = Spr(28, 32)
    _line(s, [(12, 10), (12, 3), (16, 3), (17, 7)], RED, 3)
    _line(s, [(20, 13), (23, 6)], BLUE, 3)
    _poly(s, [(7, 9), (16, 8), (23, 13), (22, 21), (16, 28), (11, 25), (5, 18)], RED)
    _line(s, [(8, 14), (11, 11), (15, 12)], PINK, 2)
    _line(s, [(16, 13), (13, 18), (16, 25)], PLUM)
    outline(s)
    return s


def lungs():
    s = Spr(32, 32)
    left = mask_superellipse(32, 32, 9, 19, 6, 10, n=2.3)
    right = mask_superellipse(32, 32, 23, 19, 6, 10, n=2.3)
    s.a[left | right] = PINK
    _line(s, [(16, 3), (16, 13)], WHITE, 3)
    for side in (-1, 1):
        _line(s, [(16, 12), (16+side*6, 17), (16+side*7, 23)], PEACH, 2)
        _line(s, [(16+side*6, 17), (16+side*10, 17)], PEACH)
    outline(s)
    return s


def liver():
    s = Spr(34, 25)
    _poly(s, [(3, 9), (9, 5), (23, 4), (30, 9), (28, 16), (19, 18), (12, 22), (5, 18)], BROWN)
    _poly(s, [(6, 9), (11, 7), (24, 7), (21, 10), (9, 12)], PEACH)
    _line(s, [(20, 9), (17, 15), (18, 18)], PLUM)
    s.a[mask_circle(34, 25, 19, 19, 2)] = DGREEN
    outline(s)
    return s


def brain():
    s = Spr(32, 28)
    m = mask_radial(32, 28, 15, 13, lambda a: 10+np.sin(6*a)*.8, sx=1.23, sy=.83)
    paint_body(s, m, 15, 13, PEACH, PINK, hi=WHITE)
    for pts in ([(7, 11), (10, 8), (13, 10), (12, 14)],
                [(17, 6), (17, 10), (21, 11), (24, 9)],
                [(7, 16), (11, 17), (14, 15), (17, 18)],
                [(22, 14), (24, 16), (22, 19)]):
        _line(s, pts, PINK)
    s.rect(19, 21, 21, 25, PEACH)
    outline(s)
    return s


def zebrafish():
    s = Spr(34, 19)
    _poly(s, [(4, 9), (1, 4), (1, 14)], BLUE)
    m = mask_superellipse(34, 19, 19, 9, 13, 5, n=2)
    paint_body(s, m, 19, 9, LGREY, BLUE, hi=WHITE)
    for y in (7, 10, 13):
        s.rect(9, y, 25, y, NAVY)
    _poly(s, [(16, 4), (20, 1), (24, 4)], BLUE)
    _poly(s, [(15, 14), (20, 17), (23, 14)], BLUE)
    s.put(29, 7, BLACK)
    outline(s)
    return s


def fruit_fly():
    s = Spr(28, 24)
    for cx in (8, 20):
        s.a[mask_superellipse(28, 24, cx, 9, 6, 4, n=2)] = LGREY
    s.a[mask_superellipse(28, 24, 14, 15, 4, 6, n=2)] = BROWN
    for y in (14, 17, 20):
        s.rect(12, y, 16, y, NAVY)
    s.a[mask_circle(28, 24, 14, 7, 3)] = PEACH
    s.put(12, 6, RED);s.put(16, 6, RED)
    for side in (-1, 1):
        for y in (12, 16, 19):
            _line(s, [(14+side*3, y), (14+side*7, y+2)], BROWN)
    outline(s)
    return s


def nematode():
    s = Spr(34, 18)
    pts = [(x, 9+round(4*math.sin((x-3)*.22))) for x in range(3, 31)]
    _line(s, pts, PEACH, 3)
    _line(s, pts[3:-3], WHITE)
    outline(s)
    return s


def seed(stage=0):
    """A seed through germination; no fixed species or growth rate is implied."""
    s = Spr(26, 34)
    m = mask_superellipse(26, 34, 13, 24, 5, 4, n=2.2)
    paint_body(s, m, 13, 24, BROWN, BROWN, hi=PEACH)
    if stage:
        _line(s, [(13, 27), (12, 29), (14, 31)], WHITE)
        _line(s, [(14, 22), (15, 18), (13, 14 if stage > 1 else 18)], DGREEN, 2)
    if stage > 1:
        s.a[mask_superellipse(26, 34, 9, 13, 4, 2.4, n=2)] = GREEN
        s.a[mask_superellipse(26, 34, 18, 11, 4, 2.4, n=2)] = GREEN
    if stage > 2:
        _line(s, [(13, 14), (14, 8)], DGREEN, 2)
        _poly(s, [(14, 8), (17, 3), (22, 3), (21, 7)], GREEN)
    outline(s)
    return s


def leaf():
    s = Spr(28, 26)
    _poly(s, [(3, 19), (4, 10), (10, 4), (23, 2), (24, 12), (18, 20), (9, 22)], GREEN)
    _line(s, [(3, 24), (21, 5)], DGREEN, 2)
    for x, y in ((9, 17), (14, 12), (18, 8)):
        _line(s, [(x, y), (x-3, y-5)], DGREEN)
        _line(s, [(x, y), (x+5, y)], DGREEN)
    outline(s)
    return s


def flower():
    s = Spr(26, 34)
    _line(s, [(13, 16), (13, 30)], DGREEN, 2)
    _poly(s, [(12, 25), (6, 20), (4, 21), (7, 26)], GREEN)
    for i in range(5):
        a = -.3+i*math.tau/5
        s.a[mask_circle(26, 34, 13+5*math.cos(a), 11+5*math.sin(a), 4)] = PINK
    s.a[mask_circle(26, 34, 13, 11, 3)] = YELLOW
    outline(s)
    return s
