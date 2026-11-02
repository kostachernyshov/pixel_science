# The contact scene: two bodies face to face, their parts on stalks out of each surface, drawn from the
# plan's mechanism model (mechanism.py). A bind closes a part's socket over its partner's key; an agent
# flies in and takes a part's place; a kill ends the right body. The scene starts in the state the last
# scene left (persistence), so nothing has to be set up twice.
#
#   - id: S04
#     type: contact
#     left: t                       # things of the model
#     right: tumor
#     show: [brake, signal]         # bind links as rows, top to bottom (default: every bind between them)
#     beats:
#       - {on: binds, do: brake}
#       - {on: lets, undo: brake}
#       - {on: sticks, do: block}
#       - {on: dies, do: kill}
#       - {on: stops, cell: left, anim: blocked}
#       - {on: stops, cell: left, fx: zzz}
#     camera:
#       - {on: binds, zoom: 2, at: gap}      # at: left, right, gap, or [x, y]

from PIL import ImageDraw
from .palette import *
from .font import text, LINE
from .timing import clamp, ease, lerp
from . import sprites as S, fx, mechanism as M

BIND_S = 0.4      # a stalk reaches its partner in 0.4 s
DOCK_S = 0.9      # an agent flies in and takes its place in 0.9 s


def _color(meta, default=LGREY):
    c = meta.get("color", default)
    return NAMES.index(c) if isinstance(c, str) else int(c)


def _label_col(c):
    """Label text in the part's color when it reads on paper, else ink."""
    return INK if c in (YELLOW, LGREY, WHITE, PEACH, PINK, LAV) else c


# ---------------------------------------------------------------- state over time

def state(plan, sc, t, start):
    """At time t: progress 0..1 of each link, agent docks, cell animations, deaths."""
    _, links = M.model(plan)
    prog = {ln: (-9.0, None) for ln in start["on"]}          # link: (t on, t off)
    anim = {"left": ("idle", 0.0), "right": ("idle", 0.0)}
    dead = {}
    for b in sorted(sc.get("beats") or [], key=lambda b: b["_t"]):
        bt = b["_t"]
        if bt > t:
            break
        if "do" in b and b["do"] in links:
            l = links[b["do"]]
            prog[b["do"]] = (bt, None)
            if l["kind"] == "occupy":
                for n2, l2 in links.items():
                    if l2.get("kind") == "bind" and l["b"] in (l2["a"], l2["b"]) and n2 in prog and prog[n2][1] is None:
                        prog[n2] = (prog[n2][0], bt + DOCK_S * 0.6)   # pushed off as the agent arrives
            if l["kind"] == "kill":
                side = "right" if sc.get("right") == l["b"] else "left"
                anim[side] = ("death", bt)
                dead[side] = bt
        if "undo" in b and b["undo"] in prog:
            prog[b["undo"]] = (prog[b["undo"]][0], bt)
        if b.get("cell") in anim and b.get("anim"):
            anim[b["cell"]] = (b["anim"], bt)
            if b["anim"] == "death":
                dead[b["cell"]] = bt
    p = {}
    for ln, (t0, t1) in prog.items():
        dur = DOCK_S if links.get(ln, {}).get("kind") == "occupy" else BIND_S
        v = ease(clamp((t - t0) / dur, 0, 1))
        if t1 is not None and t >= t1:
            v = 1 - ease(clamp((t - t1) / BIND_S, 0, 1))
        p[ln] = (v, t0)
    return {"p": p, "anim": anim, "dead": {s: t0 for s, t0 in dead.items() if t - t0 > 0.25}}


# ---------------------------------------------------------------- geometry

def _edge(name, k, row_y, side):
    """x of the surface (from the sprite center) on a row, at scale k: the last opaque pixel toward the gap."""
    im = S.frame(name, "idle", 0, False, k)
    ax, ay = S.info(name)["anchor"]
    y = max(0, min(im.height - 1, int(round(ay * k + row_y))))
    a = im.getchannel("A")
    xs = [x for x in range(im.width) if a.getpixel((x, y)) > 0]
    if not xs:
        return None
    return (max(xs) + 1 - ax * k) if side == "left" else (min(xs) - ax * k)


def _body(name):
    box = S.frame(name, "idle", 0).getchannel("A").getbbox()
    return (box[2] - box[0], box[3] - box[1]) if box else tuple(S.cell(name))


def _gap(k):
    """Surface to surface: room for two stalks, two heads, and their labels."""
    return max(18 * min(3, max(2, k - 1)), 64)


def scale_for(plan, sc, L):
    """The largest integer scale (2..7) at which both bodies, the gap, and the labels fit the stage."""
    if sc.get("scale"):
        return int(sc["scale"])
    things, _ = M.model(plan)
    x0, y0, x1, y1 = L["stage"]
    lw, rw = _body(things[sc["left"]]["sprite"]), _body(things[sc["right"]]["sprite"])
    for k in range(7, 1, -1):
        if (lw[0] + rw[0]) * k + _gap(k) <= (x1 - x0) * 0.86 and max(lw[1], rw[1]) * k + 2 * LINE + 8 <= (y1 - y0):
            return k
    return 2


def geometry(plan, sc, L):
    """(scale, part pixel size, left x, right x, y): the surfaces, not the sprite boxes, stand one gap apart."""
    things, _ = M.model(plan)
    x0, y0, x1, y1 = L["stage"]
    k = scale_for(plan, sc, L) if not L["banner"] else 2
    mk = min(3, max(2, k - 1)) if not L["banner"] else 2
    gap = _gap(k) if not L["banner"] else 40
    ls, rs = things[sc["left"]]["sprite"], things[sc["right"]]["sprite"]
    el = _edge(ls, k, 0, "left") or S.cell(ls)[0] * k // 2
    er = _edge(rs, k, 0, "right") or -S.cell(rs)[0] * k // 2
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2 + (0 if L["banner"] else 4)
    return k, mk, cx - gap // 2 - el, cx + gap // 2 - er, cy


def where(plan, sc, L, name):
    """Pixel center of "left", "right" or "gap", for the camera."""
    k, mk, lx, rx, cy = geometry(plan, sc, L)
    return {"left": (lx, cy), "right": (rx, cy)}.get(name, ((lx + rx) // 2, cy))


# ---------------------------------------------------------------- drawing

def head(img, cells, x, y, mk, col, toward=1):
    """Head cells (col, row) from a base at x, growing toward +x (toward=1) or -x, centered on row y."""
    d = ImageDraw.Draw(img)
    y0 = y - M.ROWS * mk // 2

    def box(c, r, pad):
        xa = x + c * mk if toward > 0 else x - (c + 1) * mk
        return [xa - pad, y0 + r * mk - pad, xa + mk - 1 + pad, y0 + (r + 1) * mk - 1 + pad]
    for c, r in cells:
        d.rectangle(box(c, r, 1), fill=C(BLACK))
    for c, r in cells:
        d.rectangle(box(c, r, 0), fill=C(col))


def stalk(img, x0, x1, y, mk):
    if x1 < x0:
        x0, x1 = x1, x0
    th = max(1, mk // 2)
    ImageDraw.Draw(img).rectangle([x0, y - th, x1, y + th - (1 if th > 1 else 0)], fill=C(BLACK))


def _width(cells):
    return max(c for c, _ in cells) + 1


def draw(img, plan, sc, t, L, start, labels=True):
    things, links = M.model(plan)
    P = M.parts(plan)
    st = state(plan, sc, t, start)
    x0, y0, x1, y1 = L["stage"]
    k, mk, lx, rx, cy = geometry(plan, sc, L)
    left, right = things[sc["left"]], things[sc["right"]]
    sides = {sc["left"]: "left", sc["right"]: "right"}
    # bodies
    for side, th, x in (("left", left, lx), ("right", right, rx)):
        anim, a0 = st["anim"][side]
        name = th["sprite"]
        if anim not in S.anims(name):
            anim = "idle"
        if anim == "idle":
            S.idle(img, name, t, x, cy, seed=1 if side == "right" else 0, scale=k)
        else:
            a = S.anims(name)[anim]
            done = a["frames"] == 1 or a["fps"] < 3 or (not a["loop"] and t - a0 >= S.duration(name, anim))
            # a finished or slow animation still breathes: a 1 px bob (a dead body lies still)
            bob = (int(t * 3 + (side == "right")) % 2) * k if done and anim != "death" else 0
            S.draw(img, name, anim, t - a0, x, cy - bob, scale=k)
    # rows: one bind link each, spread over the middle of the bodies
    rows = M.rows_of(plan, sc)
    n = len(rows)
    body_h = min(_body(left["sprite"])[1], _body(right["sprite"])[1]) * k
    spread = body_h * (0.56 if n > 1 else 0)
    rows_y = [cy + int(spread * ((i / (n - 1)) - 0.5)) if n > 1 else cy for i in range(n)]
    seat = {}                                   # part -> (x of its head base when bound, y, toward)
    for i, ln in enumerate(rows):
        l = links[ln]
        y = rows_y[i]
        lp, rp = (l["a"], l["b"]) if sides.get(P[l["a"]][0]) == "left" else (l["b"], l["a"])
        el = _edge(left["sprite"], k, y - cy, "left")
        er = _edge(right["sprite"], k, y - cy, "right")
        exl = lx + (el if el is not None else 0) - k
        exr = rx + (er if er is not None else 0) + k
        mid = (exl + exr) // 2
        lc, rc = M.shape(plan, lp), M.shape(plan, rp)
        a_is_left = lp == l["a"]
        wa = 4                                   # the socket block is 4 wide; the key reaches into it
        # bound: the faces meet at mid; the key's tip goes into the socket
        face = mid
        meet_l = face - (wa if a_is_left else 2) * mk
        meet_r = face + (2 if a_is_left else wa) * mk
        rest_l = exl + max(mk * 2, (face - exl) // 3)
        rest_r = exr - max(mk * 2, (exr - face) // 3)
        v, t0 = st["p"].get(ln, (0.0, -9))
        hl = int(lerp(rest_l, meet_l, v))
        hr = int(lerp(rest_r, meet_r, v))
        ld, rd = "left" in st["dead"], "right" in st["dead"]
        if not ld:
            stalk(img, exl, hl, y, mk)
            head(img, lc, hl, y, mk, _color(P[lp][1]), toward=1)
        if not rd:
            stalk(img, hr, exr, y, mk)
            head(img, rc, hr, y, mk, _color(P[rp][1]), toward=-1)
        seat[lp] = (rest_l, y, 1, "left")       # base of the free head, and the way it grows
        seat[rp] = (rest_r, y, -1, "right")
        if v >= 1.0 and not (ld or rd) and not L["banner"] and 0 <= t - t0 - BIND_S < 0.6:
            fx.sparkle(img, face, y - 3 * mk, t - t0 - BIND_S, col=ORANGE)
        if labels and not L["banner"] and (i == 0 or i == n - 1):
            ly = y - 4 * mk - LINE - 2 if i == 0 else y + 4 * mk + 3
            if not ld:
                c = _color(P[lp][1])
                text(img, mid - 3, ly, P[lp][1].get("label", lp), _label_col(c), align="r")
            if not rd:
                c = _color(P[rp][1])
                text(img, mid + 4, ly, P[rp][1].get("label", rp), _label_col(c), align="l")
    # agents: fly in from above and take the part's place
    for ln, (v, t0) in st["p"].items():
        l = links.get(ln, {})
        if l.get("kind") != "occupy" or l["b"] not in seat:
            continue
        base, y, toward, side = seat[l["b"]]
        if side in st["dead"]:
            continue
        ac = M.shape(plan, l["a"])
        col = _color(things[l["a"]], BLUE)
        # bound, a socket and a key span 6 cells base to base, so the agent's base stands 6 cells out
        # and its head grows back toward the part; a stem behind it shows it is a free molecule
        ax = base + toward * 6 * mk
        sx, sy = ax + toward * 24 * mk, y0 + 8
        px, py = int(lerp(sx, ax, v)), int(lerp(sy, y, v))
        stem = 4 * mk
        stalk(img, px, px + toward * stem, py, mk)
        head(img, ac, px, py, mk, col, toward=-toward)
        if v >= 1 and not L["banner"] and 0 <= t - t0 - DOCK_S < 0.6:
            fx.sparkle(img, px, py - 3 * mk, t - t0 - DOCK_S, col=ORANGE)
        if labels and not L["banner"]:
            ly = py - 4 * mk - 2 * LINE - 4 if rows_y and py <= rows_y[0] else py + 4 * mk + LINE + 6
            text(img, px + toward * stem, ly, things[l["a"]].get("label", l["a"]), _label_col(col), align="c")
    # effects on a body
    for b in sc.get("beats") or []:
        bt = b["_t"]
        if not b.get("fx") or t < bt or b.get("cell") not in ("left", "right"):
            continue
        if b.get("dur") is not None and t > bt + float(b["dur"]):
            continue
        px, py = (lx if b["cell"] == "left" else rx), cy
        name = (left if b["cell"] == "left" else right)["sprite"]
        if b["fx"] == "hit":
            fx.hit_flash(img, px, py, t - bt)
        elif b["fx"] == "alert" and t - bt < 1.2:
            fx.alert(img, px, py - S.body_top(name) * k - 10, t - bt)
        elif b["fx"] == "sparkle" and t - bt < 1.0:
            fx.sparkle(img, px, py - 20, t - bt)
        elif b["fx"] == "particles":
            fx.particles(img, px, py, t - bt, seed=int(bt * 10))
        elif b["fx"] == "zzz":
            fx.zzz(img, px, py - S.body_top(name) * k + 10, t - bt)
    for ln, (v, t0) in st["p"].items():                # a kill breaks the body up
        if links.get(ln, {}).get("kind") == "kill" and t0 >= 0:
            side = sides.get(links[ln]["b"])
            fx.particles(img, lx if side == "left" else rx, cy, t - t0, seed=int(t0 * 10))
    # body labels
    if labels and not L["banner"]:
        bh = max(_body(left["sprite"])[1], _body(right["sprite"])[1]) * k
        ly = min(cy + bh // 2 + 4, L["cap_y"] - LINE - 6)
        for th, x in ((left, lx), (right, rx)):
            if th.get("label"):
                text(img, x, ly, th["label"], INK, align="c")
    return img
