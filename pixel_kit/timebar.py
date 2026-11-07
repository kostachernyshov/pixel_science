# The timeline: a strip at the bottom of the stage with a scale of time, a "now" cursor, and marks. It is a layer
# over any set, not a scene: it does not dissolve between scenes. The plan gives the scale once; beats of the scenes
# move the cursor and add marks on their words.
#
#   timeline: {from: 1982, to: 2014, unit: year, now: 2014}   # unit in the singular: year, day, million year...
#   beats:                                                    # now: where the cursor starts (default from:)
#     - {word: "transplant", timeline: 1998}            # the cursor goes there; a long jump shows << or >>
#     - {word: "melanoma", mark: 1982, label: SURGERY}  # a mark stays on the strip (color: a plan color name)
#
# A long jump (more than a quarter of the scale) leaves a thick part of the line between the two places with the
# span ("16 YEARS") until the cursor moves again. Title and summary scenes, and a scene with timeline: false, hide
# the strip; it keeps its place at the bottom of the stage in every scene, so the composition does not jump.
# In the banner the strip has no room for labels: the line, the marks, the cursor and its value at the right end.

from PIL import ImageDraw
from .palette import *
from .font import text, text_w, LINE

MOVE = 0.8               # s: the cursor moves to a new place
HEIGHT = 2 * LINE + 8    # px of the stage that the strip takes (one label row, the line, the scale labels)
HEIGHT_BANNER = LINE + 6
PAD = 10


def height(L):
    return HEIGHT_BANNER if L["banner"] else HEIGHT


def scale(plan):
    tl = plan.get("timeline") or {}
    return float(tl.get("from", 0)), float(tl.get("to", 1)), str(tl.get("unit", "year"))


def events(plan, times):
    """[(global time, kind, beat)] of the beats with timeline: or mark:, in time order."""
    out = []
    for sc, (a, _) in zip(plan["scenes"], times):
        for b in sc.get("beats") or []:
            for k in ("timeline", "mark"):
                if k in b:
                    out.append((a + float(b.get("t", 0)), k, b))
    return sorted(out, key=lambda e: e[0])


def _num(v):
    return str(int(v)) if float(v) == int(v) else f"{v:g}"


def _dec(plan):
    """Decimals of the scale: the cursor value is shown with as many as from: and to: have."""
    tl = plan.get("timeline") or {}
    return max(len(s.split(".")[1]) if "." in s else 0 for s in (_num(tl.get(k, 0)) for k in ("from", "to")))


def span(d, unit, dec=0):
    n, u = _num(round(abs(d), dec)), unit.upper()
    return f"{n} {u}{'' if abs(d) == 1 or u.endswith('S') else 'S'}"


def state(plan, evs, T):
    """(cursor value, (from, to) of the last long jump or None, its direction, moving, marks [(value, label, color)]).
    A move that starts while the cursor still moves starts from where the cursor is at that time."""
    lo, hi, _ = scale(plan)
    now = float((plan.get("timeline") or {}).get("now", lo))
    past = [e for e in evs if e[0] <= T]
    marks = [(float(b["mark"]), str(b.get("label") or ""), b.get("color")) for _, k, b in past if k == "mark"]
    moves = [(t, float(b["timeline"])) for t, k, b in past if k == "timeline"]
    jump, way, moving = None, 0, False
    for i, (t, new) in enumerate(moves):
        end = moves[i + 1][0] if i + 1 < len(moves) else T
        u = min(1.0, (end - t) / MOVE)
        start, moving = now, u < 1.0
        now = start + (new - start) * (u * u * (3 - 2 * u))
        far = abs(new - start) > (hi - lo) / 4
        jump, way = ((start, now), 1 if new > start else -1) if far else (None, 0)
    return now, jump, way, moving, marks


def _geometry(plan, L):
    """(x of a value, y of the line, x of the right end of the line)."""
    x0, y0, x1, y1 = L["timebar"]
    lo, hi, _ = scale(plan)
    dec = _dec(plan)
    right = x1 - PAD - (max(text_w(_num(round(v, dec))) for v in (lo, hi)) + 6 if L["banner"] else 0)
    X = lambda v: int(x0 + PAD + (min(max(v, lo), hi) - lo) / ((hi - lo) or 1) * (right - x0 - PAD))
    ly = y1 - (LINE + 2 if not L["banner"] else LINE // 2 + 2)
    return X, ly, right


def _labels(marks, X, L):
    """[(x of the label, its width, overlaps the one before)] of the mark labels, left to right:
    each one is centred on its mark and pushed right past the label before."""
    x0, _, x1, _ = L["timebar"]
    out, end = [], x0 + 2
    for v, label, _ in sorted(marks, key=lambda m: m[0]):
        w = text_w(label) if label else 0
        a = max(X(v) - w // 2, end) if w else X(v)
        if w and a + w > x1 - 2:
            a = x1 - 2 - w
        out.append((a, w, bool(w) and a < end))
        if w:
            end = a + w + 4
    return out


def draw(img, plan, L, evs, T, color=None):
    """Draws the strip into its place at the bottom of the stage (L["timebar"])."""
    x0, y0, x1, y1 = L["timebar"]
    lo, hi, unit = scale(plan)
    X, ly, right = _geometry(plan, L)
    d = ImageDraw.Draw(img)
    banner = L["banner"]
    d.line([x0 + PAD, ly, right, ly], fill=C(INK))
    for v in (lo, hi):
        d.line([X(v), ly - 3, X(v), ly + 3], fill=C(INK))
    now, jump, way, moving, marks = state(plan, evs, T)
    cx = X(now)
    cur = _num(round(now, _dec(plan)))
    if banner:
        cl = x1 - PAD - text_w(cur)
    else:
        cl = min(max(cx - text_w(cur) // 2, x0 + 2), x1 - 2 - text_w(cur))      # where the cursor's value goes
    taken = [(cl - 3, cl + text_w(cur) + 3)]                                  # boxes on the row under the line
    if jump:                                                # the span of the long jump: a thick part of the line
        a, b = sorted((X(jump[0]), X(jump[1])))
        d.rectangle([a, ly - 1, b, ly + 1], fill=C(NAVY))
        s = span(jump[1] - jump[0], unit, _dec(plan)) if not moving else ("<<" if way < 0 else ">>")
        m, w = (a + b) // 2, text_w(s)
        if b - a > w + 4 and not banner and not any(p < m + w // 2 + 1 and m - w // 2 - 1 < q for p, q in taken):
            text(img, m, ly + 3, s, NAVY, align="c")
            taken.append((m - w // 2 - 3, m + w // 2 + 3))
    for (v, label, col), (lx, _, _) in zip(sorted(marks, key=lambda m: m[0]), _labels(marks, X, L)):
        c = color(col)[0] if (col and color) else ORANGE
        x = X(v)
        d.polygon([(x, ly - 4), (x + 3, ly - 1), (x, ly + 2), (x - 3, ly - 1)], fill=C(c))
        if label and not banner:
            text(img, lx, ly - 4 - LINE, label, c)
    if not banner:
        for v, end in ((lo, False), (hi, True)):                # the ends of the scale, where no label is
            s = _num(v)
            a = X(v) - text_w(s) if end else X(v)
            if not any(p < a + text_w(s) and a < q for p, q in taken):
                text(img, a, ly + 3, s, DGREY)
    d.polygon([(cx - 4, ly + 5), (cx + 4, ly + 5), (cx, ly)], fill=C(NAVY))     # the cursor and its value
    text(img, cl, (ly - LINE // 2) if banner else ly + 3, cur, NAVY)


def fit(plan, L):
    """Problems: mark labels that do not fit side by side on the strip in this format."""
    if L["banner"] or not plan.get("timeline"):
        return []
    marks = [(float(b["mark"]), str(b.get("label") or ""), None)
             for sc in plan["scenes"] for b in sc.get("beats") or [] if isinstance(b.get("mark"), (int, float))]
    X, _, _ = _geometry(plan, L)
    over = [m[1] for m, (_, _, o) in zip(sorted(marks, key=lambda m: m[0]), _labels(marks, X, L)) if o]
    return [f"timeline: mark labels do not fit side by side ({', '.join(over)} overlap the label before); "
            f"make them shorter or put the marks further apart"] if over else []


def _number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def check(plan, colors=()):
    """Problems of the timeline and of its beats. colors: the color names a mark may have."""
    out, tl = [], plan.get("timeline")
    for sc in plan["scenes"]:
        for b in sc.get("beats") or []:
            if isinstance(b.get("mark"), list):
                return [f"{sc.get('id')}: beat at {b.get('t')} s: mark: is a point on the timeline (a number); "
                        f"marks on an actor's body are marks: (a list)"]
    used = any("timeline" in b or "mark" in b for sc in plan["scenes"] for b in sc.get("beats") or [])
    if tl is None:
        return ["a beat moves the timeline or adds a mark, but the plan has no timeline: {from, to, unit}"] if used else []
    if tl is False:
        return ["timeline: false goes on a scene (it hides the strip there); the plan gives timeline: {from, to, unit}"]
    if not isinstance(tl, dict) or not all(_number(tl.get(k)) for k in ("from", "to")):
        return ["timeline: needs from: and to: as numbers (and unit:, default year)"]
    lo, hi, _ = scale(plan)
    if hi <= lo:
        return ["timeline: to: must be after from:"]
    if "now" in tl and not (_number(tl["now"]) and lo <= tl["now"] <= hi):
        out.append(f"timeline: now: {tl['now']!r} is not on the timeline ({_num(lo)} to {_num(hi)})")
    for sc in plan["scenes"]:
        hidden = sc.get("type") in ("title", "summary") or sc.get("timeline") is False
        for b in sc.get("beats") or []:
            for k in ("timeline", "mark"):
                if k not in b:
                    continue
                if not (_number(b[k]) and lo <= b[k] <= hi):
                    out.append(f"{sc.get('id')}: beat at {b.get('t')} s: {k}: {b[k]!r} is not on the timeline ({_num(lo)} to {_num(hi)})")
                if hidden:
                    out.append(f"warning: {sc.get('id')}: beat at {b.get('t')} s: {k}: the strip is hidden in this scene")
            if "mark" in b and b.get("color") and b["color"] not in colors:
                out.append(f"{sc.get('id')}: beat at {b.get('t')} s: mark color {b['color']!r} is unknown; use one of {', '.join(colors)}")
    return out
