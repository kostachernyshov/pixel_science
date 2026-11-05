"""Base water and weather assets. One drawing per object, independent of style."""
import math
from pixel_kit.palette import *
from pixel_kit.pixdraw import Spr, mask_circle, mask_superellipse, mask_capsule, paint_body, outline


def sun():
    s = Spr(32, 32)
    for i in range(8):
        a = i*math.tau/8
        for r in range(11, 14):
            x, y = round(16+r*math.cos(a)), round(16+r*math.sin(a))
            s.rect(x, y, x+1, y+1, ORANGE)
    paint_body(s, mask_circle(32, 32, 16, 16, 8), 16, 16, YELLOW, ORANGE, hi=WHITE)
    outline(s)
    return s


def cloud():
    s = Spr(34, 23)
    for x, y, r in ((9, 13, 7), (17, 9, 8), (26, 13, 6)):
        s.a[mask_circle(34, 23, x, y, r)] = WHITE
    s.rect(7, 12, 27, 18, WHITE)
    s.rect(8, 17, 26, 18, LGREY)
    outline(s)
    return s


def water_drop():
    s = Spr(18, 24)
    s.a[mask_circle(18, 24, 9, 15, 6)] = BLUE
    for y in range(3, 16):
        hw = max(0, (y-3)//2)
        s.rect(9-hw, y, 9+hw, y, BLUE)
    s.rect(6, 12, 7, 16, WHITE)
    s.rect(10, 19, 12, 19, NAVY)
    outline(s)
    return s


def snowflake():
    s = Spr(28, 28)
    for i in range(6):
        a = i*math.tau/6
        for r in range(11):
            s.put(round(14+r*math.cos(a)), round(14+r*math.sin(a)), WHITE)
        for r in (6, 9):
            bx, by = 14+r*math.cos(a), 14+r*math.sin(a)
            for sign in (-1, 1):
                for j in range(4):
                    aa = a+sign*math.pi/3+math.pi
                    s.put(round(bx+j*math.cos(aa)), round(by+j*math.sin(aa)), BLUE)
    outline(s)
    return s


def ice():
    s = Spr(28, 28)
    s.rect(5, 8, 21, 23, BLUE)
    s.rect(8, 4, 24, 19, LGREY)
    s.rect(8, 4, 24, 7, WHITE)
    for k in range(4):
        s.rect(5+k, 8-k, 7+k, 8-k, WHITE)
        s.put(22+k, 23-k, NAVY)
    s.rect(11, 9, 12, 16, WHITE)
    s.rect(15, 16, 17, 17, WHITE)
    outline(s)
    return s


def water_pool():
    s = Spr(42, 20)
    m = mask_superellipse(42, 20, 21, 10, 18, 6, n=2.5)
    paint_body(s, m, 21, 10, BLUE, NAVY, hi=WHITE)
    s.rect(10, 8, 25, 8, WHITE)
    s.rect(19, 12, 31, 12, LGREY)
    outline(s)
    return s


def river():
    """A bend of water, no baked terrain or setting."""
    s = Spr(42, 32)
    pts = [(6, 3), (15, 8), (28, 11), (29, 19), (20, 23), (27, 29)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.a[mask_capsule(42, 32, x0, y0, x1, y1, 3.5)] = BLUE
    for x, y in ((12, 7), (24, 10), (25, 21)):
        s.rect(x, y, x+3, y, WHITE)
    outline(s)
    return s


def soil(wet=False):
    """A soil section. Blue pores in the lower layer indicate saturation, not a cavern."""
    s = Spr(36, 30)
    s.rect(3, 4, 32, 25, BROWN)
    s.rect(3, 4, 32, 7, DGREY)
    s.rect(3, 19, 32, 25, PEACH)
    for x, y in ((7, 11), (15, 9), (25, 13), (10, 16), (29, 16)):
        s.put(x, y, PEACH)
    for x, y in ((7, 22), (13, 20), (19, 23), (25, 21), (30, 23)):
        s.rect(x, y, x+1, y+1, BLUE if wet else BROWN)
    outline(s)
    return s


def build():
    out = {}
    for fn in (sun, cloud, water_drop, snowflake, ice, water_pool, river, soil):
        out[fn.__name__] = {'group': 'prop', 'anims': {
            'idle': {'frames': [(fn(), 0, 0)], 'fps': 1, 'loop': True}}}
    out['soil']['anims']['wet'] = {'frames': [(soil(True), 0, 0)], 'fps': 1, 'loop': True}
    return out
