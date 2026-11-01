# Camera of an action scene: integer zoom (x1, x2, x3), pan, shake. Pixels stay square and sharp.
#
#   camera:                                        t (s from the scene start) or on: <word>
#     - {t: 1.5, zoom: 2, at: nk}                  cut to x2 on an actor (the camera follows it) or on [x, y]
#     - {t: 3.0, pan_to: tumor, dur: 0.8}          move the center (eased)
#     - {t: 3.4, shake: 0.4, amp: 3}               shake for 0.4 s, amp in frame pixels
#     - {t: 4.5, zoom: 1}                          cut back to the full frame
#
# A zoom is a cut (a new shot); a pan starts a new shot too. pace.py counts them.

import math, random
import numpy as np
from PIL import Image
from .timing import ease, seg, lerp


def state(cams, t, where):
    """Zoom, center (frame px), shake offset at t. where(target, t) -> (x, y) in frame px."""
    z, cx, cy = 1, None, None
    dx = dy = 0
    for c in sorted(cams, key=lambda c: c["_t"]):
        ct = c["_t"]
        if t < ct:
            break
        if "zoom" in c:
            z = int(c["zoom"])
            if z not in (1, 2, 3, 4):
                raise ValueError(f"camera zoom {c['zoom']!r}: use an integer 1 to 4")
            follow = c.get("at")
            if follow is None and z == 1:
                cx = cy = None
            elif follow is not None:
                # an actor name: the camera follows the actor; [x, y]: a fixed point
                cx, cy = where(follow, t if isinstance(follow, str) else ct)
        if "pan_to" in c:
            d = float(c.get("dur", 0.8))
            tx, ty = where(c["pan_to"], min(t, ct + d))
            if cx is None:
                cx, cy = where([0.5, 0.5], t)
            k = ease(seg(t, ct, ct + d))
            cx, cy = lerp(cx, tx, k), lerp(cy, ty, k)
        if "shake" in c:
            d = float(c["shake"])
            if t < ct + d:
                amp = float(c.get("amp", 3)) * (1 - (t - ct) / d)
                r = random.Random(int(t * 30) * 7919 + int(ct * 100))
                dx, dy = round(r.uniform(-amp, amp)), round(r.uniform(-amp, amp))
    return z, cx, cy, dx, dy


def apply(img, z, cx, cy, dx=0, dy=0, fill=(0, 0, 0)):
    """Crops (W/z) x (H/z) around (cx, cy), scales it x z with nearest neighbor; then shakes."""
    W, H = img.size
    if z > 1:
        w, h = W // z, H // z
        cx = W / 2 if cx is None else cx
        cy = H / 2 if cy is None else cy
        x0 = int(round(min(max(cx - w / 2, 0), W - w)))
        y0 = int(round(min(max(cy - h / 2, 0), H - h)))
        img = img.crop((x0, y0, x0 + w, y0 + h)).resize((w * z, h * z), Image.NEAREST)
        if img.size != (W, H):
            out = Image.new("RGB", (W, H), fill)
            out.paste(img, (0, 0))
            img = out
    if dx or dy:
        out = Image.new("RGB", (W, H), fill)
        out.paste(img, (int(dx), int(dy)))
        img = out
    return img


def shots(cams):
    """Times (s from the scene start) when a new shot begins: zoom cuts and pan starts."""
    return sorted(c["_t"] for c in cams if "zoom" in c or "pan_to" in c)
