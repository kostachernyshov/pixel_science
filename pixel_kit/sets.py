# Sets: a composition that the viewer learns once and that stays through several scenes (GLOSSARY: Set).
# An action scene names it with `set:`; an actor stands in one of its zones with `in:`, and its `at:` is then
# a fraction of that zone, not of the stage. A scene with `continue: true` keeps the set of the scene before.
#
#   set: {type: panels, panels: [{title: CONTROL, counter: "0 OF 15"}, {title: TEST}]}
#        2 to 4 frames, zones A, B, C, D. Side by side; stacked in a tall frame; 2 x 2 for 4 in a square.
#        In the banner, frames and counters only (no titles).
#        A beat {word: ..., panel: B, counter: "7 OF 15"} changes a counter. An actor with in: all stands
#        in every panel at the same place (one actor, drawn in each; its verbs play in each).
#   set: {type: border, at: 0.45, top: OUTSIDE, bottom: INSIDE, line: membrane}
#        a line across the stage at a fraction of its height, zones top and bottom, and the zone border
#        (an actor with in: border stands on the line, half on each side). The core knows no topic:
#        the look of the line comes from a pack (pack.yaml, borders:), here a membrane, elsewhere water or ground.

from PIL import ImageDraw
from .palette import *
from .font import text, text_w, LINE
from . import packs, sprites as S

KINDS = ("panels", "border")
NAMES = "ABCD"
TITLE_H = LINE + 4            # the strip with the title and the counter at the top of a panel


def panels(st):
    """[(name, {title, counter})] of a panels set."""
    return [(p.get("name", NAMES[i]), p) for i, p in enumerate(st.get("panels") or [])]


def _grid(n, tall, banner):
    if tall:
        return n, 1
    if n == 4 and not banner:
        return 2, 2
    return 1, n


def frames(st, L):
    """{panel: frame box (x0, y0, x1, y1)} of a panels set in the current format."""
    x0, y0, x1, y1 = L["stage"]
    ps = panels(st)
    rows, cols = _grid(len(ps), L["tall"], L["banner"])
    gap = 3
    w, h = (x1 - x0 - gap * (cols + 1)) / max(1, cols), (y1 - y0 - gap * (rows + 1)) / max(1, rows)
    out = {}
    for i, (name, _) in enumerate(ps):
        r, c = divmod(i, cols)
        bx, by = x0 + gap + c * (w + gap), y0 + gap + r * (h + gap)
        out[name] = (int(bx), int(by), int(bx + w), int(by + h))
    return out


def line_y(st, L):
    x0, y0, x1, y1 = L["stage"]
    return int(y0 + float(st.get("at", 0.5)) * (y1 - y0))


def zones(st, L):
    """{zone: box (x0, y0, x1, y1)} in the current format: where the actors of the set stand."""
    if not st:
        return {}
    if st.get("type") == "panels":
        top = 0 if L["banner"] else TITLE_H
        return {n: (a + 3, b + top + 2, c - 3, d - 3) for n, (a, b, c, d) in frames(st, L).items()}
    if st.get("type") == "border":
        x0, y0, x1, y1 = L["stage"]
        ly = line_y(st, L)
        return {"top": (x0, y0, x1, ly), "bottom": (x0, ly, x1, y1), "border": (x0, ly, x1, ly)}
    return {}


def style(name):
    """The look of a border line from the packs (pack.yaml, borders:), later packs win:
    {bands: [[r, g, b], ...] from the top, beads: {color, step}} (beads: round heads on the outer bands)."""
    found = None
    for p in S.in_use():
        found = (packs.get(p).meta.get("borders") or {}).get(name, found)
    return found


def styles():
    out = set()
    for p in S.in_use():
        out |= set(packs.get(p).meta.get("borders") or {})
    return sorted(out)


def counters(st, beats, t):
    """{panel: counter text} at time t: the set's start values, changed by beats with counter:."""
    out = {n: p.get("counter") for n, p in panels(st)}
    for b in sorted((b for b in beats if "counter" in b), key=lambda b: float(b.get("t", 0))):
        if float(b.get("t", 0)) <= t:
            out[b.get("panel")] = b["counter"]
    return out


def draw(img, st, L, beats, t):
    """Draws the set under the actors."""
    d = ImageDraw.Draw(img)
    if st.get("type") == "panels":
        cs = counters(st, beats, t)
        for (name, p), (a, b, c, e) in zip(panels(st), frames(st, L).values()):
            d.rectangle([a, b, c, e], outline=C(INK))          # no fill: the background of the scene shows
            d.rectangle([a + 2, b + 2, c - 2, e - 2], outline=C(LGREY))
            if L["banner"]:                          # no room for a title strip: the counter only
                if cs.get(name):
                    s = str(cs[name])
                    text(img, c - 5 - text_w(s), b + 4, s, INK)
                continue
            title = str(p.get("title") or "")
            if title:
                text(img, a + 5, b + 4, title, NAVY)
            if cs.get(name):
                s = str(cs[name])
                text(img, c - 5 - text_w(s), b + 4, s, INK)
            d.line([a + 3, b + TITLE_H, c - 3, b + TITLE_H], fill=C(LGREY))
    elif st.get("type") == "border":
        x0, y0, x1, y1 = L["stage"]
        ly = line_y(st, L)
        sty = style(st.get("line")) or {}
        bands = [tuple(c) for c in sty.get("bands") or [C(DGREY)] * 2]
        top = ly - len(bands) // 2
        for i, col in enumerate(bands):
            d.line([x0, top + i, x1, top + i], fill=col)
        bead = sty.get("beads")
        if bead:
            step, col = int(bead.get("step", 6)), tuple(bead.get("color", bands[0]))
            for x in range(x0 + step // 2, x1, step):
                for y in (top - 1, top + len(bands)):
                    d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=col)
        if not L["banner"]:
            for key, y in (("top", ly - len(bands) // 2 - 4 - LINE), ("bottom", ly + len(bands) // 2 + 5)):
                if st.get(key):
                    text(img, x1 - 6 - text_w(str(st[key])), y, str(st[key]), DGREY)


def fit(st, L, beats):
    """Problems: a title and a counter that do not fit their panel in this format."""
    out = []
    if L["banner"]:
        return out
    ws = {}
    for b in beats:
        if "counter" in b:
            ws[b.get("panel")] = max(ws.get(b.get("panel"), 0), text_w(str(b["counter"])))
    for (name, p), (a, _, c, _) in zip(panels(st), frames(st, L).values()):
        w = text_w(str(p.get("title") or "")) + max(ws.get(name, 0), text_w(str(p.get("counter") or ""))) + 16
        if w > c - a:
            out.append(f"panel {name}: the title and the counter do not fit ({w} px, the panel has {c - a}); "
                       f"make them shorter")
    return out


def check(st, sid):
    """Problems of a scene's set."""
    out = []
    k = st.get("type")
    if k not in KINDS:
        return [f"{sid}: set type {k!r} is unknown; use {', '.join(KINDS)}"]
    if k == "panels":
        names = [n for n, _ in panels(st)]
        if not 2 <= len(names) <= 4:
            out.append(f"{sid}: a panels set has 2 to 4 panels")
        if len(set(names)) < len(names):
            out.append(f"{sid}: two panels have the same name")
    if k == "border":
        if not isinstance(st.get("at", 0.5), (int, float)):
            out.append(f"{sid}: border at: is a number, a fraction of the stage height")
        elif not 0.2 <= float(st.get("at", 0.5)) <= 0.8:
            out.append(f"{sid}: border at: keep it between 0.2 and 0.8 of the stage, so both zones have room")
        if st.get("line") and not style(st["line"]):
            out.append(f"{sid}: border line {st['line']!r} is in no pack; packs have: {', '.join(styles()) or 'none'}")
    return out
