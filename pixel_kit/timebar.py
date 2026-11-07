# The timeline: a strip at the bottom of the stage with a scale of time, a "now" cursor, and marks. It is a layer
# over any set, not a scene: it does not dissolve between scenes. The plan gives the scale once; beats of the scenes
# move the cursor and add marks on their words.
#
#   timeline: {from: 1982, to: 2014, unit: year}       # any unit: year, day, hour, million year...
#   beats:
#     - {word: "transplant", timeline: 1998}            # the cursor goes there; a long jump rewinds: << or >>
#     - {word: "melanoma", mark: 1982, label: SURGERY}  # a mark stays on the strip
#
# A long jump (more than a quarter of the scale) leaves a bracket between the two places with the span
# ("16 YEARS") until the cursor moves again. Title and summary scenes, and a scene with timeline: false, hide it.

from PIL import ImageDraw
from .palette import *
from .font import text, text_w, LINE

MOVE = 0.8               # s: the cursor moves to a new place
HEIGHT = 2 * LINE + 8    # px of the stage that the strip takes (one label row, the line, the scale labels)
HEIGHT_BANNER = LINE + 6


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


def span(d, unit):
    n = _num(abs(d))
    return f"{n} {unit.upper()}{'' if abs(d) == 1 else 'S'}"


def state(plan, evs, T):
    """(cursor value, (from, to) of the last long jump or None, its direction, moving, marks [(value, label, color)])."""
    lo, hi, _ = scale(plan)
    now = float((plan.get("timeline") or {}).get("now", lo))
    jump, way, moving, marks = None, 0, False, []
    for t, k, b in evs:
        if t > T:
            break
        if k == "mark":
            marks.append((float(b["mark"]), str(b.get("label") or ""), b.get("color")))
            continue
        new = float(b["timeline"])
        u = min(1.0, (T - t) / MOVE)
        moving = u < 1.0
        far = abs(new - now) > (hi - lo) / 4
        jump, way = ((now, new), 1 if new > now else -1) if far else (None, 0)
        now = now + (new - now) * (u * u * (3 - 2 * u)) if moving else new
        if moving:
            jump = (jump[0], now) if jump else None
    return now, jump, way, moving, marks


def draw(img, plan, L, evs, T, color=None):
    """Draws the strip into its place at the bottom of the stage (L["timebar"])."""
    x0, y0, x1, y1 = L["timebar"]
    lo, hi, unit = scale(plan)
    d = ImageDraw.Draw(img)
    pad = 10
    X = lambda v: int(x0 + pad + (min(max(v, lo), hi) - lo) / ((hi - lo) or 1) * (x1 - x0 - 2 * pad))
    ly = y1 - (LINE + 2 if not L["banner"] else LINE // 2 + 2)
    d.line([x0 + pad, ly, x1 - pad, ly], fill=C(INK))
    for v in (lo, hi):
        d.line([X(v), ly - 3, X(v), ly + 3], fill=C(INK))
    now, jump, way, moving, marks = state(plan, evs, T)
    cx = X(now)
    cur = _num(round(now))
    cl = min(max(cx - text_w(cur) // 2, x0 + 2), x1 - 2 - text_w(cur))      # where the cursor's value goes
    if not L["banner"]:
        for v, right in ((lo, False), (hi, True)):              # the ends of the scale, unless the value covers one
            s = _num(v)
            a = X(v) - text_w(s) if right else X(v)
            if a + text_w(s) + 3 < cl or a > cl + text_w(cur) + 3:
                text(img, a, ly + 3, s, DGREY)
    for v, label, col in marks:
        c = color(col)[0] if (col and color) else ORANGE
        x = X(v)
        d.polygon([(x, ly - 4), (x + 3, ly - 1), (x, ly + 2), (x - 3, ly - 1)], fill=C(c))
        if label and not L["banner"]:
            text(img, min(max(x - text_w(label) // 2, x0 + 2), x1 - 2 - text_w(label)), ly - 4 - LINE, label, c)
    if jump:                                                # the span of the long jump: a thick part of the line
        a, b = sorted((X(jump[0]), X(jump[1])))
        d.rectangle([a, ly - 1, b, ly + 1], fill=C(NAVY))
        s = span(jump[1] - jump[0], unit) if not moving else ("<<" if way < 0 else ">>")
        m = (a + b) // 2
        if b - a > text_w(s) + 4 and not L["banner"] and not (cl - 4 < m + text_w(s) // 2 and m - text_w(s) // 2 < cl + text_w(cur) + 4):
            text(img, m, ly + 3, s, NAVY, align="c")
    d.polygon([(cx - 4, ly + 5), (cx + 4, ly + 5), (cx, ly)], fill=C(NAVY))     # the cursor and its value
    if not L["banner"]:
        text(img, cl, ly + 3, cur, NAVY)


def check(plan):
    """Problems of the timeline and of its beats."""
    out, tl = [], plan.get("timeline")
    used = any("timeline" in b or "mark" in b for sc in plan["scenes"] for b in sc.get("beats") or [])
    if tl is None:
        return ["a beat moves the timeline or adds a mark, but the plan has no timeline: {from, to, unit}"] if used else []
    if not isinstance(tl, dict) or not all(isinstance(tl.get(k), (int, float)) for k in ("from", "to")):
        return ["timeline: needs from: and to: as numbers (and unit:, default year)"]
    lo, hi, _ = scale(plan)
    if hi <= lo:
        out.append("timeline: to: is after from:")
    for sc in plan["scenes"]:
        for b in sc.get("beats") or []:
            for k in ("timeline", "mark"):
                if k in b and not (isinstance(b[k], (int, float)) and lo <= b[k] <= hi):
                    out.append(f"{sc.get('id')}: beat at {b.get('t')} s: {k}: {b[k]!r} is not on the timeline ({_num(lo)} to {_num(hi)})")
    return out
