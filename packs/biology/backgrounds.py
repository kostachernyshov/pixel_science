# Backgrounds of the biology pack. Drawn in base (paper) colors; the active style filters them.
# Each function gets t (s from the scene start) and reads frame.W, frame.H.
# Light and quiet: the texture differs from the fill by no more than about 1.15:1.

import math, random
from PIL import Image, ImageDraw
from pixel_kit.palette import *
from pixel_kit import frame
from pixel_kit.bg import paper, cached as _cached


def dishes(t=0, centers=None, cy=None, r=None, w=None, h=None):
    """Two Petri dishes on PAPER (cell culture), side by side (stacked in a tall frame)."""
    w, h = w or frame.W, h or frame.H
    tall = h > w
    r = r or int(min(w / (2 if not tall else 1), h / (1 if not tall else 2)) * 0.38)
    if centers is None:
        centers = [(w // 4, h // 2), (3 * w // 4, h // 2)] if not tall else [(w // 2, h // 4), (w // 2, 3 * h // 4)]
    def make():
        img = paper(w, h)
        d = ImageDraw.Draw(img)
        for cx, cy in centers:
            d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=C(DGREY))
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=C(LGREY))
            d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=(246, 236, 228))
            rnd = random.Random(cx)
            for _ in range(70):
                a, rr = rnd.uniform(0, 6.283), r * math.sqrt(rnd.random()) * 0.92
                d.point([int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a))], fill=(228, 218, 212))
            d.arc([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], 200, 240, fill=C(WHITE))
        return img
    return _cached(("dishes", tuple(centers), r, w, h), make)


def tissue(t=0, w=None, h=None):
    """Connective tissue: rows of soft bricks."""
    w, h = w or frame.W, h or frame.H
    def make():
        im = Image.new("RGB", (w, h), (250, 236, 228))
        d = ImageDraw.Draw(im)
        for row, y in enumerate(range(-6, h, 14)):
            off = 0 if row % 2 == 0 else 13
            for x in range(-26 + off, w, 26):
                d.rounded_rectangle([x + 1, y + 1, x + 24, y + 12], radius=3, outline=(236, 214, 206))
                d.point([x + 12, y + 6], fill=(230, 204, 196))
        return im
    return _cached(("tissue", w, h), make)


def epithelium(t=0, w=None, h=None, base_y=None):
    """Epithelium: a row of tall cells on the basement membrane, lumen above."""
    w, h = w or frame.W, h or frame.H
    base_y = base_y or int(h * 0.72)
    def make():
        im = Image.new("RGB", (w, h), C(PAPER))
        d = ImageDraw.Draw(im)
        d.rectangle([0, base_y - 52, w, base_y], fill=(252, 232, 222))
        for x in range(-4, w, 14):
            d.rounded_rectangle([x + 1, base_y - 50, x + 12, base_y - 2], radius=3, outline=(236, 208, 198))
            d.point([x + 6, base_y - 14], fill=(228, 198, 188))
        d.rectangle([0, base_y, w, base_y + 2], fill=(226, 200, 190))
        for row, y in enumerate(range(base_y + 8, h, 12)):
            for x in range(-20 + (row % 2) * 10, w, 22):
                d.line([x, y, x + 12, y + 2], fill=(240, 226, 220))
        return im
    return _cached(("epithelium", w, h, base_y), make)


def bloodstream(t=0, w=None, h=None, speed=40):
    """Blood vessel: walls at the top and bottom, pale red cells flow to the right."""
    w, h = w or frame.W, h or frame.H
    base = _cached(("blood_base", w, h), lambda: _blood_base(w, h))
    d = ImageDraw.Draw(base)
    rnd = random.Random(11)
    for _ in range(26):
        x0, y0 = rnd.uniform(0, w + 40), rnd.uniform(40, h - 40)
        sp = speed * rnd.uniform(0.7, 1.3)
        x = (x0 + sp * t) % (w + 40) - 20
        d.ellipse([x - 6, y0 - 3, x + 6, y0 + 3], fill=(246, 214, 214))
        d.ellipse([x - 2, y0 - 1, x + 2, y0 + 1], fill=(238, 200, 202))
    return base


def _blood_base(w, h):
    im = Image.new("RGB", (w, h), (254, 240, 236))
    d = ImageDraw.Draw(im)
    for y0, y1 in ((0, 28), (h - 28, h)):
        d.rectangle([0, y0, w, y1], fill=(246, 222, 220))
        for x in range(-10, w, 30):
            yy = y1 - 6 if y0 == 0 else y0 + 4
            d.ellipse([x, yy - 3, x + 22, yy + 3], outline=(234, 204, 204))
    return im


def lymph_node(t=0, w=None, h=None):
    """Lymph node: follicles (dense groups of small lymphocytes) and sinuses between them."""
    w, h = w or frame.W, h or frame.H
    def make():
        im = Image.new("RGB", (w, h), (246, 242, 248))
        d = ImageDraw.Draw(im)
        rnd = random.Random(5)
        for (cx, cy, r) in ((90, 80, 56), (250, 60, 48), (400, 110, 60), (170, 200, 58), (350, 230, 50)):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(236, 232, 244), outline=(222, 216, 236))
            for _ in range(r * 3):
                a, rr = rnd.uniform(0, 6.283), r * math.sqrt(rnd.random()) * 0.94
                x, y = int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a))
                d.rectangle([x, y, x + 1, y + 1], fill=(224, 218, 238))
        return im
    return _cached(("lymph", w, h), make)


def tme(t=0, w=None, h=None):
    """Tumor microenvironment: matrix fibers, a vessel, debris."""
    w, h = w or frame.W, h or frame.H
    def make():
        im = Image.new("RGB", (w, h), (250, 240, 240))
        d = ImageDraw.Draw(im)
        rnd = random.Random(9)
        for _ in range(22):
            x, y = rnd.uniform(-40, w), rnd.uniform(0, h)
            a = rnd.uniform(-0.5, 0.5)
            pts = [(x + k * 12 * math.cos(a), y + k * 12 * math.sin(a) + 3 * math.sin(k)) for k in range(8)]
            d.line(pts, fill=(236, 220, 222))
        d.line([(0, h * 0.8), (w * 0.4, h * 0.65), (w, h * 0.9)], fill=(244, 214, 216), width=12)
        d.line([(0, h * 0.8), (w * 0.4, h * 0.65), (w, h * 0.9)], fill=(250, 228, 228), width=6)
        for _ in range(80):
            d.point([rnd.randrange(w), rnd.randrange(h)], fill=(230, 214, 216))
        return im
    return _cached(("tme", w, h), make)


BACKGROUNDS = {"dishes": dishes, "tissue": tissue, "epithelium": epithelium, "bloodstream": bloodstream,
               "lymph_node": lymph_node, "tme": tme}
ANIMATED = {"bloodstream"}
TAGS = {"dishes": ["lab", "culture", "petri"], "tissue": ["tissue", "connective"],
        "epithelium": ["epithelium", "skin", "gut", "lining"], "bloodstream": ["blood", "vessel", "flow"],
        "lymph_node": ["lymph", "node", "immune"], "tme": ["tumor", "microenvironment", "cancer"]}
