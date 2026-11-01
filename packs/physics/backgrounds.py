# Backgrounds of the physics pack, in base (paper) colors; the active style filters them.

import math
from PIL import Image, ImageDraw
from pixel_kit.palette import *
from pixel_kit import frame
from pixel_kit.bg import cached


def vacuum(t=0, w=None, h=None):
    """Empty space: PAPER with a sparse lattice of faint dots."""
    w, h = w or frame.W, h or frame.H

    def make():
        im = Image.new("RGB", (w, h), B(PAPER))
        d = ImageDraw.Draw(im)
        for y in range(6, h, 12):
            for x in range(6 + (6 if (y // 12) % 2 else 0), w, 12):
                d.point([x, y], fill=(232, 230, 236))
        return im
    return cached(("vacuum", w, h), make)


def beamline(t=0, w=None, h=None):
    """A beam pipe across the frame (down the middle in a tall frame), with magnets."""
    w, h = w or frame.W, h or frame.H

    def make():
        im = vacuum(0, w, h)
        d = ImageDraw.Draw(im)
        if w >= h:
            y = h // 2
            d.rectangle([0, y - 9, w, y + 9], fill=(238, 236, 242))
            d.rectangle([0, y - 9, w, y - 8], fill=(214, 212, 224))
            d.rectangle([0, y + 8, w, y + 9], fill=(214, 212, 224))
            for x in range(10, w, 60):
                d.rectangle([x, y - 13, x + 18, y + 13], outline=(214, 212, 224))
        else:
            x = w // 2
            d.rectangle([x - 9, 0, x + 9, h], fill=(238, 236, 242))
            d.rectangle([x - 9, 0, x - 8, h], fill=(214, 212, 224))
            d.rectangle([x + 8, 0, x + 9, h], fill=(214, 212, 224))
            for y in range(10, h, 60):
                d.rectangle([x - 13, y, x + 13, y + 18], outline=(214, 212, 224))
        return im
    return cached(("beamline", w, h), make)


def detector_hall(t=0, w=None, h=None):
    """Faint rings of a large detector around the frame center."""
    w, h = w or frame.W, h or frame.H

    def make():
        im = vacuum(0, w, h)
        d = ImageDraw.Draw(im)
        cx, cy = w // 2, h // 2
        for r in range(30, int(math.hypot(w, h) / 2), 22):
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(228, 226, 236))
        return im
    return cached(("detector_hall", w, h), make)


BACKGROUNDS = {"vacuum": vacuum, "beamline": beamline, "detector_hall": detector_hall}
TAGS = {"vacuum": ["space", "empty", "field"], "beamline": ["collider", "beam", "accelerator", "lhc"],
        "detector_hall": ["detector", "rings", "collision"]}
