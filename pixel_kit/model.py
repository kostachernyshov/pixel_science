# The mechanism model of a video: what takes part in the story and how, with a source for each relation.
# Rule (any science): each frame works at one level of detail; what is drawn at that level is true to the
# sources. What lies below the level may be left out, never replaced by fiction.
#
#   model:
#     things:                                  # actors of action scenes are things (actor name, or thing: t)
#       t:     {parts: {tcr: {label: TCR, color: GREEN}, pd1: {label: PD-1, color: LGREY}}}
#       tumor: {parts: {mhc1: {label: MHC-I, color: YELLOW}, pdl1: {label: PD-L1, color: PINK}}}
#       drug:  {color: BLUE}                   # no parts: a free agent
#     relations:                               # 3 to 6, each with "<source number>: <short quote>"
#       signal:   {kind: bind,     a: tcr,  b: mhc1,  source: "1: TCR recognizes peptide on MHC class I"}
#       brake:    {kind: bind,     a: pd1,  b: pdl1,  source: "2: ..."}
#       cover:    {kind: occupy,   a: drug, b: pdl1,  source: "4: ..."}
#       granules: {kind: transfer, a: t,    b: tumor, source: "1: ..."}
#       death:    {kind: destroy,  a: t,    b: tumor, after: granules, source: "1: ..."}
#
# Kinds fit any science:
#   bind      a part of one thing and a part of another touch and hold (receptor and ligand, two plates)
#   occupy    a free agent sits on a part; the part lets go of its binds (a drug on a receptor)
#   transfer  something passes from thing a to thing b (granules, a photon, heat)
#   change    thing b changes state because of a
#   destroy   a ends b (apoptosis, a decay); b stays gone
#
# A pack verb names the kinds it shows (relation: in verbs.yaml). A beat with such a verb must match a relation
# of the model: its actor and target are the relation's a and b (parts or things). The level follows from it:
# a beat between parts needs both parts shown on their owners (actor field parts: [...]) and close enough to
# touch; parts are drawn on stalks out of the membrane, and partners get a matching lock-and-key head made
# from the relation, so no table of who binds whom is needed.

import functools, math, zlib
from PIL import ImageDraw
from .palette import C, BLACK, NAMES
from .timing import clamp, ease
from . import sprites as S, verbs, frame

KINDS = ("bind", "occupy", "transfer", "change", "destroy")
ROWS = 7                 # head height in units
HEAD = 6                 # length of a bound pair of heads, in units
STALK = 3                # free stalk, in units
REACH = 26               # longest stalk to reach a partner, in units
SNAP = 0.4               # s: a bind closes or opens
GLIDE = 0.6              # s: an agent moves onto its part
PROFILES = [
    [0, 3, 3, 3, 3, 3, 0], [0, 1, 2, 3, 2, 1, 0], [0, 3, 3, 0, 3, 3, 0], [0, 0, 3, 3, 3, 0, 0],
    [3, 2, 1, 0, 1, 2, 3], [0, 0, 0, 3, 0, 0, 0], [3, 3, 0, 0, 0, 3, 3],
]
PLAIN = [0, 0, 1, 1, 1, 0, 0]


# ---------------------------------------------------------------- the model

def get(plan):
    m = plan.get("model") or {}
    return m.get("things") or {}, m.get("relations") or {}


def parts(plan):
    """{part: (thing, meta)}"""
    out = {}
    for th, d in get(plan)[0].items():
        for p, pm in ((d or {}).get("parts") or {}).items():
            out[p] = (th, pm or {})
    return out


def thing_of(name, a):
    return a.get("thing", name)


def _palette(name, default):
    return NAMES.index(name) if name in NAMES else default


def slots(plan):
    """{part: slot}: partners of a bind share a slot, so their heads face each other."""
    rels = get(plan)[1]
    out, n = {}, 0
    for r in rels.values():
        if r.get("kind") == "bind":
            out.setdefault(r["a"], n)
            out.setdefault(r["b"], n)
            n += 1
    for p in parts(plan):
        if p not in out:
            out[p] = n
            n += 1
    return out, max(n, 1)


def site(plan, part):
    """(relation, role a/b, profile) of the first bind of a part: it sets the head shape."""
    rels = get(plan)[1]
    binds = [n for n, r in rels.items() if r.get("kind") == "bind"]
    for i, (n, r) in enumerate((n, rels[n]) for n in binds):
        if part in (r.get("a"), r.get("b")):
            k = (zlib.crc32(n.encode()) + i) % len(PROFILES)
            return n, ("a" if r["a"] == part else "b"), PROFILES[k]
    return None, "b", PLAIN


def cells(prof, role):
    """Head cells (col, row); col 0 at the stalk, cols grow toward the partner."""
    if role == "a":
        return [(c, r) for r in range(ROWS) for c in range(4 - prof[r])]
    return [(c, r) for r in range(ROWS) for c in range(2 + prof[r])]


def kinds_of(verb):
    v = verbs.get(verb)
    k = v.get("relation")
    return [k] if isinstance(k, str) else list(k or [])


def match(plan, beat, actors):
    """The relation a beat shows: (name, relation) or (None, problem) or (None, None) for a verb with no relation."""
    if not beat.get("verb"):
        return None, None
    try:
        ks = kinds_of(beat["verb"])
    except KeyError:
        return None, None
    if not ks:
        return None, None
    things, rels = get(plan)
    P = parts(plan)

    def name_of(x):
        if x in P:
            return x
        return thing_of(x, actors[x]) if x in actors else x
    a, b = name_of(beat.get("actor")), name_of(beat.get("target"))
    for n, r in rels.items():
        if r.get("kind") not in ks:
            continue
        if r.get("kind") == "destroy" and r.get("b") == a and not beat.get("target"):
            return n, r
        if {r.get("a"), r.get("b")} == {a, b} or (r.get("a"), r.get("b")) == (a, b):
            return n, r
    who = f"{beat.get('actor')}" + (f" and {beat.get('target')}" if beat.get("target") else "")
    return None, (f"verb {beat['verb']} shows a {'/'.join(ks)} relation, but the model has none for {who} "
                  f"(add it to model: relations, with a source)")


# ---------------------------------------------------------------- state over the whole plan

def _events(plan):
    """[(scene index, t, kind, key, extra)] in story order."""
    out = []
    for i, sc in enumerate(plan["scenes"]):
        actors = sc.get("actors") or {}
        for b in sorted(sc.get("beats") or [], key=lambda b: float(b.get("t", 0))):
            if "shows" in b:              # drawn by custom code: still part of the story (a destroyed thing stays gone)
                n = b["shows"] if sc.get("type") == "custom" else None
                r = get(plan)[1].get(n) if n else None
            else:
                n, r = match(plan, b, actors)
            if not n or not r:
                continue
            t = float(b.get("t", 0))
            out.append((i, t, r["kind"], n, b))
    return out


def owner(plan, sc, part, t=None, beats=None):
    """The actor of the scene that carries this part (the first actor of its thing that shows it)."""
    P = parts(plan)
    if part not in P:
        return part if part in (sc.get("actors") or {}) else None
    th = P[part][0]
    for name, a in (sc.get("actors") or {}).items():
        if thing_of(name, a) == th and part in shown_parts(a, beats or sc.get("beats") or [], name, t):
            return name
    for name, a in (sc.get("actors") or {}).items():
        if thing_of(name, a) == th:
            return name
    return None


def shown_parts(a, beats, name, t=None):
    ps = list(a.get("parts") or [])
    for b in sorted((b for b in beats if b.get("actor") == name and "parts" in b), key=lambda b: float(b.get("t", 0))):
        if t is not None and float(b.get("t", 0)) > t:
            break
        ps = list(b["parts"] or [])
    return ps


def world(plan):
    """For each scene, the state at its start: bound {(rel, actor_a, actor_b): t_on}, occupied
    {(rel, agent, owner): t_on}, dead {actor}. Times of earlier scenes are -inf (settled)."""
    rels = get(plan)[1]
    if "_world" in plan:
        return plan["_world"]
    bound, occ, dead, out = {}, {}, set(), []
    ev = _events(plan)
    for i, sc in enumerate(plan["scenes"]):
        out.append({"bound": {k: -1e9 for k in bound}, "occupied": {k: -1e9 for k in occ}, "dead": set(dead)})
        for (j, t, kind, n, b) in ev:
            if j != i:
                continue
            r = rels[n]
            if "shows" in b:              # custom code: no actors to bind; a destroyed thing stays gone
                if kind == "destroy":
                    dead.add(r["b"])
                continue
            if kind == "bind":
                bound[(n, owner(plan, sc, r["a"], t), owner(plan, sc, r["b"], t))] = t
            elif kind == "occupy":
                ow = owner(plan, sc, r["b"], t)
                occ[(n, b.get("actor"), ow)] = t
                for k in list(bound):
                    if r["b"] in (rels[k[0]]["a"], rels[k[0]]["b"]) and ow in k[1:]:
                        del bound[k]
            elif kind == "destroy":
                dead.add(b.get("actor") if not b.get("target") else b.get("target"))
    plan["_world"] = out
    return out


def scene_state(plan, si, sc, t):
    """bound {key: (t_on, t_off or None)}, occupied {key: t_on} at time t of scene si."""
    rels = get(plan)[1]
    st = world(plan)[si]
    bound = {k: (v, None) for k, v in st["bound"].items()}
    occ = dict(st["occupied"])
    for (j, bt, kind, n, b) in _events(plan):
        if j != si or bt > t:
            continue
        r = rels[n]
        if kind == "bind":
            bound[(n, owner(plan, sc, r["a"], bt), owner(plan, sc, r["b"], bt))] = (bt, None)
        elif kind == "occupy":
            ow = owner(plan, sc, r["b"], bt)
            occ[(n, b.get("actor"), ow)] = bt
            for k, (on, off) in list(bound.items()):
                if off is None and r["b"] in (rels[k[0]]["a"], rels[k[0]]["b"]) and ow in k[1:]:
                    bound[k] = (on, bt)
    return bound, occ


# ---------------------------------------------------------------- drawing

@functools.lru_cache(maxsize=4096)
def _ray(name, anim_k, d, off, flip=False):
    """Steps from the sprite's anchor (shifted by off across d) to its last opaque pixel along d, or None."""
    im = S.frame(name, "idle", 0, flip, anim_k)
    ax, ay = S.meta()[name]["anchor"]
    if flip:
        ax = S.meta()[name]["cell"][0] - ax
    nx, ny = abs(d[1]), abs(d[0])
    x, y, last = ax * anim_k + nx * off, ay * anim_k + ny * off, None
    for s in range(0, max(im.size)):
        xx, yy = int(x + d[0] * s), int(y + d[1] * s)
        if not (0 <= xx < im.width and 0 <= yy < im.height):
            break
        if im.getpixel((xx, yy))[3] > 0:
            last = s
    return last


def fit_off(name, anim_k, d, off, flip=False):
    """The offset nearest to off at which a row still meets the body (a row past the side of a small body
    moves in)."""
    while _ray(name, anim_k, d, off, flip) is None and abs(off) >= 1:
        off -= math.copysign(1, off)
    return off


def _edge(name, anim_k, px, py, d, off, flip=False):
    """The membrane point of the sprite (as drawn, flipped or not) from its anchor along direction d, shifted by
    off across it."""
    nx, ny = abs(d[1]), abs(d[0])          # a fixed side axis: partners on both bodies share their offset
    last = _ray(name, anim_k, d, off, flip)
    s = (last + 1) if last is not None else max(S.frame(name, "idle", 0, False, anim_k).size) * 0.4
    return px + nx * off + d[0] * s, py + ny * off + d[1] * s


def _axis(dx, dy):
    if abs(dx) >= abs(dy):
        return (1 if dx >= 0 else -1, 0)
    return (0, 1 if dy >= 0 else -1)


def unit(k):
    """Head unit at sprite scale k: readable, never larger than the body needs."""
    return 1 if k <= 1 else max(2, k - 1)


def reach(name, k, d, off=0, flip=False):
    """Distance from the sprite's anchor to its edge along direction d (any unit vector), off across it."""
    ex, ey = _edge(name, k, 0, 0, d, off, flip)
    return ex * d[0] + ey * d[1] - (abs(d[1]) * off * d[0] + abs(d[0]) * off * d[1])


def bind_range(plan, pa, pb, u, d, mols=(False, False), labels=True):
    """(lo, hi): the gaps between the two membranes at which parts pa and pb bind along axis d: room for both
    heads, and on a level axis for both labels between the bodies, but within the reach of the stalks.
    mols: which of the two sit on a molecule (no stalk, no head: one stalk and one head span the gap)."""
    P = parts(plan)
    stalked = [p for p, m in zip((pa, pb), mols) if not m]
    if not stalked:
        return 0, 2 * u                 # two molecules: edge to edge
    n = len(stalked)
    lo = (HEAD * n // 2 + 2) * u
    hi = (n * REACH + HEAD * n // 2) * u
    if labels and d[0] and frame.H >= 160:     # labels on their stalks, if the stalks can reach that far
        room = HEAD * n // 2 * u + n * (max(_label_w(P, p) for p in stalked) + 2)
        lo = room if room <= hi else lo   # else they sit by the heads, one above and one below (_label_box)
    return lo, hi


def is_molecule(sprite):
    return S.meta()[sprite].get("body") == "molecule"


def bind_between(plan, sc, me, tg, beats, t):
    """The first bind relation (name, part of me, part of tg) between parts that these two actors show at t,
    or None."""
    actors = sc.get("actors") or {}
    if me not in actors or tg not in actors:
        return None
    P = parts(plan)
    tm, tt = thing_of(me, actors[me]), thing_of(tg, actors[tg])
    sm, st = shown_parts(actors[me], beats, me, t), shown_parts(actors[tg], beats, tg, t)
    for n, r in get(plan)[1].items():
        if r.get("kind") != "bind" or r.get("a") not in P or r.get("b") not in P:
            continue
        for pa, pb in ((r["a"], r["b"]), (r["b"], r["a"])):
            if (P[pa][0], P[pb][0]) == (tm, tt) and pa in sm and pb in st:
                return n, pa, pb
    return None


def _head(dr, ox, oy, d, u, prof, role, col):
    """Draw head cells from (ox, oy), the stalk tip, toward direction d. Cells are centered, so a head and its
    partner's head (drawn from the other side, d reversed) fill each other's gaps exactly."""
    n = (-d[1], d[0])
    pts = []
    for c, r in cells(prof, role):
        along, acr = (c + 0.5) * u, (r - (ROWS - 1) / 2) * u
        pts.append((ox + d[0] * along + n[0] * acr, oy + d[1] * along + n[1] * acr))
    h = u / 2
    cells_ = [(round(x - h), round(y - h)) for x, y in pts]     # each cell exactly u px, at any position
    for x0, y0 in cells_:               # outline, then fill
        dr.rectangle([x0 - 1, y0 - 1, x0 + u, y0 + u], fill=C(BLACK))
    for x0, y0 in cells_:
        dr.rectangle([x0, y0, x0 + u - 1, y0 + u - 1], fill=C(col))


def layout_parts(plan, sc, t, state, beats):
    """{part@actor: geometry} for the shown parts: base, direction, unit, slot offset."""
    P = parts(plan)
    rels = get(plan)[1]
    sl, _ = slots(plan)
    actors = sc.get("actors") or {}
    shown = {name: [p for p in shown_parts(a, beats, name, t) if p in P and P[p][0] == thing_of(name, a)]
             for name, a in actors.items() if name in state and state[name][8]}
    rows = scene_rows(plan, sc, beats)
    out = {}
    for name, ps in shown.items():
        a = actors[name]
        px, py, r, k = state[name][:4]
        u = unit(k)
        for p in ps:
            target = None
            for rel in rels.values():                       # face the nearest owner of a partner
                if rel.get("kind") == "bind" and p in (rel["a"], rel["b"]):
                    q = rel["b"] if rel["a"] == p else rel["a"]
                    o = owner(plan, sc, q, t, beats)
                    if o in state and state[o][8] and o != name and (target is None or
                            math.hypot(state[o][0] - px, state[o][1] - py) <
                            math.hypot(state[target][0] - px, state[target][1] - py)):
                        target = o
            if target is None:
                others = [o for o in state if o != name and state[o][8] and o in actors and actors[o].get("parts")]
                others = others or [o for o in state if o != name and state[o][8]]
                if others:
                    target = min(others, key=lambda o: math.hypot(state[o][0] - px, state[o][1] - py))
            d = _axis(state[target][0] - px, state[target][1] - py) if target else (1, 0)
            off = (rows.index(sl[p]) - (len(rows) - 1) / 2) * (ROWS + 3) * u
            mol = is_molecule(a["sprite"])          # its site is drawn in the sprite: no stalk
            fl = bool(state[name][6])
            out[(p, name)] = {"d": d, "u": u, "off": fit_off(a["sprite"], k, d, off, fl), "mol": mol,
                              "_at": (a["sprite"], k, px, py, fl)}
    near = {}                       # partners share a row: the offset that fits on every body of the slot
    for (p, name), g in out.items():
        o = near.get(sl[p])
        near[sl[p]] = g["off"] if o is None or abs(g["off"]) < abs(o) else o
    for (p, name), g in out.items():
        sprite, k, px, py, fl = g.pop("_at")
        g["off"] = near[sl[p]]
        g["base"] = _edge(sprite, k, px, py, g["d"], g["off"], fl)
    return out


def scene_rows(plan, sc, beats):
    """The slots of the parts that the scene shows at any time, packed: rows stay put when parts come and go."""
    P = parts(plan)
    sl, _ = slots(plan)
    ps = set()
    for name, a in (sc.get("actors") or {}).items():
        ps.update(a.get("parts") or [])
    for b in beats:
        ps.update(b.get("parts") or [])
    return sorted({sl[p] for p in ps if p in P})


def head_at(g, sx, sy):
    """The center of a part's head from its stalk tip; a molecule's site is its edge (no head)."""
    a = 0 if g["mol"] else 3 * g["u"]
    return sx + g["d"][0] * a, sy + g["d"][1] * a


def _label_box(lab, g, bx, by, sx, sy, length):
    """(left, top, right, bottom) of a part's label. Level axis: above or below the head (the outer side of its
    row), on its own stalk when bound and long enough. Upright axis: beside the stalk, so that it needs no gap."""
    from .font import text_w, LINE
    d, u = g["d"], g["u"]
    w = text_w(str(lab))
    hx, hy = head_at(g, sx, sy)
    if d[0]:
        on_stalk = length >= w + 2                           # bound: on its own stalk (the room rule keeps it there)
        cx = (bx + sx) / 2 if on_stalk else hx
        if g["mol"]:                                         # no stalk: over its own body, out of the gap
            on_stalk, cx = True, bx - d[0] * (w / 2 + 2)
        # the outer side of its row; one row and by the head: partners face opposite ways, so one above, one below
        side = (-1 if g["off"] <= 0 else 1) if on_stalk or g["off"] else -d[0]
        top = hy + side * (ROWS * u / 2 + 1) - (LINE if side < 0 else 0)
    else:                                                  # partners face opposite ways: labels on opposite sides
        cx = hx + d[1] * (ROWS * u / 2 + 4 + w / 2)
        top = (by + sy) / 2 - LINE / 2
    return (cx - w / 2, top, cx + w / 2, top + LINE)


def stalks(plan, si, sc, t, state, beats):
    """[(part, actor, g, base, tip, length, label box or None)] of the shown parts at time t: bound pairs stretch
    their stalks to meet in the middle."""
    rels = get(plan)[1]
    P = parts(plan)
    geo = layout_parts(plan, sc, t, state, beats)
    bound, _ = scene_state(plan, si, sc, t)
    ext = {}
    for (n, aa, ab), (on, off) in bound.items():
        r = rels[n]
        ga, gb = geo.get((r["a"], aa)), geo.get((r["b"], ab))
        if not ga or not gb:
            continue
        e = ease(clamp((t - on) / SNAP)) * (1 - ease(clamp((t - off) / SNAP)) if off is not None else 1)
        ext[(r["a"], aa)] = (e, gb)
        ext[(r["b"], ab)] = (e, ga)
    out = []
    for (p, name), g in geo.items():
        bx, by = g["base"]
        d, u = g["d"], g["u"]
        free = 0 if g["mol"] else STALK * u
        length = free
        if (p, name) in ext and not g["mol"]:
            e, gp = ext[(p, name)]
            gap = (gp["base"][0] - bx) * d[0] + (gp["base"][1] - by) * d[1]
            # two heads meet in the middle; a molecule's site is its edge, so the head goes all the way to it
            want = max(free, gap - HEAD * u / 2 if gp["mol"] else (gap - HEAD * u) / 2)
            length = free + (want - free) * e
        sx, sy = bx + d[0] * length, by + d[1] * length
        lab = P[p][1].get("label")
        box = _label_box(lab, g, bx, by, sx, sy, length) if lab and frame.H >= 160 else None
        out.append((p, name, g, (bx, by), (sx, sy), length, box))
    return out


def draw(img, plan, si, sc, t, state, beats):
    """Parts on stalks, bound pairs joined, occupying agents on their part. Returns {name: (x, y, r)} of the
    part heads, so verbs can use parts as actor or target."""
    things, rels = get(plan)
    P = parts(plan)
    if not P:
        return {}
    _, occ = scene_state(plan, si, sc, t)
    dr = ImageDraw.Draw(img)
    heads = {}
    covered = {}
    for (n, agent, ow), on in occ.items():
        covered[(rels[n]["b"], ow)] = (agent, on, things.get(rels[n]["a"], {}))
    for p, name, g, (bx, by), (sx, sy), length, box in stalks(plan, si, sc, t, state, beats):
        d, u = g["d"], g["u"]
        col = _palette(P[p][1].get("color", "LGREY"), 6)
        _, role, prof = site(plan, p)
        hx, hy = head_at(g, sx, sy)
        if not g["mol"]:                # a molecule's site is drawn in its sprite; verbs aim at the edge
            w = max(1, u // 2 + 1)
            x0, x1 = sorted((bx, sx))
            y0, y1 = sorted((by, sy))
            dr.rectangle([x0 - w // 2, y0 - w // 2, x1 + w // 2, y1 + w // 2], fill=C(col))
            _head(dr, sx, sy, d, u, prof, role, col)
        heads[p] = heads.get(p) or (hx, hy, ROWS * u / 2)
        heads[f"{p}@{name}"] = (hx, hy, ROWS * u / 2)
        cov = covered.get((p, name))
        if cov and t - cov[1] >= GLIDE * 0.8 and not g["mol"]:   # the agent's head takes the partner's place
            acol = _palette(cov[2].get("color", "BLUE"), 12)
            _head(dr, sx + d[0] * HEAD * u, sy + d[1] * HEAD * u, (-d[0], -d[1]), u, prof,
                  "a" if role == "b" else "b", acol)
        if box:
            from .font import text
            text(img, (box[0] + box[2]) / 2, box[1], str(P[p][1]["label"]),
                 col if col not in (6, 7, 10, 15) else BLACK, align="c")
    return heads


def agent_place(plan, si, sc, t, state, beats):
    """Moves each occupying agent onto its part (call before the sprites are drawn)."""
    rels = get(plan)[1]
    _, occ = scene_state(plan, si, sc, t)
    if not occ:
        return
    geo = layout_parts(plan, sc, t, state, beats)
    for (n, agent, ow), on in occ.items():
        g = geo.get((rels[n]["b"], ow))
        if not g or agent not in state:
            continue
        d, u = g["d"], g["u"]
        reach = (0 if g["mol"] else (STALK + HEAD + 1) * u) + state[agent][2] * 0.6   # on a molecule: at its edge
        tx, ty = g["base"][0] + d[0] * reach, g["base"][1] + d[1] * reach
        k = ease(clamp((t - on) / GLIDE))
        state[agent][0] += (tx - state[agent][0]) * k
        state[agent][1] += (ty - state[agent][1]) * k


# ---------------------------------------------------------------- checks

def _label_w(P, part):
    from .font import text_w
    lab = P.get(part, (None, {}))[1].get("label")
    return text_w(str(lab)) if lab else 0


def _actor_labels(sc, state):
    """[(actor, box)] of the actor labels under the sprites (as explain.p_action draws them)."""
    from .font import text_w, LINE
    out = []
    for name, a in (sc.get("actors") or {}).items():
        if a.get("label") and name in state and state[name][8] and frame.H >= 160:
            px, py, _, k = state[name][:4]
            w, y = text_w(str(a["label"])), int(py) + S.meta()[a["sprite"]]["cell"][1] * k // 2 + 2
            out.append((name, (int(px) - w / 2, y, int(px) + w / 2, y + LINE)))
    return out


def _crowded(st, others=()):
    """Labels that overlap another label, a head, or an actor label (others: [(name, box)])."""
    def meets(a, b):
        return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
    heads = []
    for p, name, g, _, (sx, sy), _, _ in st:
        d, u = g["d"], g["u"]
        (hx, hy), h = head_at(g, sx, sy), ROWS * u / 2
        heads.append((p, name, (hx - h, hy - h, hx + h, hy + h)))
    out = []
    for i, (p, name, _, _, _, _, box) in enumerate(st):
        if not box:
            continue
        for q, qn, _, _, _, _, other in st[i + 1:]:
            if other and meets(box, other):
                out.append(f"label {p} covers label {q}")
        for q, qn, hb in heads:
            if (q, qn) != (p, name) and meets(box, hb):
                out.append(f"label {p} covers the head of {q}")
        for q, ob in others:
            if meets(box, ob):
                out.append(f"label {p} covers the label of {q}")
    return sorted(set(out))


def check(plan, positions=None, stage=None):
    """Problems of the model and of the beats that show it. positions(si, sc, t) -> state for the contact rule;
    stage (x0, y0, x1, y1) turns a wrong gap into the place that fixes it."""
    things, rels = get(plan)
    P = parts(plan)
    out = []
    uses = []
    for i, sc in enumerate(plan["scenes"]):
        actors = sc.get("actors") or {}
        for b in sc.get("beats") or []:
            if "shows" in b:                 # a custom scene: the code draws the relation, timed by this beat
                if sc.get("type") != "custom":
                    out.append(f"{sc.get('id')}: beat at {b.get('t')} s: shows: is for custom scenes "
                               f"(an action scene shows a relation with a verb)")
                elif b["shows"] not in rels:
                    out.append(f"{sc.get('id')}: beat at {b.get('t')} s: shows: {b['shows']!r} is not a relation in model")
                elif b.get("verb") or b.get("actor") or b.get("target"):
                    out.append(f"{sc.get('id')}: beat at {b.get('t')} s: a shows: beat has only a word (or t) "
                               f"and the relation; the custom code draws it")
                else:
                    uses.append((i, sc, b, b["shows"], rels[b["shows"]]))
                continue
            n, r = match(plan, b, actors)
            if n:
                uses.append((i, sc, b, n, r))
            elif r and (rels or True):
                out.append(f"{sc.get('id')}: beat at {b.get('t')} s: {r}")
        for name, a in actors.items():
            th = thing_of(name, a)
            for p in shown_parts(a, sc.get("beats") or [], name) + [p for b in sc.get("beats") or []
                                                                    if b.get("actor") == name for p in (b.get("parts") or [])]:
                if p not in P:
                    out.append(f"{sc.get('id')}: actor {name}: {p!r} is not a part in model: things")
                elif P[p][0] != th:
                    out.append(f"{sc.get('id')}: actor {name}: {p} belongs to {P[p][0]}, not to {th} (ownership)")
    if not rels:
        return out
    nsrc = len(plan.get("sources") or [])
    for n, r in rels.items():
        tag = f"model relation {n}"
        k, a, b = r.get("kind"), r.get("a"), r.get("b")
        if k not in KINDS:
            out.append(f"{tag}: kind must be one of {', '.join(KINDS)}")
            continue
        src = str(r.get("source", ""))
        num = src.split(":")[0].strip()
        if not num.isdigit() or not 1 <= int(num) <= nsrc or len(src.split(":", 1)) < 2 or not src.split(":", 1)[1].strip():
            out.append(f"{tag}: source must be '<number in sources (1..{nsrc})>: <short quote>'")
        if k == "bind":
            for x in (a, b):
                if x not in P:
                    out.append(f"{tag}: {x!r} is not a part of a thing")
            if a in P and b in P and P[a][0] == P[b][0]:
                out.append(f"{tag}: {a} and {b} sit on the same thing; a bind joins parts of two things")
        elif k == "occupy":
            if a not in things or (things[a] or {}).get("parts"):
                out.append(f"{tag}: {a!r} must be a free agent in things (no parts)")
            if b not in P:
                out.append(f"{tag}: {b!r} is not a part of a thing")
        else:
            for x in (a, b):
                if x not in things and x not in P:
                    out.append(f"{tag}: {x!r} is not a thing or a part of the model")
        if r.get("after") and r["after"] not in rels:
            out.append(f"{tag}: after: {r['after']!r} is not a relation")
    if out:
        return out
    first = {}
    seq = 0
    for i, sc, b, n, r in sorted(uses, key=lambda u: (u[0], float(u[2].get("t", 0)))):
        seq += 1
        first.setdefault(n, (i, float(b.get("t", 0))))
    for i, sc, b, n, r in uses:
        sid, bt = sc.get("id"), float(b.get("t", 0))
        if r.get("after"):
            f = first.get(r["after"])
            if not f or f > (i, bt):
                out.append(f"{sid}: beat at {bt} s shows {n} before {r['after']} (causality: after)")
        if r["kind"] in ("bind", "occupy") and "shows" not in b:
            for x in ([r["a"], r["b"]] if r["kind"] == "bind" else [r["b"]]):
                ow = owner(plan, sc, x, bt)
                a = (sc.get("actors") or {}).get(ow)
                if not a or x not in shown_parts(a, sc.get("beats") or [], ow, bt):
                    out.append(f"{sid}: beat at {bt} s: {x} is not shown on its owner (add it to the actor's parts:)")
    dead_by_scene = [w["dead"] for w in world(plan)]
    for i, sc in enumerate(plan["scenes"]):
        for name, a in (sc.get("actors") or {}).items():
            if name in dead_by_scene[i] and not a.get("hidden"):
                out.append(f"{sc.get('id')}: actor {name!r} was destroyed in an earlier scene and cannot come back")
    used = {u[3] for u in uses}
    for n in rels:
        if n not in used:
            out.append(f"model relation {n}: no beat shows it (a verb with this relation kind, "
                       f"or shows: {n} in a custom scene)")
    notes = [f"warning: {sc.get('id')}: relation {n} is shown by custom code; its order and source are "
             f"checked, its drawing is not" for i, sc, b, n, r in uses if "shows" in b]
    if positions and not out:
        for i, sc, b, n, r in uses:
            if r["kind"] != "bind" or "shows" in b:
                continue
            bt = float(b.get("t", 0))
            state = positions(i, sc, bt + SNAP)
            geo = layout_parts(plan, sc, bt + SNAP, state, sc.get("beats") or [])
            ga = geo.get((r["a"], owner(plan, sc, r["a"], bt)))
            gb = geo.get((r["b"], owner(plan, sc, r["b"], bt)))
            if not ga or not gb:
                continue
            d, u = ga["d"], ga["u"]
            gap = (gb["base"][0] - ga["base"][0]) * d[0] + (gb["base"][1] - ga["base"][1]) * d[1]
            lo, hi = bind_range(plan, r["a"], r["b"], u, d, (ga["mol"], gb["mol"]))
            oa, ob = owner(plan, sc, r["a"], bt), owner(plan, sc, r["b"], bt)
            fix = f": move {ob} with move_to: {oa}"
            if stage and lo <= hi and ob in state:          # where the partner's owner may stand on the axis
                ax = 0 if d[0] else 1
                a0, a1 = (stage[0], stage[2]) if ax == 0 else (stage[1], stage[3])
                ends = sorted(state[ob][ax] + (g - gap) * d[ax] for g in (lo + 1, hi - 1))
                f0, f1 = ((e - a0) / ((a1 - a0) or 1) for e in ends)
                fix = f": place {ob} at {'xy'[ax]} {f0:.2f} to {f1:.2f}, or move it with move_to: {oa}"
            if gb["d"] != (-d[0], -d[1]) or gap < bind_range(plan, r["a"], r["b"], u, d, (ga["mol"], gb["mol"]),
                                                            labels=False)[0]:
                out.append(f"{sc.get('id')}: beat at {bt} s: {r['a']} and {r['b']} do not face each other across a gap "
                           f"(contact){fix}")
            elif gap < lo:
                out.append(f"{sc.get('id')}: beat at {bt} s: {r['a']} and {r['b']} have no room for their labels "
                           f"({gap:.0f} px between the bodies) (contact){fix}")
            elif gap > hi:
                out.append(f"{sc.get('id')}: beat at {bt} s: {r['a']} and {r['b']} are {gap:.0f} px apart, too far to touch "
                           f"(contact){fix}")
            else:
                out += [f"{sc.get('id')}: beat at {bt} s: {x} (contact): move the things apart, make them larger, or show fewer parts"
                        for x in _crowded(stalks(plan, i, sc, bt + SNAP, state, sc.get("beats") or []),
                                         _actor_labels(sc, state))]
    return out + notes
