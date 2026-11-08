# Actor state: where each actor of an action scene is and how it looks at time t.
#
#   problems = stage.resolve(plan, times)   # once per plan, after word times: continue, behaviors, verb show/hide
#   for name, s in stage.state_at(plan, sc, t, L).items():
#       s.x, s.y, s.k, s.anim, s.flip, s.shown, s.look, s.marks ...
#
# Only contact depends on the format: the place where move_to: <actor> stops comes from the sprites' sizes on the
# stage. resolve leaves it as a name; state_at finds the place for the current layout L.

import math
from dataclasses import dataclass
from typing import NamedTuple
from .timing import clamp, seg, ease, lerp
from . import sprites as S, verbs, model, sets

GHOST_S = 1.0          # s: an actor fades to its ghost, or a ghost comes back
HEAD_GAP = model.HEAD + 2 * model.STALK + 4      # units: a bind placed by move_to shows both stalks
BEHAVIORS = ("wander", "hunt", "divide")
WANDER_STEP = 1.5        # s: one walk of wander
HUNT_MOVE = 1.2          # s: hunt goes to each target in this time
APART = 0.12             # fraction of the zone: a cell steps this far aside when its daughter appears


@dataclass
class ActorState:
    """An actor at time t. at: its place in fractions of its box; x, y: pixels; r: half the sprite's size; k: its
    scale. look: (before, now, progress) of real, ghost, none. marks: (list, time given). rest: 1 when nothing
    moves it (a little motion at rest), 0 while something does. box: the box its fractions are of."""
    at: tuple
    x: float
    y: float
    r: float
    k: int
    anim: str
    anim_t: float
    flip: bool
    badge: object
    shown: bool
    look: tuple
    marks: tuple
    rest: float
    box: tuple


# ---------------------------------------------------------------- the interface

def resolve(plan, times):
    """Makes the plan play as it is drawn, for every format: continue scenes get the set, background, title, and
    actors of the scene before (as they are at its end); behaviors become plain beats; the show and hide of
    verbs become beats. move_to: <actor> stays a name (state_at places it). Runs once per plan.
    times: [(start, end)] of the scenes. Returns problems."""
    prev, problems = None, []
    for i, sc in enumerate(plan["scenes"]):
        if sc.get("continue") and prev is not None and prev.get("type") == sc.get("type") == "action":
            _carry(plan, prev, sc, i, times[i - 1][1] - times[i - 1][0])
        problems += _behave(plan, sc, times[i][1] - times[i][0])
        if sc.get("type") == "action":
            sc["beats"] = _with_verbs(sc.get("beats") or [])
        prev = sc
    return problems


def state_at(plan, sc, t, L):
    """{actor: ActorState} of an action scene at time t, for the layout L of the current format."""
    beats = _beats(plan, sc, L)
    out = {}
    for name, a in (sc.get("actors") or {}).items():
        x, y, anim, anim_t, flip, badge, shown, look, marks = _fold(a, beats, name, t, _start(plan, sc, name, L))
        k = _scale(sc, a, L)
        cw, ch = S.meta()[a["sprite"]]["cell"]
        px, py = _place(sc, a, L, x, y, k)
        out[name] = ActorState((x, y), px, py, max(cw, ch) * k / 2, k, anim, anim_t, flip, badge, shown, look, marks,
                               0.0 if a.get("still") else _at_rest(beats, name, t), _box(sc, a, L))
    return out


# ---------------------------------------------------------------- one pass over an actor's beats

class _Seen(NamedTuple):
    """An actor at time t before a layout: place in fractions (x, y) and how it looks."""
    x: float
    y: float
    anim: str
    anim_t: float
    flip: bool
    badge: object
    shown: bool
    look: tuple
    marks: tuple


def _fold(a, beats, name, t, start):
    """_Seen of an actor at time t. A move_to that is still an actor's name (resolve, before a format) does not
    move it."""
    x, y = start
    anim, a_t0 = a.get("anim", "idle"), 0.0
    flip, badge, shown = bool(a.get("flip", False)), a.get("badge"), not a.get("hidden", False)
    look = "ghost" if a.get("ghost") else "real"
    prev, u, g_t0 = look, 1.0, 0.0
    marks, m_t0 = a.get("marks") or [], 0.0
    shown_before, last = shown, None
    for b in sorted((b for b in beats if b.get("actor") == name), key=lambda b: float(b.get("t", 0))):
        bt = float(b.get("t", 0))
        if t < bt:
            break
        if bt != last:                    # shown just before this time: a ghost beat starts from it
            shown_before, last = shown, bt
        if "ghost" in b:                  # true fades to its ghost (a hidden actor appears as one); false: back
            u_then = min(1.0, (bt - g_t0) / GHOST_S) if prev != look else 1.0
            seen = look if u_then >= 0.5 else prev          # a fade that still runs: start from what is on screen
            prev = seen if shown_before else "none"
            look, u, g_t0 = "ghost" if b["ghost"] else "real", min(1.0, (t - bt) / GHOST_S), bt
            shown = True
        if "move_to" in b and not isinstance(b["move_to"], str):
            k = ease(seg(t, bt, bt + float(b.get("dur", 1.0))))
            tx, ty = b["move_to"]
            x, y = lerp(x, tx, k), lerp(y, ty, k)
        if "anim" in b:
            anim, a_t0 = b["anim"], bt
        if "flip" in b:
            flip = bool(b["flip"])
        if "badge" in b:
            badge = b["badge"]
        if "show" in b:
            shown = bool(b["show"])
        if "marks" in b:
            marks, m_t0 = b["marks"] or [], bt
    return _Seen(x, y, anim, t - a_t0, flip, badge, shown, (prev, look, u), (marks, m_t0))


def _prev(plan, sc):
    """The scene a continue scene goes on from, or None."""
    if not sc.get("continue"):
        return None
    i = next(i for i, s in enumerate(plan["scenes"]) if s is sc)
    return plan["scenes"][i - 1] if i else None


def _start(plan, sc, name, L):
    """Where an actor stands when the scene starts: its at:; in a continue scene without at:, where it stood at
    the end of the scene before (its last move done); else the middle."""
    a = sc["actors"][name]
    if "at" in a:
        return tuple(a["at"])
    prev = _prev(plan, sc)
    if prev is not None and name in (prev.get("actors") or {}):
        s = _fold(prev["actors"][name], _beats(plan, prev, L), name, math.inf, _start(plan, prev, name, L))
        return round(s.x, 4), round(s.y, 4)
    return 0.5, 0.5


def _by_contact(plan, sc, beats, name, t):
    """True when the actor's place at t comes from a move_to: <actor>, so it is known only in a format."""
    moves = [b for b in beats if b.get("actor") == name and "move_to" in b and float(b.get("t", 0)) <= t]
    if moves:
        return isinstance(max(moves, key=lambda b: float(b.get("t", 0)))["move_to"], str)
    prev = _prev(plan, sc)
    return ("at" not in sc["actors"][name] and prev is not None and name in (prev.get("actors") or {})
            and _by_contact(plan, prev, prev.get("beats") or [], name, math.inf))


def _at_rest(beats, name, t, near=0.4):
    """1 when no move of the actor, and no verb by it or on it, runs at time t; 0 while one runs; between the
    two in the near s around it (the motion at rest fades out and in)."""
    f = 1.0
    for b in beats:
        if name not in (b.get("actor"), b.get("target")):
            continue
        bt = float(b.get("t", 0))
        d = float(b.get("dur", 1.0)) if "move_to" in b else (_verb_s(b["verb"]) if b.get("verb") else None)
        if d is not None:
            f = min(f, clamp(max(bt - t, t - bt - d, 0.0) / near))
    return f


def _verb_s(name):
    try:
        return verbs.duration(name)
    except KeyError:              # an unknown verb: check reports it
        return 0.5


def _with_verbs(beats):
    """The beats plus the show/hide beats that verbs add (show: at the start, hide: at the end)."""
    out = list(beats)
    for b in beats:
        if not b.get("verb"):
            continue
        try:
            v = verbs.get(b["verb"])
        except KeyError:          # an unknown verb: check reports it
            continue
        bt = float(b.get("t", 0))
        for key, when, val in (("show", bt, True), ("hide", bt + verbs.duration(b["verb"]), False)):
            who = v.get(key)
            name = b.get(who) if who == "target" else b.get("actor")
            if not who or (not val and any(g.get("actor") == name and g.get("ghost") is True
                                           and bt <= float(g.get("t", 0)) <= when for g in beats)):
                continue                  # a ghost: true beat during the verb: the actor stays, as a ghost
            out.append({"t": when, "actor": name, "show": val})
    return out


# ---------------------------------------------------------------- places for the current format

def _box(sc, a, L):
    """The box that an actor's fractions (at:, move_to: [x, y]) are of: its zone of the set, or the stage."""
    z = a.get("in")
    if z and sc.get("set"):
        zs = sets.zones(sc["set"], L)
        if z == "all" and zs:
            return next(iter(zs.values()))
        if z in zs:
            return zs[z]
    return L["stage"]


def _zone_room(sc, a, L):
    """(width, height) a sprite may take in its zone; on the border, the room of the smaller side."""
    x0, y0, x1, y1 = _box(sc, a, L)
    if a["in"] == "border":
        s0, s1 = L["stage"][1], L["stage"][3]
        return x1 - x0, 2 * min(y0 - s0, s1 - y0)
    return x1 - x0, y1 - y0


def _scale(sc, a, L):
    """The sprite scale of an actor. In a set, the actors in its zones share one scale, so sizes still
    compare: the largest at which each fits its zone (in the banner or in small panels, down to 1)."""
    k = int(a.get("scale", L["sprite_scale"]))
    if not (a.get("in") and sc.get("set")):
        return k
    for b in (sc.get("actors") or {}).values():
        if b.get("in") and "scale" not in b:
            w, h = _zone_room(sc, b, L)
            cw, ch = S.meta()[b["sprite"]]["cell"]
            while k > 1 and (cw * k > w or ch * k > h):
                k -= 1
    return k


def _place(sc, a, L, fx_, fy_, k):
    """Pixel place of an actor from its fractions. In a zone of a set, the sprite stays inside the zone."""
    x0, y0, x1, y1 = _box(sc, a, L)
    px, py = x0 + fx_ * (x1 - x0), y0 + fy_ * (y1 - y0)
    if a.get("in") and sc.get("set"):
        cw, ch = S.meta()[a["sprite"]]["cell"]
        hw, hh = cw * k / 2, ch * k / 2
        if a["in"] == "border":                      # on the line, inside the stage
            x0, x1 = L["stage"][0], L["stage"][2]
            y0, y1 = L["stage"][1], L["stage"][3]
        px = min(max(px, x0 + hw), x1 - hw) if x1 - x0 > 2 * hw else (x0 + x1) / 2
        py = min(max(py, y0 + hh), y1 - hh) if y1 - y0 > 2 * hh else (y0 + y1) / 2
    return px, py


def _beats(plan, sc, L):
    """The scene's beats; for a layout, with each move_to: <actor> turned into the place where the mover
    touches that actor (fractions of its box). Kept in plan.placed per scene and format: after resolve,
    nothing changes the beats."""
    beats = sc.get("beats") or []
    if L is None or not any(isinstance(b.get("move_to"), str) for b in beats):
        return beats
    key = (next(i for i, s in enumerate(plan["scenes"]) if s is sc), L["W"], L["H"], tuple(L["stage"]))
    placed = plan.placed
    if key not in placed:
        todo = [i for i, b in enumerate(beats) if isinstance(b.get("move_to"), str)]
        out = list(beats)
        for _ in range(2):          # twice: a target that itself moves to an actor is placed by the first pass
            out = _approach(plan, sc, beats, out, todo, L)
        placed[key] = out
    return placed[key]


def _approach(plan, sc, beats, done, todo, L):
    """The place where the mover touches the target: edge to edge along the way it comes, or, when their parts
    bind, at the gap of the bind on a level or upright axis. Sizes come from the sprites."""
    actors = sc.get("actors") or {}
    out = list(done)
    for i in sorted(todo, key=lambda i: float(beats[i].get("t", 0))):
        b = beats[i]
        me, tg = b.get("actor"), b.get("move_to")
        if me not in actors or tg not in actors or me == tg:
            continue
        bt, end = float(b.get("t", 0)), float(b.get("t", 0)) + float(b.get("dur", 1.0))
        mover = _fold(actors[me], out, me, bt, _start(plan, sc, me, L))
        target = _fold(actors[tg], out, tg, end, _start(plan, sc, tg, L))
        km, kt = _scale(sc, actors[me], L), _scale(sc, actors[tg], L)         # sprite scales: mover, target
        mb = _box(sc, actors[me], L)
        mx, my = _place(sc, actors[me], L, mover.x, mover.y, km)
        tx, ty = _place(sc, actors[tg], L, target.x, target.y, kt)
        bind = model.bind_between(plan, sc, me, tg, out, end)
        if bind:
            d = model.axis(mx - tx, my - ty)                      # level or upright, on the target's line
            ua = model.unit(km)
            mols = (model.is_molecule(actors[me]["sprite"]), model.is_molecule(actors[tg]["sprite"]))
            lo, hi = model.bind_range(plan, bind[1], bind[2], ua, d, mols)
            gap = max(lo, min(hi - 1, max(lo + 2, HEAD_GAP * ua * (2 - sum(mols)) // 2)))  # inside, not on, the ends
        else:
            dist = math.hypot(mx - tx, my - ty) or 1.0
            d, gap = ((mx - tx) / dist, (my - ty) / dist), 0
        far = (model.reach(actors[tg]["sprite"], kt, d, flip=target.flip) + gap
               + model.reach(actors[me]["sprite"], km, (-d[0], -d[1]), flip=mover.flip))
        nx, ny = tx + d[0] * far, ty + d[1] * far
        out[i] = dict(b, move_to=[round((nx - mb[0]) / ((mb[2] - mb[0]) or 1), 4),
                                  round((ny - mb[1]) / ((mb[3] - mb[1]) or 1), 4)])
    return out


# ---------------------------------------------------------------- continue

def _carry(plan, prev, sc, i, end):
    """A continue scene goes on from the scene before: its set, background, title, and actors as they are at its
    end (place, zone, flip, badge, ghost, marks, shown). Its own actors add to these or change them. A place that
    came by contact is not copied: state_at finds it in each format."""
    own, own_keys = dict(sc.get("actors") or {}), set(sc)
    beats = prev.get("beats") or []
    for k in ("set", "bg", "title"):
        if k not in own_keys and k in prev:
            sc[k] = prev[k]
    st = sc.get("set")
    if "set" not in own_keys and st and st.get("type") == "panels":    # counters go on too
        last = sets.counters(st, beats, end)
        sc["set"] = dict(st, panels=[dict(p, counter=last.get(n)) for n, p in sets.panels(st)])
    dead = model.world(plan)[i]["dead"] if plan.get("model") else set()
    out = {}
    for name, a in (prev.get("actors") or {}).items():
        s = _fold(a, beats, name, end, _start(plan, prev, name, None))
        ghost = s.look[1] == "ghost"
        c = {k: v for k, v in a.items() if k not in ("anim", "at")}
        if not _by_contact(plan, prev, beats, name, end):
            c["at"] = [round(s.x, 4), round(s.y, 4)]
        c.update(flip=s.flip, badge=s.badge, ghost=ghost, marks=s.marks[0],
                 hidden=not s.shown or (name in dead and not ghost))
        if "parts" in a or any(b.get("actor") == name and "parts" in b for b in beats):
            c["parts"] = model.shown_parts(a, beats, name)
        out[name] = c
    for name, a in own.items():
        out[name] = dict(out.get(name, {}), **a)
    sc["actors"] = out


# ---------------------------------------------------------------- behaviors: beats that make beats

def _behave(plan, sc, dur):
    """Beats with wander:, hunt:, or divide: of one scene become plain beats (move_to, verb, anim, show, flip,
    badge, marks), so check sees what plays: the targets of a hunt and who is destroyed. Each made beat has
    _from: the beat that made it. Returns problems of these beats."""
    src = list(sc.get("beats") or [])
    if not any(k in x for x in src for k in BEHAVIORS):
        return []
    actors, sid, out = sc.get("actors") or {}, sc.get("id"), []
    plain = [x for x in src if not any(k in x for k in BEHAVIORS)]
    made = []
    todo = sorted((x for x in src if any(k in x for k in BEHAVIORS)),
                  key=lambda x: ("wander" in x, float(x.get("t", 0))))      # wander last: it stops at the others
    for x in todo:
        me, t0 = x.get("actor"), float(x.get("t", 0))
        kind = next(k for k in BEHAVIORS if k in x)
        where = f"{sid}: {kind} at {t0:.2f} s" + (f" (word {x['word']!r})" if "word" in x else "")
        tag = {"_from": where.split(": ", 1)[1]}
        step = x.get("dur", WANDER_STEP if kind == "wander" else HUNT_MOVE)
        if sc.get("type") != "action" or me not in actors:
            what = "a part, not an actor" if me in model.parts(plan) else "not an actor of the scene"
            out.append(f"{where}: {kind}: is for an actor of an action scene ({me!r} is {what})")
            continue
        if sum(k in x for k in BEHAVIORS) > 1:
            out.append(f"{where}: one of {', '.join(BEHAVIORS)} in a beat")
            continue
        if not (isinstance(step, (int, float)) and not isinstance(step, bool) and step >= 0.2):
            out.append(f"{where}: dur: is a number of seconds, 0.2 or more")
            continue
        now = plain + made
        if kind == "hunt":
            tgs = x["hunt"] if isinstance(x["hunt"], list) else [x["hunt"]]
            bad = [g for g in tgs if not isinstance(g, str) or g not in actors or g == me]
            bad += [g for i, g in enumerate(tgs) if g in tgs[:i] and g not in bad]
            if bad or not tgs or not x.get("verb"):
                out.append(f"{where}: hunt: names other actors of the scene, each once, in order, and verb: what it "
                           f"does to each (then: what each does after it)" + (f"; not right: {bad}" if bad else ""))
                continue
            far = [g for g in tgs if actors[g].get("in") != actors[me].get("in")]
            if far:
                out.append(f"{where}: hunt: the targets are in the hunter's zone (in: {actors[me].get('in')}); "
                           f"not: {', '.join(far)}")
                continue
            t, mine = t0, []
            for g in tgs:
                seen = _with_verbs(now + mine)          # with the shows and hides of verbs
                if not _fold(actors[g], seen, g, t + step, _start(plan, sc, g, None)).shown:
                    out.append(f"{where}: hunt: {g} is hidden or gone when the hunter comes ({t + step:.2f} s)")
                mine.append({"t": round(t, 3), "actor": me, "move_to": g, "dur": step, **tag})
                hit = {"hit": x["hit"]} if "hit" in x else {}
                mine.append({"t": round(t + step, 3), "actor": me, "verb": x["verb"], "target": g, **hit, **tag})
                t += step + _verb_s(x["verb"])
                if x.get("then"):
                    mine.append({"t": round(t, 3), "actor": g, "verb": x["then"], **tag})
                    if x.get("ghost") is True:
                        mine.append({"t": round(t, 3), "actor": g, "ghost": True, **tag})
            end = t + (_verb_s(x["then"]) if x.get("then") else 0)
            if end > dur + 1e-6:
                out.append(f"{where}: the hunt ends at {end:.2f} s, after the scene ({dur:.2f} s): start it on an "
                           f"earlier word, give fewer targets or a shorter dur:, or give the scene dur:")
            busy = [y for y in src if y.get("actor") == me and t0 < float(y.get("t", 0)) < t]
            if busy:
                out.append(f"{where}: {me} has a beat at {float(busy[0].get('t', 0)):.2f} s while the hunt runs "
                           f"(until {t:.2f} s): move it after the hunt")
            made += mine
        elif kind == "wander":
            if x["wander"] is not True:
                out.append(f"{where}: wander: {x['wander']!r}; write wander: true (the actor walks in its zone "
                           f"until its next beat), or leave it out")
                continue
            stop = [float(y.get("t", 0)) for y in plain + made if float(y.get("t", 0)) > t0 and
                    (y.get("actor") == me or me in (y.get("target"), y.get("move_to")))]
            mine = _wander(plan, sc, me, now, t0, min(stop + [dur]), float(step))
            made += [dict(y, **tag) for y in mine]
        else:
            d = x["divide"]
            if not isinstance(d, str) or d not in actors or d == me or not actors[d].get("hidden") \
                    or actors[d].get("in") != actors[me].get("in"):
                out.append(f"{where}: divide: names the daughter: another actor of the scene with hidden: true, "
                           f"in the same zone")
                continue
            if x.get("apart") is None and _by_contact(plan, sc, now, me, t0):
                out.append(f"{where}: divide: {me} came to its place by move_to: <actor>; give it a place first "
                           f"(move_to: [x, y]) or give apart:")
                continue
            mine = [dict(y, **tag) for y in _divide(plan, sc, me, d, now, t0, x.get("apart"))]
            made += mine
            end = max(float(y["t"]) + float(y.get("dur", 0)) for y in mine)
            if end > dur + 1e-6:
                out.append(f"{where}: the division ends at {end:.2f} s, after the scene ({dur:.2f} s): start it "
                           f"on an earlier word, or give the scene dur:")
    sc["beats"] = plain + made
    return out


def _wander(plan, sc, me, beats, t0, t1, step):
    """Walks from point to point inside the actor's zone (fractions) from t0 to t1; faces where it goes.
    After a move_to: <actor>, it faces from the place before that move."""
    import random, zlib
    a = sc["actors"][me]
    rnd = random.Random(zlib.crc32(f"{plan.get('seed', 0)}/{sc.get('id')}/{me}/{t0}".encode()))
    s = _fold(a, beats, me, t0, _start(plan, sc, me, None))
    x, y, flip = s.x, s.y, s.flip
    out, t = [], t0
    while t1 - t > 0.4:
        d = min(step, t1 - t - 0.1)
        nx = rnd.uniform(0.15, 0.85)
        ny = y if a.get("in") == "border" else rnd.uniform(0.25, 0.75)
        if (nx < x) != flip:
            flip = nx < x
            out.append({"t": round(t, 3), "actor": me, "flip": flip})
        out.append({"t": round(t, 3), "actor": me, "move_to": [round(nx, 3), round(ny, 3)], "dur": round(d, 3)})
        x, y, t = nx, ny, t + d + 0.1
    return out


def _divide(plan, sc, me, d, beats, t0, apart):
    """The cell plays its divide animation (if its sprite has one); then the daughter appears at its place with
    its marks and badge, and the two move apart: edge to edge (the cell steps aside, the daughter moves to it),
    or apart: a fraction of the zone between them."""
    a = sc["actors"][me]
    start = _start(plan, sc, me, None)
    anim = _fold(a, beats, me, t0, start).anim
    out, t = [], t0
    if "divide" in S.meta().get(a.get("sprite"), {}).get("anims", {}):
        t = t0 + S.duration(a["sprite"], "divide")
        out += [{"t": round(t0, 3), "actor": me, "anim": "divide"}, {"t": round(t, 3), "actor": me, "anim": anim}]
    s = _fold(a, beats, me, t, start)
    x, y = s.x, s.y
    p = lambda v: round(min(0.95, max(0.05, v)), 4)
    out += [{"t": round(t, 3), "actor": d, "move_to": [p(x), p(y)], "dur": 0.001},
            {"t": round(t, 3), "actor": d, "show": True, "badge": s.badge, "marks": s.marks[0]}]
    if apart is None:
        return out + [{"t": round(t + 0.01, 3), "actor": me, "move_to": [p(x - APART / 2), p(y)], "dur": 0.6},
                      {"t": round(t + 0.01, 3), "actor": d, "move_to": me, "dur": 0.6}]
    h = float(apart) / 2
    return out + [{"t": round(t + 0.01, 3), "actor": me, "move_to": [p(x - h), p(y)], "dur": 0.6},
                  {"t": round(t + 0.01, 3), "actor": d, "move_to": [p(x + h), p(y)], "dur": 0.6}]
