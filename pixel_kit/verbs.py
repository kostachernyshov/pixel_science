# Verbs: actions that a scene beat names. A verb is data (YAML), not code: a list of primitives
# (pixel_kit/fx.py) with colors by role, optional hit mechanics, and show or hide of an actor.
# Core verbs are in pixel_kit/verbs.yaml; each pack can add packs/<name>/verbs.yaml (a pack replaces
# a core verb of the same name; a later pack replaces an earlier one).
#
#   from pixel_kit import verbs
#   verbs.use(["biology"])               the plan's packs
#   verbs.get("secrete")                 the verb (dict), or KeyError with the next step
#   verbs.play(cv, "secrete", t, geo, seed)
#   verbs.check_beat(beat, actors)       problems of one beat (list of str)

import math, os, time
import yaml
from . import packs, palette, fx

CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verbs.yaml")
MAX_MS = 5          # a verb draws a 480x270 frame in this many ms or less (pixsci check warns)
ADD = "add it to packs/<pack>/verbs.yaml (see .agents/skills/add-verb/SKILL.md)"
_use = None
_cache = None


def use(names=None):
    global _use, _cache
    _use = list(names) if names else None
    _cache = None


def _load():
    """(verbs, colors): {name: verb with "pack"}, {role: [RGB, ...]}."""
    global _cache
    if _cache is None:
        verbs, colors = {}, {}
        files = [("core", CORE)]
        for name in _use or sorted(packs.find()):
            p = os.path.join(packs.get(name).dir, "verbs.yaml")
            if os.path.exists(p):
                files.append((name, p))
        for pack, path in files:
            d = yaml.safe_load(open(path, encoding="utf-8")) or {}
            for role, names in (d.get("colors") or {}).items():
                colors[role] = [palette.P[palette.NAMES.index(n)] for n in names]
            for name, v in (d.get("verbs") or {}).items():
                verbs[name] = dict(v, pack=pack)
        _cache = verbs, colors
    return _cache


def all():
    return _load()[0]


def get(name):
    v = all().get(name)
    if v is None:
        raise KeyError(f"verb {name!r} is not in core or packs [{', '.join(_use or packs.find())}]: {ADD}")
    return v


def duration(name):
    return max(float(s.get("t", 0)) + float(s.get("dur", 1.0)) for s in get(name)["steps"])


def hit(name, beat):
    """(contact time from the beat start, params, who strikes: "actor" or "target"), or None."""
    v = get(name)
    h = beat.get("hit", v.get("hit"))
    if h in (None, False):
        return None
    base = v.get("hit") or {}
    if isinstance(h, str):
        h = dict(base, preset=h)
    p = fx.hit_params({k: x for k, x in h.items() if k not in ("at", "by")})
    return float(h.get("at", base.get("at", 0))), p, h.get("by", base.get("by", "actor"))


# ---------------------------------------------------------------- drawing

def _edge(p, r, q, k=0.8):
    """A point on the edge of the actor at p (radius r) toward q."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    d = math.hypot(dx, dy) or 1.0
    return p[0] + dx / d * r * k, p[1] + dy / d * r * k


def geometry(step, geo):
    """geo: {"actor": (x, y, r), "target": (x, y, r) or None} -> g for a primitive."""
    if "from" in step:
        a, b = geo[step["from"]], geo[step["to"]]
        return {"a": _edge(a, a[2], b), "b": _edge(b, b[2], a, 0.6), "r": a[2]}
    who = step.get("at", "actor")
    other = "target" if who == "actor" else "actor"
    p, q = geo[who], geo.get(other)
    a = _edge(p, p[2], q) if step.get("edge") and q else p[:2]
    return {"a": a, "b": q[:2] if q else None, "r": p[2]}


def play(cv, name, t, geo, seed=0):
    """Draw the verb at time t (s from the beat)."""
    v = get(name)
    colors = _load()[1]
    for i, s in enumerate(v["steps"]):
        o = {k: x for k, x in s.items() if k not in ("prim", "at", "from", "to", "color", "t", "edge")}
        o["seed"] = seed * 31 + i
        if "color" in s and s["color"] not in colors:
            raise KeyError(f"verb {name}: unknown color role {s['color']!r}; add it under colors: in the verbs.yaml")
        fx.PRIMS[s["prim"]](cv, t - float(s.get("t", 0)), geometry(s, geo), colors.get(s.get("color"), colors["spark"]), o)


# ---------------------------------------------------------------- checks

def check_verb(name):
    """Problems of the verb definition itself."""
    out = []
    v = get(name)
    colors = _load()[1]
    for s in v.get("steps") or []:
        if s.get("prim") not in fx.PRIMS:
            out.append(f"verb {name}: unknown primitive {s.get('prim')!r}; primitives: {', '.join(fx.PRIMS)}")
        if s.get("color") and s["color"] not in colors:
            out.append(f"verb {name}: unknown color role {s['color']!r}")
        if ("target" in (s.get("at"), s.get("to"), s.get("from"))) and not v.get("target"):
            out.append(f"verb {name}: a step uses the target, so the verb needs 'target: true'")
    if not v.get("steps"):
        out.append(f"verb {name}: no steps")
    return out


def check_beat(beat, actors):
    """Problems of a beat with a verb (or an old fx: field)."""
    if "fx" in beat:
        return [f"beat at {beat.get('t')} s: 'fx: {beat['fx']}' is replaced by 'verb:' (pixsci verbs lists them)"]
    name = beat.get("verb")
    if not name:
        return []
    try:
        v = get(name)
    except KeyError as e:
        return [str(e).strip('"')]
    out = check_verb(name)
    if v.get("target") and beat.get("target") not in actors:
        out.append(f"beat at {beat.get('t')} s: verb {name} needs 'target:' (an actor of the scene)")
    return out


def bench(name, w=480, h=270, frames=12):
    """Average ms per frame to draw the verb on an empty canvas of w x h."""
    from PIL import Image
    img = Image.new("RGB", (w, h), (251, 250, 247))
    geo = {"actor": (w * 0.3, h * 0.5, 18), "target": (w * 0.7, h * 0.5, 18)}
    d = duration(name)
    t0 = time.perf_counter()
    for i in range(frames):
        cv = fx.Canvas(img, img)
        play(cv, name, d * i / frames, geo)
        cv.image()
    return (time.perf_counter() - t0) / frames * 1000
