# Procedural parts of an action scene: swarm, grow, field. Each has a seed: the same seed gives
# the same video. Every position is a closed formula of t, so any frame draws on its own.
#
# Positions are fractions of the stage (0..1). "target" is an actor name or [x, y].
#
#   swarm: N sprites that move by a rule
#     {sprite, n, area: [x0, y0, x1, y1], rule: wander | seek | orbit | flow | flee,
#      target, t, dur, stagger, radius, speed, scale, anim, arrive_anim, arrive_sprite, flip}
#   grow: cells that divide (N doubles every "doubling" s, up to max), color by generation
#     {sprite | sprites: [gen0, gen1, ...], at, n0, max, doubling, t, spread, scale}
#   field: a field or a flow of small things
#     {kind: dots, spacing, color, drag: target, radius, t, wave}   lattice; dots crowd around the target
#     {kind: flow, n, dir: [dx, dy], speed, color, sprite, area}      a stream that wraps around
#     {kind: gradient, at: target, radius, color, t, dur}              dithered rings that spread
#
# t: start (s from the scene start); a plan can give "on: <word>" instead (explain.py resolves it).

import math, random, zlib
from PIL import ImageDraw
from .palette import C, NAMES
from .timing import clamp, seg, ease, lerp
from .fx import bayer
from . import sprites as S


def color(c):
    if isinstance(c, str):
        return NAMES.index(c.upper())
    return int(c)


def _rnd(seed, *k):
    return random.Random(zlib.crc32(repr((int(seed),) + tuple(k)).encode()))


# ---------------------------------------------------------------- swarm

def swarm_state(g, t, target_xy, seed):
    """[(x, y, sprite, anim, anim_t, flip)] in stage fractions, for each member."""
    n = int(g.get("n", 8))
    x0, y0, x1, y1 = g.get("area", [0.1, 0.15, 0.9, 0.85])
    rule = g.get("rule", "wander")
    t0 = float(g.get("_t", 0.0))
    dur = float(g.get("dur", 1.2))
    stagger = float(g.get("stagger", 0.08))
    radius = float(g.get("radius", 0.12))
    speed = float(g.get("speed", 0.15))
    out = []
    for k in range(n):
        r = _rnd(seed, "swarm", k)
        hx, hy = r.uniform(x0, x1), r.uniform(y0, y1)
        ph1, ph2 = r.uniform(0, 6.283), r.uniform(0, 6.283)
        w1, w2 = r.uniform(1.2, 2.4), r.uniform(1.0, 2.0)
        amp = float(g.get("wobble", 0.015))
        wx, wy = amp * math.sin(w1 * t + ph1), amp * math.cos(w2 * t + ph2)
        sprite, anim, at0, flip = g["sprite"], g.get("anim", "idle"), 0.0, bool(g.get("flip", False))
        if rule == "wander":
            x, y = hx + wx * 2, hy + wy * 2
        elif rule == "flow":
            dx, dy = g.get("dir", [1, 0])
            span_x, span_y = (x1 - x0) or 1, (y1 - y0) or 1
            x = x0 + ((hx - x0) + dx * speed * t) % span_x
            y = y0 + ((hy - y0) + dy * speed * t) % span_y + wy
        else:
            tx, ty = target_xy(t)
            a = 2 * math.pi * k / n + r.uniform(-0.25, 0.25)
            ox, oy = math.cos(a) * radius, math.sin(a) * radius * 1.6
            tk = t0 + stagger * k
            if rule == "seek":
                kk = ease(seg(t, tk, tk + dur))
                x, y = lerp(hx, tx + ox, kk) + wx * (1 - kk), lerp(hy, ty + oy, kk) + wy * (1 - kk)
                if t >= tk + dur:
                    if g.get("arrive_sprite"):
                        sprite = g["arrive_sprite"]
                    if g.get("arrive_anim"):
                        anim, at0 = g["arrive_anim"], tk + dur
                flip = (tx + ox) < hx
            elif rule == "flee":
                kk = ease(seg(t, tk, tk + dur))
                vx, vy = hx - tx, hy - ty
                # away from the target, out to the edge of the area
                L = math.hypot(vx, vy) or 1
                x = hx + vx / L * 0.5 * kk + wx
                y = hy + vy / L * 0.5 * kk + wy
                flip = vx < 0
            elif rule == "orbit":
                ang = a + speed * 6.283 * max(0.0, t - t0)
                x, y = tx + math.cos(ang) * radius, ty + math.sin(ang) * radius * 1.6
            else:
                raise ValueError(f"swarm rule {rule!r}: use wander, seek, orbit, flow, flee")
        out.append((x, y, sprite, anim, t - at0, flip))
    return out


# ---------------------------------------------------------------- grow

GOLDEN = math.pi * (3 - math.sqrt(5))


def grow_state(g, t):
    """[(x, y, sprite, anim, anim_t)] of the cells that exist at t (stage fractions)."""
    t0 = float(g.get("_t", 0.0))
    n0 = int(g.get("n0", 1))
    mx = int(g.get("max", 16))
    dbl = float(g.get("doubling", 0.8))
    cx, cy = g.get("_at", (0.5, 0.5))
    spread = float(g.get("spread", 0.05))
    sprites = g.get("sprites") or [g["sprite"]]
    n = n0 if t < t0 else min(mx, int(n0 * 2 ** ((t - t0) / dbl)))
    out = []
    for i in range(n):
        r = spread * math.sqrt(i)
        a = i * GOLDEN
        gen = int(math.log2(i / n0 + 1)) if i >= n0 else 0
        born = t0 + dbl * math.log2((i + 1) / n0) if i >= n0 else -9
        sp = sprites[min(gen, len(sprites) - 1)]
        out.append((cx + math.cos(a) * r, cy + math.sin(a) * r * 1.6, sp, "idle", t - born))
    return out


def grow_end(g):
    """Time when the cells stop dividing (for the pace check)."""
    n0, mx, dbl = int(g.get("n0", 1)), int(g.get("max", 16)), float(g.get("doubling", 0.8))
    return float(g.get("_t", 0.0)) + dbl * math.log2(max(1, mx / n0))


# ---------------------------------------------------------------- field

def draw_field(img, g, t, stage, target_px, seed):
    x0, y0, x1, y1 = stage
    kind = g.get("kind", "dots")
    col = C(color(g.get("color", "LGREY")))
    d = ImageDraw.Draw(img)
    t0 = float(g.get("_t", 0.0))
    if t < t0 and not g.get("always", True):
        return
    if kind == "dots":
        step = int(g.get("spacing", 12))
        rad = float(g.get("radius", 0.18)) * (x1 - x0)
        tx, ty = target_px(t) if g.get("drag") else (None, None)
        pull = float(g.get("pull", 0.6))
        size = int(g.get("size", 1))
        for j, y in enumerate(range(y0 + step // 2, y1, step)):
            for i, x in enumerate(range(x0 + step // 2 + (step // 2 if j % 2 else 0), x1, step)):
                px, py = float(x), float(y)
                if g.get("wave"):
                    px += 1.5 * math.sin(0.15 * y + 4 * t)
                if tx is not None and t >= t0:
                    dx, dy = tx - px, ty - py
                    dist = math.hypot(dx, dy)
                    if dist < rad:
                        k = (1 - dist / rad) * pull * clamp((t - t0) / 0.4)
                        px, py = px + dx * k, py + dy * k
                d.rectangle([int(px), int(py), int(px) + size - 1, int(py) + size - 1], fill=col)
    elif kind == "flow":
        n = int(g.get("n", 30))
        dx, dy = g.get("dir", [1, 0])
        sp = float(g.get("speed", 0.2))
        ax0, ay0, ax1, ay1 = g.get("area", [0, 0, 1, 1])
        for k in range(n):
            r = _rnd(seed, "flow", k)
            fx, fy = r.uniform(ax0, ax1), r.uniform(ay0, ay1)
            v = sp * r.uniform(0.7, 1.3)
            fx = ax0 + (fx - ax0 + dx * v * t) % ((ax1 - ax0) or 1)
            fy = ay0 + (fy - ay0 + dy * v * t) % ((ay1 - ay0) or 1)
            px, py = x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)
            if g.get("sprite"):
                S.draw(img, g["sprite"], "idle", t + k * 0.1, px, py, scale=int(g.get("scale", 1)))
            else:
                d.rectangle([int(px), int(py), int(px) + 1, int(py)], fill=col)
    elif kind == "gradient":
        if t < t0:
            return
        tx, ty = target_px(t)
        R = float(g.get("radius", 0.4)) * (x1 - x0) * ease(seg(t, t0, t0 + float(g.get("dur", 1.5))))
        if R < 2:
            return
        bm = bayer(img.height, img.width)
        px = img.load()
        for yy in range(max(0, int(ty - R)), min(img.height, int(ty + R) + 1)):
            for xx in range(max(0, int(tx - R)), min(img.width, int(tx + R) + 1)):
                dist = math.hypot(xx - tx, yy - ty)
                if dist < R and bm[yy, xx] < 8 * (1 - dist / R) ** 1.5:
                    px[xx, yy] = col
    else:
        raise ValueError(f"field kind {kind!r}: use dots, flow, gradient")
