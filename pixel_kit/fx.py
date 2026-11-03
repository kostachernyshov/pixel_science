# Effects: the canvas with a color layer and a light layer, the primitives, and the hit mechanics.
# Primitives have no topic: no cells, no atoms. Packs give them meaning in verbs (pixel_kit/verbs.py).
#
#   cv = Canvas(img, bg)                 img: the frame with sprites; bg: the frame before sprites
#   PRIMS["jet"](cv, t, g, ramp, o)      draw one primitive at local time t (s)
#   img = cv.image()                     color + light -> PIL image
#
# Contract of a primitive (read before you add one, see skills/add-verb/SKILL.md):
# - fn(cv, t, g, ramp, o). t: seconds from the start of the primitive. Nothing is drawn when t < 0 or t > o["dur"].
# - The frame comes from t and o["seed"] only (no state between frames), so any frame renders alone.
# - g: geometry from the actors: g["a"] (x, y), g["b"] (x, y) or None, g["r"] the actor radius in px.
# - ramp: colors from dark to bright (RGB tuples). Bright = hot, dark = cool.
# - Under 5 ms a frame at 480x270 (pixsci check warns).
# Techniques after pixelfx (MIT, patch-gg) and Sprite Fusion's VFX (MIT, Hugo Duprez): lines and light,
# not fills; a white-hot core; fast attack, slow decay; a flash on contact.

import math
import numpy as np
from PIL import Image
from .timing import clamp, ease

# The light layer. A style sets it: "add" for a dark background (glow adds to the color),
# "tint" for a light background (glow tints the color, white stays visible). k: strength.
LIGHT = {"mode": "tint", "k": 0.55}


class Canvas:
    def __init__(self, img, bg=None):
        self.col = np.array(img.convert("RGB"))
        self.H, self.W = self.col.shape[:2]
        self.bg = np.array(bg.convert("RGB")) if bg is not None else None
        self.light = None
        self.box = None                                # the area with light: x0, y0, x1, y1

    def px(self, xs, ys, rgb):
        """Set pixels; xs, ys are numbers or arrays."""
        xs = np.round(np.atleast_1d(xs)).astype(int)
        ys = np.round(np.atleast_1d(ys)).astype(int)
        m = (xs >= 0) & (ys >= 0) & (xs < self.W) & (ys < self.H)
        self.col[ys[m], xs[m]] = rgb

    def lamp(self, x, y, r, rgb, k=1.0):
        """Add light: a disc of radius r, in 3 steps (pixel art has no smooth gradient)."""
        if k <= 0 or r < 1:
            return
        if self.light is None:
            self.light = np.zeros((self.H, self.W, 3), np.float32)
        x0, x1 = max(0, int(x - r)), min(self.W, int(x + r) + 1)
        y0, y1 = max(0, int(y - r)), min(self.H, int(y + r) + 1)
        if x0 >= x1 or y0 >= y1:
            return
        yy, xx = np.mgrid[y0:y1, x0:x1]
        f = np.ceil(np.clip(1 - np.hypot(xx - x, yy - y) / r, 0, 1) * 3) / 3 * k
        self.light[y0:y1, x0:x1] += f[..., None] * np.asarray(rgb, np.float32)
        b = self.box
        self.box = (x0, y0, x1, y1) if b is None else (min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1))

    def shift(self, dx, dy):
        """Move the whole picture (shake)."""
        if dx or dy:
            self.col = np.roll(self.col, (dy, dx), axis=(0, 1))
            if self.light is not None:
                self.light = np.roll(self.light, (dy, dx), axis=(0, 1))
                self.box = (0, 0, self.W, self.H)

    def image(self):
        """Color + light. Only the area with light is blended (the rest costs nothing)."""
        out = self.col
        if self.box is not None:
            x0, y0, x1, y1 = self.box
            L, c, k = self.light[y0:y1, x0:x1], out[y0:y1, x0:x1], LIGHT["k"]
            if LIGHT["mode"] == "add":
                out[y0:y1, x0:x1] = np.clip(c + L * k, 0, 255).astype(np.uint8)
            else:
                peak = L.max(axis=2, keepdims=True)
                a = np.clip(peak / 255 * k, 0, 0.6)
                hue = L / np.maximum(peak, 1) * 255
                out[y0:y1, x0:x1] = (c * (1 - a) + hue * a).astype(np.uint8)
        return Image.fromarray(out)


def _rng(o, salt=0):
    return np.random.default_rng(int(o.get("seed", 0)) * 7919 + salt)


def _dir(g):
    (ax, ay), b = g["a"], g.get("b")
    if not b:
        return 1.0, 0.0
    dx, dy = b[0] - ax, b[1] - ay
    d = math.hypot(dx, dy) or 1.0
    return dx / d, dy / d


# ---------------------------------------------------------------- primitives

def jet(cv, t, g, ramp, o):
    """A stream from a to b: the head runs out, beads run along it, the tail follows. White core, dark edges."""
    dur = o.get("dur", 0.6)
    if t < 0 or t > dur or not g.get("b"):
        return
    (ax, ay), (bx, by) = g["a"], g["b"]
    L = math.hypot(bx - ax, by - ay)
    head = ease(clamp(t / (0.35 * dur)))
    tail = ease(clamp((t - 0.6 * dur) / (0.4 * dur)))
    if head <= tail:
        return
    ux, uy = _dir(g)
    nx, ny = -uy, ux
    s = np.linspace(tail, head, max(2, int(L * (head - tail))))
    sag = o.get("arc", 4) * np.sin(np.pi * s)
    x, y = ax + (bx - ax) * s + nx * sag, ay + (by - ay) * s + ny * sag
    w = o.get("width", 1)
    for k in range(w, 0, -1):
        c = ramp[max(0, len(ramp) - 2 - k)]
        cv.px(x + nx * k, y + ny * k, c)
        cv.px(x - nx * k, y - ny * k, c)
    cv.px(x, y, ramp[-1])
    rng = _rng(o)
    for i in range(o.get("n", 4)):                     # beads run along the stream
        p = (t * 2.5 + rng.random()) % 1.0
        if tail <= p <= head:
            px, py = ax + (bx - ax) * p + nx * o.get("arc", 4) * math.sin(math.pi * p), ay + (by - ay) * p + ny * o.get("arc", 4) * math.sin(math.pi * p)
            cv.px([px, px + 1, px, px + 1], [py, py, py + 1, py + 1], ramp[-1])
            cv.lamp(px, py, 4, ramp[-1], 0.5)
    for p in np.arange(tail, head, 0.25):
        cv.lamp(ax + (bx - ax) * p, ay + (by - ay) * p, 5, ramp[-2], 0.3)
    hx, hy = x[-1], y[-1]
    cv.lamp(hx, hy, 8, ramp[-1], 0.8 * (1 - tail))


def burst(cv, t, g, ramp, o):
    """Particles fly out of a point: a white flash, fast out, slow drift (drag), bright to dark as they age."""
    dur = o.get("dur", 0.8)
    if t < 0 or t > dur:
        return
    x0, y0 = g["a"]
    rng = _rng(o, 1)
    n = o.get("n", 18)
    base = math.atan2(*_dir(g)[::-1]) if g.get("b") and o.get("spread", 2 * math.pi) < 2 * math.pi else 0.0
    spread = o.get("spread", 2 * math.pi)
    ang = base + (rng.random(n) - 0.5) * spread
    v = o.get("speed", 90) * (0.4 + 0.6 * rng.random(n))
    life = dur * (0.5 + 0.5 * rng.random(n))
    drag, grav = 4.0, o.get("gravity", 0)
    age = t / life
    alive = age < 1
    d = v * (1 - math.exp(-drag * t)) / drag
    x = x0 + np.cos(ang) * d
    y = y0 + np.sin(ang) * d + 0.5 * grav * t * t
    idx = np.clip((1 - age) * len(ramp), 0, len(ramp) - 1).astype(int)
    for i in np.nonzero(alive)[0]:
        c = ramp[idx[i]]
        cv.px(x[i], y[i], c)
        if age[i] < 0.3:                               # fast: a streak behind
            cv.px(x[i] - math.cos(ang[i]) * 1.5, y[i] - math.sin(ang[i]) * 1.5, ramp[max(0, idx[i] - 1)])
        cv.lamp(x[i], y[i], 3, c, 0.5 * (1 - age[i]))
    if t < 0.07:                                       # the hero frame
        yy, xx = np.mgrid[-3:4, -3:4]
        m = xx * xx + yy * yy <= 9
        cv.px(x0 + xx[m], y0 + yy[m], ramp[-1])
    cv.lamp(x0, y0, o.get("size", 18), ramp[-1], math.exp(-t * 8))


def ring(cv, t, g, ramp, o):
    """A wave: a 1 px ring grows and thins out (every other pixel at the end)."""
    dur = o.get("dur", 0.6)
    if t < 0 or t > dur:
        return
    k = t / dur
    for i in range(o.get("rings", 1)):
        kk = k - 0.18 * i
        if kk <= 0:
            continue
        r = g.get("r", 4) * 0.6 + (o.get("size", 40)) * ease(clamp(kk))
        n = max(12, int(r * 6))
        a = np.linspace(0, 2 * np.pi, n, endpoint=False)
        if kk > 0.6:
            a = a[::2]
        c = ramp[int(clamp(1 - kk) * (len(ramp) - 1))]
        x, y = g["a"][0] + np.cos(a) * r, g["a"][1] + np.sin(a) * r * o.get("flat", 1.0)
        cv.px(x, y, c)
        for j in range(0, len(a), max(1, len(a) // 8)):
            cv.lamp(x[j], y[j], 4, c, 0.35 * (1 - kk))


def shell(cv, t, g, ramp, o):
    """A shield around an actor: a rim, a diamond lattice, a sheen that sweeps across.
    o["flash"]: time of a blow (a flash and a ripple). o["break"]: True, it falls apart cell by cell at the end."""
    dur = o.get("dur", 1.5)
    if t < 0 or t > dur:
        return
    cx, cy = g["a"]
    R = g.get("r", 10) * 0.8 + o.get("gap", 2)
    grow = ease(clamp(t / 0.2))
    r = R * (0.6 + 0.4 * grow)
    x0, x1 = int(cx - r - 1), int(cx + r + 2)
    y0, y1 = int(cy - r - 1), int(cy + r + 2)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    d = np.hypot(xx - cx, yy - cy)
    rim = (d <= r) & (d > r - 1.2)
    lat = (d <= r - 1.2) & (((xx + yy) % 6 == 0) | ((xx - yy) % 6 == 0)) & (xx % 2 == 0)
    fl = o.get("flash")
    hot = fl is not None and 0 <= t - fl < 0.1
    rip = fl is not None and 0 <= t - fl < 0.35
    if rip:                                            # a ripple runs over the film from the blow
        bx, by = g["b"] if g.get("b") else (cx - r, cy)
        rr = np.hypot(xx - bx, yy - by)
        lat |= (d <= r) & (np.abs(rr - (t - fl) * 90) < 1)
    sweep = ((t * 40) % (4 * r)) - 2 * r
    sheen = (d <= r - 1.2) & (np.abs((xx - cx) + (yy - cy) - sweep) < 1.2)
    if o.get("break", False):                          # cells blink out at the end
        k = clamp((t - (dur - 0.35)) / 0.35)
        cell = (((xx // 3) * 73856093) ^ ((yy // 3) * 19349663)) % 997 / 997
        keep = cell >= k
        rim &= keep
        lat &= keep
        sheen &= keep
    cv.px(xx[lat], yy[lat], ramp[-1] if hot else ramp[1])
    cv.px(xx[sheen], yy[sheen], ramp[-1] if hot else ramp[-2])
    cv.px(xx[rim], yy[rim], ramp[-1] if hot else ramp[-2])
    cv.lamp(cx, cy, r + 2, ramp[-2], 0.1 * grow)
    if hot:
        cv.lamp(*(g["b"] or (cx, cy)), 14, ramp[-1], 1.0)


def sparks(cv, t, g, ramp, o):
    """Twinkles around a point: small plus signs that flash and fade at random times."""
    dur = o.get("dur", 0.8)
    if t < 0 or t > dur:
        return
    rng = _rng(o, 2)
    n = o.get("n", 6)
    R = o.get("spread", g.get("r", 8))
    a, rr = rng.random(n) * 2 * np.pi, R * np.sqrt(rng.random(n))
    start = rng.random(n) * dur * 0.6
    for i in range(n):
        k = (t - start[i]) / 0.3
        if not 0 <= k <= 1:
            continue
        x, y = g["a"][0] + math.cos(a[i]) * rr[i], g["a"][1] + math.sin(a[i]) * rr[i]
        s = 2 if 0.2 < k < 0.6 else 1
        c = ramp[-1] if k < 0.5 else ramp[-2]
        cv.px([x] + [x - j for j in range(1, s + 1)] + [x + j for j in range(1, s + 1)] + [x] * 2 * s,
              [y] * (2 * s + 1) + [y - j for j in range(1, s + 1)] + [y + j for j in range(1, s + 1)], c)
        cv.lamp(x, y, 4, c, 0.6 * (1 - k))


def dissolve(cv, t, g, ramp, o):
    """The actor's pixels break up from the edge to the center; a hot rim runs ahead of the hole."""
    dur = o.get("dur", 0.9)
    if t < 0:
        return
    k = clamp(t / dur) * 1.1
    cx, cy = g["a"]
    R = g.get("r", 10) + 2
    x0, x1 = max(0, int(cx - R)), min(cv.W, int(cx + R) + 1)
    y0, y1 = max(0, int(cy - R)), min(cv.H, int(cy + R) + 1)
    if x0 >= x1 or y0 >= y1:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1]
    noise = (((xx * 73856093) ^ (yy * 19349663) ^ int(o.get("seed", 0))) % 1009) / 1009
    th = 0.55 * noise + 0.45 * (1 - np.hypot(xx - cx, yy - cy) / R)
    bg = cv.bg[y0:y1, x0:x1] if cv.bg is not None else np.full((y1 - y0, x1 - x0, 3), 251, np.uint8)
    sprite = np.any(cv.col[y0:y1, x0:x1] != bg, axis=2)
    gone = sprite & (th < k)
    edge = sprite & (th >= k) & (th < k + 0.08) & (k < 1.05)
    cv.col[y0:y1, x0:x1][gone] = bg[gone]
    cv.px(xx[edge], yy[edge], ramp[-1])
    if t <= dur:
        cv.lamp(cx, cy, R + 4, ramp[-2], 0.5 * (1 - abs(2 * clamp(t / dur) - 1)))


def trail(cv, t, g, ramp, o):
    """A dotted path from a to b, dots run toward b (a signal, a flow)."""
    dur = o.get("dur", 1.5)
    if t < 0 or t > dur or not g.get("b"):
        return
    (ax, ay), (bx, by) = g["a"], g["b"]
    L = math.hypot(bx - ax, by - ay) or 1
    gap = o.get("gap", 6)
    vis = clamp(t / 0.3) * clamp((dur - t) / 0.3)
    s = np.arange((t * o.get("speed", 30)) % gap, L, gap) / L
    s = s[s <= clamp(t / 0.4)]
    x, y = ax + (bx - ax) * s, ay + (by - ay) * s
    c = ramp[-2] if vis > 0.5 else ramp[1]
    cv.px(x, y, c)
    for i in range(0, len(s), 2):
        cv.lamp(x[i], y[i], 3, ramp[-1], 0.4 * vis)


def glow(cv, t, g, ramp, o):
    """Light only: a soft pulse around a point (attention, an active state)."""
    dur = o.get("dur", 1.0)
    if t < 0 or t > dur:
        return
    k = math.sin(math.pi * t / dur)
    cv.lamp(g["a"][0], g["a"][1], g.get("r", 8) * o.get("size", 1.6), ramp[-1], k)


_GLYPHS = {"!": ["X", "X", "X", "X", ".", "X"], "?": ["XX.", "..X", ".X.", ".X.", "...", ".X."],
           "z": ["XXX", "..X", ".X.", "X..", "XXX"]}


def sign(cv, t, g, ramp, o):
    """A sign above an actor: "!" (it notices), "?" (it searches), "z" (it is blocked). It bobs."""
    dur = o.get("dur", 1.2)
    if t < 0 or t > dur:
        return
    rows = _GLYPHS[o.get("text", "!")]
    sc = 2
    x0 = int(g["a"][0] - len(rows[0]) * sc / 2)
    y0 = int(g["a"][1] - g.get("r", 10) * 0.8 - len(rows) * sc - 2 - (1 if int(t * 8) % 2 else 0))
    pts = [(x0 + i * sc + u, y0 + j * sc + v) for j, row in enumerate(rows) for i, ch in enumerate(row)
           if ch == "X" for u in range(sc) for v in range(sc)]
    xs, ys = np.array(pts).T
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):  # a dark outline, then the sign
        cv.px(xs + dx, ys + dy, ramp[0])
    cv.px(xs, ys, ramp[-1])


PRIMS = {f.__name__: f for f in (jet, burst, ring, shell, sparks, dissolve, trail, glow, sign)}


# ---------------------------------------------------------------- hit mechanics

# windup: the attacker pulls back before contact (s); freeze: the picture stops on contact (s);
# shake: px; push: px the target moves back.
HIT = {
    "soft": {"windup": 0.15, "freeze": 0.06, "shake": 1, "push": 2},
    "normal": {"windup": 0.25, "freeze": 0.10, "shake": 2, "push": 4},
    "heavy": {"windup": 0.35, "freeze": 0.16, "shake": 3, "push": 7},
}


def hit_params(h):
    """A preset name or a dict (fields override the "normal" preset)."""
    if h in (None, False):
        return None
    if isinstance(h, str):
        return dict(HIT[h])
    base = dict(HIT[h.get("preset", "normal")])
    base.update({k: v for k, v in h.items() if k != "preset"})
    return base


def warp(t, hits):
    """Scene time with the freezes: the picture holds for "freeze" s at each contact.
    hits: [(contact time, params)]. Returns (time, shake px; 0 when not frozen)."""
    acc = 0.0                                          # freezes before t
    for th, p in sorted(hits, key=lambda h: h[0]):
        real = th + acc
        if t < real:
            break
        if t < real + p["freeze"]:
            return th, p["shake"]
        acc += p["freeze"]
    return t - acc, 0


def offset(t, th, p, role):
    """How far (px, along the attack direction) the attacker or the target moves around a contact."""
    if role == "attacker":
        w = p["windup"]
        if th - w <= t < th:                           # pull back, then snap forward
            k = (t - (th - w)) / w
            return -3 * ease(clamp(k / 0.8)) if k < 0.8 else -3 + 6 * (k - 0.8) / 0.2
        if t >= th:
            return 3 * math.exp(-(t - th) * 8)
        return 0
    if t < th:                                         # the target is pushed back and springs to rest
        return 0
    d = t - th
    return p["push"] * (math.exp(-d * 4) * (1 + 0.3 * math.sin(d * 25)))
