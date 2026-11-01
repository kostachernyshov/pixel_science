# People and organs: normal characters at human scale, not cell scale.
# No tumor or immune features: soft colors, dot eyes, blush,
# black outline.

import numpy as np
from .palette import *
from .pixdraw import Spr, mask_circle, mask_superellipse, paint_body, outline

W, H = 18, 30

# hair styles
HAIR = {
    "long": BROWN,
    "bob": ORANGE,
    "short": DGREY,
}


def _hair_mask(style):
    yy, xx = np.mgrid[0:H, 0:W]
    top = mask_circle(W, H, 8.5, 8.5, 6.6) & (yy <= 6)
    if style == "long":
        sides = ((xx <= 3) | (xx >= 13)) & (yy >= 5) & (yy <= 19) & (xx >= 1) & (xx <= 16)
        return top | sides
    if style == "bob":
        sides = ((xx <= 3) | (xx >= 13)) & (yy >= 5) & (yy <= 12) & (xx >= 2) & (xx <= 15)
        return top | sides
    return mask_circle(W, H, 8.5, 8.5, 6.6) & (yy <= 5)


def person(hair="long", top=LAV, blink=False, sick=False, gown=False, ghost=False):
    """Person, front view, 18x30. sick: tired eyes, no blush, a drop of sweat; gown: hospital gown;
    ghost: a memory outline (a person who died), one color, no face."""
    s = Spr(W, H)
    hc = HAIR[hair]
    if gown:
        top = LGREY
    yy, xx = np.mgrid[0:H, 0:W]
    # long hair behind the back
    if hair == "long":
        s.a[((xx >= 2) & (xx <= 15) & (yy >= 8) & (yy <= 19))] = hc
    # body: shoulders and arms
    body = (yy >= 16) & (yy <= 25) & (np.abs(xx - 8.5) <= 4.5 + (yy - 16) * 0.12)
    s.a[body] = top
    shade = DGREY if gown else (PLUM if top in (LAV, PINK) else NAVY)
    s.a[body & (xx >= 11) & (yy >= 18)] = shade if not gown else LGREY
    for ax in (3, 14):
        s.rect(ax, 18, ax, 23, top)
        s.put(ax, 24, PEACH)
    if gown:
        for (x, y) in [(6, 19), (10, 21), (7, 23), (11, 18)]:
            s.put(x, y, BLUE)
    # legs
    s.rect(6, 26, 7, 28, DGREY if not gown else LGREY)
    s.rect(10, 26, 11, 28, DGREY if not gown else LGREY)
    s.rect(5, 29, 7, 29, BROWN if not gown else WHITE)
    s.rect(10, 29, 12, 29, BROWN if not gown else WHITE)
    # neck and head
    s.rect(7, 14, 10, 16, PEACH)
    face = mask_superellipse(W, H, 8.5, 9.0, 5.6, 6.0, n=2.4)
    s.a[face] = PEACH
    # hair
    s.a[_hair_mask(hair) & ~(face & (yy >= 6))] = hc
    if hair == "bob":
        s.rect(5, 5, 12, 5, hc)
    if hair == "short":
        s.put(5, 6, hc); s.put(12, 6, hc)
    # face
    for ex in (6, 11):
        if blink or sick:
            s.put(ex, 10, BLACK); s.put(ex + (1 if ex > 8 else -1), 10, BLACK)
        else:
            s.put(ex, 9, BLACK); s.put(ex, 10, BLACK)
    if not sick:
        s.put(5, 12, PINK); s.put(12, 12, PINK)
    s.put(8, 13, BROWN); s.put(9, 13, BROWN)
    if sick:  # tired eyes and sweat, not grey skin: grey reads as "dead"
        s.put(6, 11, LGREY); s.put(11, 11, LGREY)
        s.put(14, 4, BLUE); s.put(14, 5, BLUE); s.put(13, 5, WHITE)
    outline(s, BLACK)
    if ghost:
        m = s.a >= 0
        s.a[m] = DGREY
        s.a[m & ((xx + yy) % 2 == 0)] = -1
    return s


def kidney(cells=0, glow=False):
    """Kidney, 14x18 (front view, hilum on the right). cells: number of tumor dots
    inside (PLUM, like the tumor body); glow: a highlight."""
    w, h = 14, 18
    s = Spr(w, h)
    m = mask_superellipse(w, h, 7.0, 9.0, 5.6, 8.0, n=2.2)
    yy, xx = np.mgrid[0:h, 0:w]
    m &= ~mask_circle(w, h, 13.8, 9.0, 3.4)   # hilum notch
    paint_body(s, m, 7.0, 9.0, PINK, BROWN if not glow else YELLOW, shade=RED, hi=WHITE if glow else PEACH)
    # vessels from the hilum
    s.put(11, 8, RED); s.put(12, 8, RED); s.put(13, 8, RED)
    s.put(11, 10, BLUE); s.put(12, 10, BLUE); s.put(13, 10, BLUE)
    s.put(11, 12, LGREY); s.put(11, 13, LGREY); s.put(12, 14, LGREY)
    for (x, y) in [(5, 6), (6, 12), (4, 9), (8, 4), (7, 9)][:cells]:
        s.put(x, y, PLUM); s.put(x + 1, y, PLUM); s.put(x, y + 1, PLUM); s.put(x + 1, y + 1, BLACK)
    outline(s, BLACK)
    return s


def ribbon(w=10):
    """Removed or surgery: a small plaster, 7x4."""
    s = Spr(7, 4)
    s.ascii(0, 0, [".WWWWW.", "WWPWPWW", "WWWPWWW", ".WWWWW."], {"W": WHITE, "P": PEACH})
    return s
