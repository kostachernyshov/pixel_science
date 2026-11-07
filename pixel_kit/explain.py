# explainer.yaml -> Timeline, for each video format. The agent writes the plan; this module draws it.
# The plan format is in skills/animate/PLAN.md. Paths in the plan are relative to the plan file.
#
#   from pixel_kit import explain, frame
#   plan = explain.load("my-video/explainer.yaml")
#   problems = explain.check(plan)        # rules: captions, sources, sprites, timing, text fits
#   frame.use("vertical")
#   tl, marks = explain.timeline(plan)    # marks: key times for the storyboard
#
# Scene types: title, cast, action, fact, flow, summary, custom.
# Layout is relative to the frame, so one plan renders in every format of frame.FORMATS.

import importlib.util, math, os, re
from PIL import ImageDraw
from .palette import *
from .font import text, text_w, title_text, TITLE_GLYPHS, LINE
from .timing import clamp, seg, ease, lerp
from . import sprites as S, fx, ui, bg, frame, verbs, model, sets, timebar, words as WD
from .scene import Timeline

WORDS_PER_S = 2.5        # voice-over pace
MIN_SCENE = 2.5          # a caption must stay >= 2 s; the scene is a bit longer
SUMMARY_HOLD = 8.0       # s: the last frame stays so that the viewer can read it
TYPES = ("title", "cast", "action", "fact", "flow", "summary", "custom")
COLOR_NAMES = {
    "favorable": FAVORABLE[0], "favorable2": FAVORABLE[1], "favorable3": FAVORABLE[2],
    "unfavorable": UNFAVORABLE[0], "unfavorable2": UNFAVORABLE[1], "unfavorable3": UNFAVORABLE[2],
    "neutral": NEUTRAL[0], "neutral2": NEUTRAL[1], "neutral3": NEUTRAL[2],
    "ink": (INK, INK), "navy": (NAVY, NAVY),
}


# ---------------------------------------------------------------- plan, voice-over, timing

def load(path):
    import yaml
    plan = yaml.safe_load(open(path, encoding="utf-8"))
    plan["_dir"] = os.path.dirname(os.path.abspath(path))
    plan.setdefault("scenes", [])
    plan.setdefault("lang", "en")
    plan.setdefault("formats", list(frame.FORMATS))
    S.use(plan.get("packs"))              # packs: [biology]; without it, every pack
    verbs.use(plan.get("packs"))
    return plan


def path(plan, p):
    return p if not p or os.path.isabs(p) else os.path.join(plan["_dir"], p)


def voiceover(plan):
    """Scene texts from voiceover.md: '## S01' headings, the text below each heading."""
    p = path(plan, plan.get("voiceover"))
    if not p or not os.path.exists(p):
        return {}
    out, cur = {}, None
    for line in open(p, encoding="utf-8"):
        m = re.match(r"^##\s+(\S+)", line)
        if m:
            cur = m.group(1)
            out[cur] = ""
        elif cur and line.strip() and not line.startswith("<!--"):
            out[cur] += " " + line.strip()
    return {k: v.strip() for k, v in out.items()}


def durations(plan):
    """Start and end of each scene: from the words of its voice-over (2.5 words/s), or "dur" in the scene.
    With synthesized audio (voice.attach puts plan["_spoken"]), a scene lasts as long as its audio,
    and a "dur" in the scene is never shorter than the audio."""
    scenes = plan["scenes"]
    vo = voiceover(plan)
    spoken = plan.get("_spoken") or {}
    times = []
    t = 0.0
    for sc in scenes:
        words = len(vo.get(sc.get("id"), "").split())
        s = spoken.get(sc.get("id"))
        d = float(sc.get("dur", max(MIN_SCENE, words / WORDS_PER_S + 0.8 if s is None else s)))
        if s is not None:
            d = max(d, s)
        if sc.get("type") == "summary" and "dur" not in sc:
            d = max(d, SUMMARY_HOLD)
        times.append((t, t + d))
        t += d
    return times


def color(name):
    if isinstance(name, (list, tuple)):
        return tuple(name)
    if name not in COLOR_NAMES:
        raise KeyError(f"unknown color {name!r}; use one of {', '.join(COLOR_NAMES)}")
    return COLOR_NAMES[name]


# ---------------------------------------------------------------- layout for the current format

SUBS = False             # subtitles on: set from plan["subtitles"] by prepare()
TIMEBAR = False          # a timeline strip at the bottom of the stage: set from plan["timeline"] by prepare()
SUB_LINES = 2


def layout():
    """Sizes for the current format. Tall frames stack items; the banner is one low row."""
    W, H = frame.W, frame.H
    tall = H > W
    banner = H < 160
    cap_scale = 1 if banner else 2
    cap_h = (LINE * cap_scale + 4) if not banner else 18
    # vertical video: apps cover the bottom ~20 % with buttons and text, keep the caption above it
    cap_y = H - cap_h - (int(H * 0.2) if tall else (2 if banner else 10))
    head_h = 0 if banner else 30
    L = dict(W=W, H=H, tall=tall, banner=banner, cap_scale=cap_scale, cap_y=cap_y,
             head_h=head_h, stage=(0, head_h, W, cap_y - 4), sprite_scale=2, subs=None)
    if SUBS:
        # subtitles: a box of SUB_LINES lines at the bottom (one line in the banner); no caption
        n = 1 if banner else SUB_LINES
        box_h = n * LINE + (n - 1) * 2 + 10
        margin = int(H * 0.2) if tall else (2 if banner else 6)
        side = 4 if banner else 8
        box = (side, H - margin - box_h, W - side, H - margin)
        if banner:      # the banner has no room below: the box sits on the right third
            box = (W * 2 // 3, H - margin - box_h, W - side, H - margin)
        L.update(subs=dict(box=box, lines=n), cap_y=box[1],
                 stage=(0, head_h, box[0] - 4 if banner else W, box[1] - 4 if not banner else H))
    if TIMEBAR:
        x0, y0, x1, y1 = L["stage"]
        h = timebar.height(L)
        L.update(timebar=(x0, y1 - h, x1, y1), stage=(x0, y0, x1, y1 - h))
    return L


def wrap(s, scale, maxw):
    """Words into lines that fit maxw px at this text scale."""
    lines, cur = [], ""
    for w in str(s).split():
        nxt = (cur + " " + w).strip()
        if cur and text_w(nxt, scale) > maxw:
            lines.append(cur)
            cur = w
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def fit_text(s, maxw, scales=(2, 1), max_lines=3):
    """The largest scale at which s wraps into max_lines or fewer. Returns (scale, lines)."""
    for k in scales:
        lines = wrap(s, k, maxw)
        if len(lines) <= max_lines and all(text_w(x, k) <= maxw for x in lines):
            return k, lines
    k = scales[-1]
    return k, wrap(s, k, maxw)


def grid(n, box, tall):
    """Cell centers for n items in a box: one row when wide, two columns (or one) when tall."""
    x0, y0, x1, y1 = box
    if tall:
        cols = 1 if n <= 2 else 2
    else:
        cols = n
    rows = (n + cols - 1) // cols
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    out = []
    for i in range(n):
        r, c = divmod(i, cols)
        in_row = min(cols, n - r * cols)
        off = (cols - in_row) * cw / 2
        out.append((int(x0 + off + cw * (c + 0.5)), int(y0 + ch * (r + 0.5))))
    return out, cw, ch


def best_scale(name, cw, ch, room=20, top=4):
    """The largest integer scale at which the sprite cell fits in a cw x ch cell, with room for a label."""
    sw, sh = S.meta()[name]["cell"]
    for k in range(top, 0, -1):
        if sw * k <= cw - 6 and sh * k <= ch - room:
            return k
    return 1


# ---------------------------------------------------------------- checks

def _texts(sc):
    for f in ("title", "sub", "caption", "credit"):
        if isinstance(sc.get(f), str):
            yield f, sc[f]
    for f in ("text",):
        for x in (sc.get(f) or []) if isinstance(sc.get(f), list) else ([sc[f]] if sc.get(f) else []):
            yield f, x
    for key in ("items", "steps"):
        for it in sc.get(key) or []:
            if isinstance(it, dict) and isinstance(it.get("label"), str):
                yield "label", it["label"]
    for a in (sc.get("actors") or {}).values():
        if isinstance(a.get("label"), str):
            yield "label", a["label"]
    for b in sc.get("beats") or []:
        if "mark" in b and isinstance(b.get("label"), str):
            yield "mark label", b["label"]


def _sprites(sc):
    for key in ("items", "steps"):
        for it in sc.get(key) or []:
            yield it.get("sprite"), it.get("anim", "idle")
    for a in (sc.get("actors") or {}).values():
        yield a.get("sprite"), a.get("anim", "idle")
        if a.get("badge"):
            yield a["badge"], "idle"
    for m in _all_marks(sc):
        if m.get("sprite"):
            yield m["sprite"], m.get("anim", "idle")
    for b in sc.get("beats") or []:
        if b.get("anim") and b.get("actor") in (sc.get("actors") or {}):
            yield sc["actors"][b["actor"]].get("sprite"), b["anim"]
        if b.get("badge"):
            yield b["badge"], "idle"
    if sc.get("sprite"):
        yield sc["sprite"], sc.get("anim", "idle")


def check(plan):
    """Rules of the skill. Returns a list of problems (empty: all pass)."""
    out = list(prepare(plan))
    carry(plan)
    out += timebar.check(plan, colors=list(COLOR_NAMES))
    if not plan.get("sources"):
        out.append("sources: list at least one source for the science in the video")
    vo = voiceover(plan)
    if not vo:
        out.append(f"voiceover not found or empty: {plan.get('voiceover')}")
    for f in plan.get("formats") or []:
        if f not in frame.FORMATS:
            out.append(f"formats: unknown format {f!r}; use {', '.join(frame.FORMATS)}")
    times = durations(plan)
    seen, used = set(), set()
    meta = S.meta()
    for sc, (a, b) in zip(plan["scenes"], times):
        sid = sc.get("id", "?")
        typ = sc.get("type")
        if sid in seen:
            out.append(f"{sid}: id is not unique")
        seen.add(sid)
        if vo and sid not in vo:
            out.append(f"{sid}: no '## {sid}' heading in the voice-over")
        if typ not in TYPES:
            out.append(f"{sid}: unknown type {typ!r}; use {', '.join(TYPES)}")
        for name, anim in _sprites(sc):
            if name not in meta:
                out.append(f"{sid}: unknown sprite {name!r} (see the cast sheet: pixsci.py sheet)")
            elif anim not in meta[name]["anims"]:
                out.append(f"{sid}: sprite {name} has no animation {anim!r}; it has {', '.join(meta[name]['anims'])}")
        for key in ("items", "steps"):
            if len(sc.get(key) or []) > 4:
                out.append(f"{sid}: {key} has more than 4 entries (they do not fit a vertical frame)")
        names = set(sc.get("actors") or {}) | set(model.parts(plan))
        out += _check_set(plan, sc, sid)
        out += [f"{sid}: {p}" for p in _check_marks(sc)]
        for beat in sc.get("beats") or []:
            if "shows" in beat and "actor" not in beat:
                continue                  # a relation drawn by custom code (model.check)
            if "counter" in beat and "actor" not in beat:
                continue                  # a counter of a panel (_check_set)
            if ("timeline" in beat or "mark" in beat) and "actor" not in beat:
                continue                  # the timeline strip (timebar.check)
            if beat.get("actor") not in names:
                out.append(f"{sid}: beat at {beat.get('t')} s names an unknown actor {beat.get('actor')!r}")
            mt = beat.get("move_to")
            if isinstance(mt, str) and (mt not in (sc.get("actors") or {}) or beat.get("actor") == mt):
                out.append(f"{sid}: beat at {beat.get('t')} s: move_to names {mt!r}, not another actor of the scene")
            elif "move_to" in beat and beat.get("actor") not in (sc.get("actors") or {}):
                out.append(f"{sid}: beat at {beat.get('t')} s: only an actor moves ({beat.get('actor')!r} is a part)")
            out += [f"{sid}: {p}" for p in verbs.check_beat(beat, names)]
            for k in ("ghost", "marks"):
                if k in beat and beat.get("actor") not in (sc.get("actors") or {}):
                    out.append(f"{sid}: beat at {beat.get('t')} s: {k}: is for an actor ({beat.get('actor')!r} is a part)")
            if "ghost" in beat and not isinstance(beat["ghost"], bool):
                out.append(f"{sid}: beat at {beat.get('t')} s: ghost: is true (the actor fades to a ghost) or false (it comes back)")
            if beat.get("verb"):
                used.add(beat["verb"])
        cap = sc.get("caption")
        if cap and len(cap.split()) > 3:
            out.append(f"{sid}: caption has {len(cap.split())} words (max 3): {cap!r}")
        if cap and b - a < 2.0:
            out.append(f"{sid}: caption is on screen {b - a:.1f} s (min 2 s)")
        for f, s in _texts(sc):
            if plan.get("lang") == "en" and not s.isascii():
                out.append(f"{sid}: {f} is not plain English text (lang: en): {s!r}")
        if typ == "title":
            for ch in (sc.get("title") or "").upper():
                if ch not in TITLE_GLYPHS:
                    out.append(f"{sid}: title character {ch!r} is not in the title font (A-Z, 0-9, - ! . ? :)")
        why = sc.get("why")
        if typ == "custom" and not (isinstance(why, str) and why.strip()):
            out.append(f"{sid}: a custom scene needs why: (one line: no scene type shows this set, or the frame "
                       f"is key (hook, turn, end) and a scene type shows it worse)")
        if typ == "fact" and len(sc.get("text") or []) > 3:
            out.append(f"{sid}: a fact has 3 lines of text or fewer")
    # text must fit in each format
    for f in plan.get("formats") or []:
        if f not in frame.FORMATS:
            continue
        frame.use(f)
        L = layout()
        if TIMEBAR:
            out += [f"{p} [{f}]" for p in timebar.fit(plan, L)]
        for sc in plan["scenes"]:
            cap = sc.get("caption")
            if cap:
                k, lines = fit_text(cap, L["W"] - 16, (L["cap_scale"], 1), max_lines=1 if L["banner"] else 2)
                if len(lines) > (1 if L["banner"] else 2):
                    out.append(f"{sc.get('id')}: caption {cap!r} does not fit the {f} frame")
    frame.use("landscape")
    for name in sorted(used & set(verbs.all())):
        ms = verbs.bench(name)
        if ms > verbs.MAX_MS:
            out.append(f"warning: verb {name} takes {ms:.1f} ms a frame (limit {verbs.MAX_MS} ms); make its primitives faster")
    plan.pop("_world", None)
    fmts = [x for x in (plan.get("formats") or ["landscape"]) if x in frame.FORMATS] or ["landscape"]
    for i, f in enumerate(fmts):          # the model once; contact (geometry) in each format
        frame.use(f)
        carry(plan)
        found = model.check(plan, positions=lambda si, sc, t: _positions(sc, t, plan), stage=layout()["stage"])
        found += _touch(plan)
        out += found if i == 0 else [f"{p} [{f}]" for p in found if "(contact)" in p]
    frame.use("landscape")
    if not plan["scenes"] or plan["scenes"][-1].get("type") not in ("summary", "custom"):
        out.append("the last scene must be a summary (or a custom final frame)")
    story_end = times[-2][1] if len(times) > 1 and plan["scenes"][-1].get("type") == "summary" else (times[-1][1] if times else 0)
    limit = float(plan.get("max_s", 60))
    if story_end > limit:
        out.append(f"length before the summary {story_end:.0f} s: keep it at 20-45 s ({limit:.0f} s at most, max_s)")
    return out


def _check_set(plan, sc, sid):
    """Problems of a scene's set, zones, counters, and continue."""
    out = []
    st = sc.get("set")
    if sc.get("continue"):
        i = plan["scenes"].index(sc)
        if sc.get("type") != "action" or i == 0 or plan["scenes"][i - 1].get("type") != "action":
            out.append(f"{sid}: continue: true goes on from an action scene into an action scene")
    if st:
        if sc.get("type") != "action":
            return out + [f"{sid}: set: is for action scenes"]
        out += sets.check(st, sid)
    if st and st.get("type") == "panels" and not out:
        for f in plan.get("formats") or []:
            if f in frame.FORMATS:
                frame.use(f)
                out += [f"{sid}: {p} [{f}]" for p in sets.fit(st, layout(), sc.get("beats") or [])]
        frame.use("landscape")
    zs = set(sets.zones(st, layout())) | ({"all"} if st and st.get("type") == "panels" else set())
    for name, a in (sc.get("actors") or {}).items():
        if a.get("in") == "all" and a.get("parts"):
            out.append(f"{sid}: actor {name} is in all panels and has parts; parts and binds show in one panel "
                       f"only, so give each panel its own actor")
        if a.get("in") and a["in"] not in zs:
            out.append(f"{sid}: actor {name} is in {a['in']!r}, not a zone of the set"
                       f"{' (' + ', '.join(sorted(zs)) + ')' if zs else ' (the scene has no set:)'}")
    acts = sc.get("actors") or {}
    for b in sc.get("beats") or []:
        a, tg = acts.get(b.get("actor")) or {}, acts.get(b.get("target")) or {}
        if a.get("in") == "all" and b.get("target") and tg.get("in") != "all":
            out.append(f"{sid}: beat at {b.get('t')} s: {b['actor']} is in all panels, so its target is too "
                       f"(in: all); for one panel, give that panel its own actor")
    names = {n for n, _ in sets.panels(st)} if st and st.get("type") == "panels" else set()
    for b in sc.get("beats") or []:
        if "counter" in b and b.get("panel") not in names:
            out.append(f"{sid}: beat at {b.get('t')} s: counter needs panel: one of {', '.join(sorted(names)) or 'the panels of a panels set'}")
    return out


# ---------------------------------------------------------------- shared drawing

def _bg(sc, t):
    name = sc.get("bg", "paper")
    fn = bg.ALL.get(name, bg.paper)
    return fn(t) if fn is bg.bloodstream else fn()


def _heading(img, L, s):
    if s and not L["banner"]:
        k, lines = fit_text(s, L["W"] - 24, (1,), max_lines=1)
        text(img, 12, 8, lines[0], NAVY)
        ImageDraw.Draw(img).line([12, 26, 12 + text_w(lines[0]), 26], fill=C(NAVY))


def _caption(img, L, sc, t):
    cap = sc.get("caption")
    if not cap or t < 0.3 or L.get("subs"):
        return
    k, lines = fit_text(cap, L["W"] - 16, (L["cap_scale"], 1), max_lines=1 if L["banner"] else 2)
    lh = LINE * k + 2
    y = L["cap_y"] - (len(lines) - 1) * lh
    d = ImageDraw.Draw(img)
    w = max(text_w(s, k) for s in lines)
    cx = L["W"] // 2
    d.rectangle([cx - w // 2 - 6, y - 3, cx + w // 2 + 6, y + lh * len(lines) - 1], fill=C(NAVY))
    for i, s in enumerate(lines):
        text(img, cx, y + lh * i, s, WHITE, scale=k, align="c")


def _one_line(s, maxw, scales):
    """The largest scale at which s stays on one line; else the smallest scale, wrapped."""
    for k in scales:
        if text_w(s, k) <= maxw:
            return k, [s]
    return fit_text(s, maxw, scales[-1:], max_lines=2)


def _label(img, x, y, s, col, maxw):
    k, lines = fit_text(s, maxw, (1,), max_lines=2)
    for i, ln in enumerate(lines):
        text(img, x, y + LINE * i, ln, col, align="c")


def _sprite(img, name, anim, t, x, y, scale, seed=0, flip=False):
    if anim == "idle":
        S.idle(img, name, t, x, y, seed=seed, scale=scale, flip=flip)
    else:
        S.draw(img, name, anim, t, x, y, scale=scale, flip=flip)


def _arrow(d, x0, y0, x1, y1, col):
    d.line([x0, y0, x1, y1], fill=C(col), width=2)
    if abs(x1 - x0) >= abs(y1 - y0):
        s = 1 if x1 > x0 else -1
        d.polygon([(x1, y1), (x1 - 5 * s, y1 - 4), (x1 - 5 * s, y1 + 4)], fill=C(col))
    else:
        s = 1 if y1 > y0 else -1
        d.polygon([(x1, y1), (x1 - 4, y1 - 5 * s), (x1 + 4, y1 - 5 * s)], fill=C(col))


def _items(img, L, items, t, box, t0=0.3, step=0.35, labels=True, still=False):
    """Sprites in a grid with labels under them. Returns the cell centers."""
    n = len(items)
    if not n:                         # a text-only scene (a summary with no items)
        return []
    pts, cw, ch = grid(n, box, L["tall"])
    # one scale for all items, so that sizes compare
    common = min([best_scale(it["sprite"], cw, ch, room=22 if labels else 4, top=2 if L["banner"] else 4)
                  for it in items] or [1])
    for i, (it, (x, y)) in enumerate(zip(items, pts)):
        ti = t0 + step * i
        if t < ti and not still:
            continue
        k = int(it.get("scale") or common)
        sh = S.meta()[it["sprite"]]["cell"][1] * k
        cy = y - (9 if labels and it.get("label") else 0)
        _sprite(img, it["sprite"], it.get("anim", "idle"), 0.0 if still else t - ti, x, cy, k, seed=i)
        if labels and it.get("label"):
            _label(img, x, cy + sh // 2 + 3, it["label"], color(it.get("color", "ink"))[0], cw - 4)
    return pts


# ---------------------------------------------------------------- scene painters

def p_title(plan, sc, t, dur, ctx):
    img = bg.paper()
    L = layout()
    W, H = L["W"], L["H"]
    s = (sc.get("title") or "").upper()
    k = 6
    while k > 2 and len(s) * 6 * k > W - 16:
        k -= 1
    th = 7 * k
    sub_k, sub = fit_text(sc.get("sub") or "", W - 24, (2, 1) if not L["banner"] else (1,), max_lines=2)
    block = th + (12 + len(sub) * LINE * sub_k if sub else 0)
    top = max(4, (H - block) // 2 - (10 if not L["banner"] else 0))
    y = int(lerp(-th - 10, top, ease(seg(t, 0, 0.6))))
    title_text(img, W // 2, y, s, k, XBLUE, NAVY, back=LGREY)
    if sub and t > 0.5:
        for i, ln in enumerate(sub):
            text(img, W // 2, top + th + 12 + i * LINE * sub_k, ln, INK, scale=sub_k, align="c")
    if sc.get("credit") and t > 0.8 and not L["banner"]:
        text(img, W // 2, H - 26, sc["credit"], DGREY, align="c")
    return img


def p_cast(plan, sc, t, dur, ctx):
    """The characters of the story in a row (a grid in a tall frame), each with a label."""
    img = _bg(sc, t)
    L = layout()
    _heading(img, L, sc.get("title"))
    _items(img, L, sc.get("items") or [], t, L["stage"])
    _caption(img, L, sc, t)
    return img


def p_flow(plan, sc, t, dur, ctx):
    """Steps of a process with arrows: left to right, or top to bottom in a tall frame."""
    img = _bg(sc, t)
    L = layout()
    _heading(img, L, sc.get("title"))
    steps = sc.get("steps") or []
    n = len(steps)
    step_t = max(0.35, min(0.9, (dur - 1.0) / max(1, n)))
    box = L["stage"]
    if L["tall"]:
        x0, y0, x1, y1 = box
        ch = (y1 - y0) / n
        pts = [(L["W"] // 2, int(y0 + ch * (i + 0.5))) for i in range(n)]
        cw = x1 - x0
    else:
        pts, cw, ch = grid(n, box, False)
    d = ImageDraw.Draw(img)
    for i, (st, (x, y)) in enumerate(zip(steps, pts)):
        ti = 0.3 + step_t * i
        if t < ti:
            continue
        if L["tall"]:
            k = int(st.get("scale") or best_scale(st["sprite"], cw / 2, ch, room=4, top=3))
            sw = S.meta()[st["sprite"]]["cell"][0] * k
            _sprite(img, st["sprite"], st.get("anim", "idle"), t - ti, x - sw // 2 - 4, y, k, seed=i)
            k2, lines = fit_text(st.get("label", ""), L["W"] // 2 - 12, (1,), max_lines=2)
            for j, ln in enumerate(lines):
                text(img, x + 6, y - LINE * len(lines) // 2 + LINE * j, ln, INK)
            if i + 1 < n and t > ti + step_t * 0.6:
                _arrow(d, x, int(y + ch / 2 - 6), x, int(y + ch / 2 + 6), DGREY)
        else:
            k = int(st.get("scale") or best_scale(st["sprite"], cw - 24, ch, room=22, top=2 if L["banner"] else 3))
            sh = S.meta()[st["sprite"]]["cell"][1] * k
            sw = S.meta()[st["sprite"]]["cell"][0] * k
            cy = y - 9
            _sprite(img, st["sprite"], st.get("anim", "idle"), t - ti, x, cy, k, seed=i)
            _label(img, x, cy + sh // 2 + 3, st.get("label", ""), INK, cw - 8)
            if i + 1 < n and t > ti + step_t * 0.6:
                xa = int(x + max(sw // 2 + 4, cw * 0.32))
                xb = int(pts[i + 1][0] - max(sw // 2 + 4, cw * 0.32))
                if xb - xa >= 8:
                    _arrow(d, xa, cy, xb, cy, DGREY)
    _caption(img, L, sc, t)
    return img


def p_fact(plan, sc, t, dur, ctx):
    """One idea: a sprite and 1 to 3 short lines (beside it when wide, under it when tall)."""
    img = _bg(sc, t)
    L = layout()
    W = L["W"]
    x0, y0, x1, y1 = L["stage"]
    lines = sc.get("text") or []
    lines = [lines] if isinstance(lines, str) else lines
    name = sc.get("sprite")
    if L["tall"] or W == L["H"]:
        share = 0.5 if L["tall"] else 0.36
        k = best_scale(name, W - 20, (y1 - y0) * share, room=4) if name else 0
        sy = y0 + int((y1 - y0) * share / 2)
        if name:
            _sprite(img, name, sc.get("anim", "idle"), t, W // 2, sy, k)
        ty = sy + (S.meta()[name]["cell"][1] * k // 2 + 10 if name else 0)
        tx, align, maxw = W // 2, "c", W - 20
    else:
        k = best_scale(name, W * 0.3, y1 - y0, room=4) if name else 0
        if name:
            _sprite(img, name, sc.get("anim", "idle"), t, int(W * 0.18), (y0 + y1) // 2, k)
        tx, align, maxw = int(W * 0.36), "l", int(W * 0.6)
        ty = None
    room = y1 - (ty if ty is not None else y0)
    for scales in (((1,) if L["banner"] else (2, 1)), (1,)):
        shown = [fit_text(s, maxw, scales, max_lines=2) for s in lines]
        total_h = sum(len(ww) * LINE * kk + 6 for kk, ww in shown)
        if total_h <= room:
            break
    y = ty if ty is not None else (y0 + y1) // 2 - total_h // 2
    n_chars = int(max(0, t - 0.3) * 40)
    used = 0
    for i, (kk, ww) in enumerate(shown):
        for ln in ww:
            k_vis = int(clamp(n_chars - used, 0, len(ln)))
            used += len(ln)
            text(img, tx, y, ln[:k_vis], NAVY if i == 0 else INK, scale=kk, align=align)
            y += LINE * kk
        y += 6
    _caption(img, L, sc, t)
    return img


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


def _copies(sc, a, L):
    """Boxes of the other panels for an actor with in: all (drawn in each panel)."""
    if a.get("in") != "all" or not sc.get("set"):
        return []
    return list(sets.zones(sc["set"], L).values())[1:]


def carry(plan):
    """Scenes with continue: true go on from the scene before: its set, background, title, and actors as they are at
    its end (place, zone, flip, badge, ghost, marks, shown). Their own actors add to these or change them.
    Runs for the current format (an end place found by move_to depends on it), after prepare()."""
    times, prev = None, None
    for i, sc in enumerate(plan["scenes"]):
        sc.setdefault("_own", dict(sc.get("actors") or {}))
        sc.setdefault("_own_keys", sorted(sc))
        if sc.get("continue") and prev is not None and prev.get("type") == sc.get("type") == "action":
            times = times or durations(plan)
            a0, a1 = times[i - 1]
            beats = _expand(prev, plan)
            for k in ("set", "bg", "title"):
                if k not in sc["_own_keys"] and k in prev:
                    sc[k] = prev[k]
            st = sc.get("set")
            if "set" not in sc["_own_keys"] and st and st.get("type") == "panels":    # counters go on too
                end = sets.counters(st, beats, a1 - a0)
                sc["set"] = dict(st, panels=[dict(p, counter=end.get(n)) for n, p in sets.panels(st)])
            dead = model.world(plan)[i]["dead"] if plan.get("model") else set()
            out = {}
            for name, a in (prev.get("actors") or {}).items():
                x, y, _, _, flip, badge, shown = _actor_state(a, beats, name, a1 - a0)
                ghost = _ghost(a, beats, name, a1 - a0)[1] == "ghost"
                c = {k: v for k, v in a.items() if k != "anim"}
                c.update(at=[round(x, 4), round(y, 4)], flip=flip, badge=badge, ghost=ghost,
                         marks=_marks(a, beats, name, a1 - a0), hidden=not shown or (name in dead and not ghost))
                if "parts" in a or any(b.get("actor") == name and "parts" in b for b in beats):
                    c["parts"] = model.shown_parts(a, beats, name)
                out[name] = c
            for name, a in sc["_own"].items():
                out[name] = dict(out.get(name, {}), **a)
            sc["actors"] = out
        prev = sc


def _actor_state(a, beats, name, t):
    """Position (fractions of the stage), animation, the time in that animation, flip, badge, shown."""
    x, y = a.get("at", [0.5, 0.5])
    anim, a_t0 = a.get("anim", "idle"), 0.0
    flip, badge, shown = bool(a.get("flip", False)), a.get("badge"), not a.get("hidden", False)
    for b in sorted((b for b in beats if b.get("actor") == name), key=lambda b: float(b.get("t", 0))):
        bt = float(b.get("t", 0))
        if t < bt:
            break
        if "move_to" in b and not isinstance(b["move_to"], str):    # an actor name is resolved by _approach
            d = float(b.get("dur", 1.0))
            k = ease(seg(t, bt, bt + d))
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
        if "ghost" in b:                   # a hidden actor appears as a ghost
            shown = True
    return x, y, anim, t - a_t0, flip, badge, shown


GHOST_S = 1.0          # s: an actor fades to its ghost, or a ghost comes back


def _ghost(a, beats, name, t):
    """(look before, look now, progress 0..1) of an actor; a look is real, ghost, or none (hidden).
    A beat ghost: true fades the actor to its ghost (or a hidden actor appears as one); ghost: false brings it back."""
    look = "ghost" if a.get("ghost") else "real"
    prev, u = look, 1.0
    for b in sorted((b for b in beats if b.get("actor") == name and "ghost" in b), key=lambda b: float(b.get("t", 0))):
        bt = float(b.get("t", 0))
        if t < bt:
            break
        prev = look if _actor_state(a, beats, name, bt - 1e-6)[6] else "none"
        look, u = "ghost" if b["ghost"] else "real", min(1.0, (t - bt) / GHOST_S)
    return prev, look, u


def _marks(a, beats, name, t):
    """Marks on the actor's body at time t: its marks:, then the list of the last beat with marks:."""
    out = a.get("marks") or []
    for b in sorted((b for b in beats if b.get("actor") == name and "marks" in b), key=lambda b: float(b.get("t", 0))):
        if float(b.get("t", 0)) <= t:
            out = b["marks"] or []
    return out


def _all_marks(sc):
    for a in (sc.get("actors") or {}).values():
        yield from (m for m in a.get("marks") or [] if isinstance(m, dict))
    for b in sc.get("beats") or []:
        yield from (m for m in b.get("marks") or [] if isinstance(m, dict))


def _check_marks(sc):
    """Problems of marks on actors' bodies."""
    out = []
    lists = [(f"actor {n}", a["marks"]) for n, a in (sc.get("actors") or {}).items() if "marks" in a]
    lists += [(f"beat at {b.get('t')} s", b["marks"]) for b in sc.get("beats") or [] if "marks" in b]
    for who, ms in lists:
        if not isinstance(ms, list):
            out.append(f"{who}: marks: is a list of {{at: [x, y], sprite: ...}} or {{at: [x, y], color: ...}}")
            continue
        for m in ms:
            at = m.get("at") if isinstance(m, dict) else None
            if not (isinstance(at, list) and len(at) == 2 and all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in at)):
                out.append(f"{who}: a mark needs at: [x, y], fractions of the sprite (0 to 1): {m!r}")
            elif bool(m.get("sprite")) == bool(m.get("color")):
                out.append(f"{who}: a mark has a sprite: or a color: (a dot), one of them: {m!r}")
            elif m.get("color") and m["color"] not in COLOR_NAMES:
                out.append(f"{who}: mark color {m['color']!r} is unknown; use one of {', '.join(COLOR_NAMES)}")
    return out


HEAD_GAP = model.HEAD + 2 * model.STALK + 4      # units: a bind placed by move_to shows both stalks


def _approach(plan, sc, beats):
    """Beats with `move_to: <actor>` get the place where the mover touches that actor (fractions of the stage):
    edge to edge along the way it comes, or, when their parts bind, at the gap of the bind on a level or
    upright axis. Sizes come from the sprites, so the place fits every format."""
    if not any(isinstance(b.get("move_to"), str) for b in beats):
        return beats
    L = layout()
    x0, y0, x1, y1 = L["stage"]
    sw, sh = (x1 - x0) or 1, (y1 - y0) or 1
    todo = [i for i, b in enumerate(beats) if isinstance(b.get("move_to"), str)]
    out = list(beats)
    for _ in range(2):              # twice: a target that itself moves to an actor is placed by the first pass
        out = _approach_once(plan, sc, beats, out, todo, L, (x0, y0, sw, sh))
    return out


def _approach_once(plan, sc, beats, done, todo, L, stage):
    actors = sc.get("actors") or {}
    x0, y0, sw, sh = stage
    out = list(done)
    for i in sorted(todo, key=lambda i: float(beats[i].get("t", 0))):
        b = beats[i]
        me, tg = b.get("actor"), b.get("move_to")
        if me not in actors or tg not in actors or me == tg:
            continue
        bt, end = float(b.get("t", 0)), float(b.get("t", 0)) + float(b.get("dur", 1.0))
        mx, my, _, _, mf = _actor_state(actors[me], out, me, bt)[:5]
        tx, ty, _, _, tf = _actor_state(actors[tg], out, tg, end)[:5]
        km, kt = _scale(sc, actors[me], L), _scale(sc, actors[tg], L)
        mb = _box(sc, actors[me], L)
        mx, my = _place(sc, actors[me], L, mx, my, km)
        tx, ty = _place(sc, actors[tg], L, tx, ty, kt)
        bind = model.bind_between(plan, sc, me, tg, out, end) if plan else None
        if bind:
            d = model._axis(mx - tx, my - ty)                      # level or upright, on the target's line
            ua = model.unit(km)
            mols = (model.is_molecule(actors[me]["sprite"]), model.is_molecule(actors[tg]["sprite"]))
            lo, hi = model.bind_range(plan, bind[1], bind[2], ua, d, mols)
            gap = max(lo, min(hi - 1, max(lo + 2, HEAD_GAP * ua * (2 - sum(mols)) // 2)))  # inside, not on, the ends
        else:
            dist = math.hypot(mx - tx, my - ty) or 1.0
            d, gap = ((mx - tx) / dist, (my - ty) / dist), 0
        far = (model.reach(actors[tg]["sprite"], kt, d, flip=tf) + gap
               + model.reach(actors[me]["sprite"], km, (-d[0], -d[1]), flip=mf))
        nx, ny = tx + d[0] * far, ty + d[1] * far
        out[i] = dict(b, move_to=[round((nx - mb[0]) / ((mb[2] - mb[0]) or 1), 4),
                                  round((ny - mb[1]) / ((mb[3] - mb[1]) or 1), 4)])
    return out


def _expand(sc, plan=None):
    """The scene's beats (move_to an actor resolved) plus show/hide beats that verbs add (show: at the start,
    hide: at the end)."""
    out = _approach(plan, sc, list(sc.get("beats") or []))
    for b in sc.get("beats") or []:
        if not b.get("verb"):
            continue
        v = verbs.get(b["verb"])
        bt = float(b.get("t", 0))
        for key, when, val in (("show", bt, True), ("hide", bt + verbs.duration(b["verb"]), False)):
            who = v.get(key)
            if who:
                out.append({"t": when, "actor": b.get(who) if who == "target" else b["actor"], "show": val})
    return out


def _touch(plan):
    """A verb with a hit must reach its target: at the moment of contact their sprites touch (current format)."""
    out = []
    for sc in plan["scenes"]:
        if sc.get("type") != "action":
            continue
        actors = sc.get("actors") or {}
        try:
            hits = _hits(sc)
            beats = _expand(sc, plan)
        except KeyError:                  # an unknown verb: reported by the beat checks
            continue
        for th, _, att, tg in hits:
            if att not in actors or tg not in actors or model.bind_between(plan, sc, att, tg, beats, th):
                continue                  # bound things touch through their parts, across the gap of the bind
            st = _positions(sc, th, plan)
            (ax, ay, _, ka), (tx, ty, _, kt) = st[att][:4], st[tg][:4]
            if not (st[att][8] and st[tg][8]):
                continue
            dist = math.hypot(tx - ax, ty - ay) or 1.0
            d = ((tx - ax) / dist, (ty - ay) / dist)
            gap = (dist - model.reach(actors[att]["sprite"], ka, d, flip=st[att][6])
                   - model.reach(actors[tg]["sprite"], kt, (-d[0], -d[1]), flip=st[tg][6]))
            if gap > 2:
                out.append(f"{sc.get('id')}: hit at {th:.2f} s: {att} does not touch {tg} ({gap:.0f} px apart) "
                           f"(contact): move it with move_to: {tg}")
    return out


def _hits(sc):
    """[(contact time, params, attacker, target)] of the beats whose verb has hit mechanics."""
    out = []
    for b in sc.get("beats") or []:
        if b.get("verb") and b.get("target"):
            h = verbs.hit(b["verb"], b)
            if h:
                at, p, by = h
                a, tg = (b["target"], b["actor"]) if by == "target" else (b["actor"], b["target"])
                out.append((float(b.get("t", 0)) + at, p, a, tg))
    return out


def _positions(sc, t, plan=None):
    """Actor state of an action scene at time t, for checks (no hit offsets)."""
    beats = _expand(sc, plan)
    L = layout()
    out = {}
    for name, a in (sc.get("actors") or {}).items():
        fx_, fy_, anim, at, flip, badge, shown = _actor_state(a, beats, name, t)
        k = _scale(sc, a, L)
        cw, ch = S.meta()[a["sprite"]]["cell"]
        out[name] = [*_place(sc, a, L, fx_, fy_, k), max(cw, ch) * k / 2, k, anim, at, flip, badge, shown]
    return out


def p_action(plan, sc, T, dur, ctx):
    """Actors on a stage and timed beats: move, change animation, flip, add or remove a badge, verbs.
    Positions are fractions of the stage (0..1), so the scene fits every format.
    A verb with hit mechanics stops the picture for a moment on contact (the scene time T is warped)."""
    if "beats" not in ctx:
        ctx["beats"], ctx["hits"] = _expand(sc, plan), _hits(sc)
    beats, hits = ctx["beats"], ctx["hits"]
    t, shake = fx.warp(T, [h[:2] for h in hits])
    img = _bg(sc, t)
    L = layout()
    if sc.get("set"):
        sets.draw(img, sc["set"], L, beats, t)
    base = img.copy()
    _heading(img, L, sc.get("title"))
    actors = sc.get("actors") or {}
    state, frac = {}, {}
    for name, a in actors.items():
        fx_, fy_, anim, at, flip, badge, shown = _actor_state(a, beats, name, t)
        frac[name] = (fx_, fy_)
        k = _scale(sc, a, L)
        cw, ch = S.meta()[a["sprite"]]["cell"]
        state[name] = [*_place(sc, a, L, fx_, fy_, k), max(cw, ch) * k / 2, k, anim, at, flip, badge, shown]
    for th, p, att, tg in hits:                        # windup of the attacker, push of the target
        if att in state and tg in state:
            dx, dy = state[tg][0] - state[att][0], state[tg][1] - state[att][1]
            d = math.hypot(dx, dy) or 1.0
            for who, role in ((att, "attacker"), (tg, "target")):
                o = fx.offset(t, th, p, role)
                state[who][0] += dx / d * o
                state[who][1] += dy / d * o
    si = ctx.get("si", 0)
    model.agent_place(plan, si, sc, t, state, beats)
    copies = {}                                        # in: all: the same actor in each other panel
    for name, a in actors.items():
        (fx_, fy_), home = frac[name], _box(sc, a, L)
        for bx in _copies(sc, a, L):
            copies.setdefault(name, []).append((bx[0] - home[0] + fx_ * (bx[2] - bx[0] - home[2] + home[0]),
                                                bx[1] - home[1] + fy_ * (bx[3] - bx[1] - home[3] + home[1])))
    for i, (name, a) in enumerate(actors.items()):
        px, py, r, k, anim, at, flip, badge, shown = state[name]
        if not shown:
            continue
        look, marks = _ghost(a, beats, name, t), _marks(a, beats, name, t)
        for dx, dy in [(0, 0)] + copies.get(name, []):
            _draw_actor(img, a, L, int(px + dx), int(py + dy), k, anim, at, flip, badge, i,
                        bottom=_box(sc, a, L)[3] + dy if a.get("in") and a["in"] != "border" else None,
                        look=look, marks=marks, t=t)
    heads = model.draw(img, plan, si, sc, t, state, beats)
    where = {n: tuple(v[:3]) for n, v in state.items()}
    where.update({n: v for n, v in heads.items() if n not in where})
    cv = fx.Canvas(img, base)
    for i, b in enumerate(beats):
        name, bt = b.get("verb"), float(b.get("t", 0))
        if not name or not bt <= t <= bt + verbs.duration(name) or b.get("actor") not in where:
            continue
        for j, (dx, dy) in enumerate([(0, 0)] + copies.get(b["actor"], [])):
            g = where[b["actor"]]
            geo = {"actor": (g[0] + dx, g[1] + dy) + tuple(g[2:])}
            if b.get("target") in where:
                g = where[b["target"]]
                ox, oy = copies[b["target"]][j - 1] if j and b["target"] in copies else (0, 0)
                geo["target"] = (g[0] + ox, g[1] + oy) + tuple(g[2:])    # both in all panels: this panel's
            verbs.play(cv, name, t - bt, geo, seed=int(plan.get("seed", 0)) * 101 + i)
    if shake:
        s = shake if int(T * 30) % 2 else -shake
        cv.shift(s, -s // 2)
    img = cv.image()
    _caption(img, L, sc, t)
    return img


def _draw_actor(img, a, L, px, py, k, anim, at, flip, badge, i, bottom=None, look=("real", "real", 1.0), marks=(), t=0.0):
    """An actor with its marks, badge, and label. look: (before, now, progress) from _ghost: a change of look
    dissolves (Bayer) from the one before to the one now."""
    prev, now, u = look
    if now == "real" and (u >= 1 or prev == "real"):
        _body(img, a, px, py, k, anim, at, flip, badge, i, marks, t)
    else:
        import numpy as np
        from PIL import Image
        from .scene import dither_mask
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        _body(lay, a, px, py, k, anim, at, flip, badge, i, marks, t)
        arr = np.array(lay)
        looks = {"real": arr, "ghost": S.ghost(arr, k), "none": np.zeros_like(arr)}
        mix = np.where(dither_mask(*arr.shape[:2], u)[..., None], looks[now], looks[prev]) if u < 1 else looks[now]
        over = Image.fromarray(mix.astype(np.uint8))
        img.paste(over, (0, 0), over)
    sh = S.meta()[a["sprite"]]["cell"][1] * k
    if a.get("label") and not L["banner"] and not (now == "none" or (prev == "none" and u < 0.5)):
        y = py + sh // 2 + 2
        if bottom is not None:                      # in a zone: the label stays inside it
            y = min(y, int(bottom) - LINE)
        text(img, px, y, a["label"], color(a.get("color", "ink"))[0], align="c")


def _body(img, a, px, py, k, anim, at, flip, badge, i, marks, t):
    """The sprite, the marks on it (at: fractions of its cell, mirrored with it), and the badge above it."""
    _sprite(img, a["sprite"], anim, at, px, py, k, seed=i, flip=flip)
    m = S.meta()[a["sprite"]]
    (cw, ch), (ax, ay) = m["cell"], m["anchor"]
    x0, y0 = px - (cw - ax if flip else ax) * k, py - ay * k
    for mk in marks:
        fx_, fy_ = mk["at"]
        mx, my = x0 + (1 - fx_ if flip else fx_) * cw * k, y0 + fy_ * ch * k
        if mk.get("sprite"):
            S.draw(img, mk["sprite"], mk.get("anim", "idle"), t, mx, my, scale=k, flip=flip)
        else:
            r = max(1, int(mk.get("size", 2)) * k // 2)
            ImageDraw.Draw(img).rectangle([mx - r, my - r, mx + r - 1, my + r - 1], fill=C(color(mk["color"])[0]))
    if badge:
        sh, bh = ch * k, S.meta()[badge]["cell"][1] * k
        S.draw(img, badge, "idle", 0, px, max(bh // 2 + 1, py - sh // 2 - bh // 2 + 2), scale=k)


def p_summary(plan, sc, t, dur, ctx):
    """The last frame: a heading, up to 4 sprites with labels, and 1 or 2 lines of conclusion.
    It appears in about 1.5 s and then holds still."""
    img = bg.plain()
    L = layout()
    W, H = L["W"], L["H"]
    _heading(img, L, sc.get("title") or plan.get("title"))
    lines = sc.get("text") or []
    lines = [lines] if isinstance(lines, str) else lines
    fitted = [_one_line(s, W - 20, (1,) if L["banner"] else (2, 1)) for s in lines]
    text_h = sum(len(ww) * LINE * kk + 4 for kk, ww in fitted)
    # the bottom of the free area: above the subtitle box when subtitles are on
    bottom = L["subs"]["box"][1] - 4 if L["subs"] else H - (int(H * 0.2) if L["tall"] else 8)
    x0, y0, x1, y1 = 0, L["head_h"], W, bottom - text_h
    if not sc.get("items"):            # a text-only frame: the conclusion in the middle
        y1 = L["head_h"] + (bottom - L["head_h"] - text_h) // 2
    if L["banner"]:
        # one low row: sprites on the left half, conclusion on the right half
        _items(img, L, sc.get("items") or [], t, (0, 4, W // 2, H - 4), t0=0.2, step=0.2, labels=False)
        banner_fit = [fit_text(s, W // 2 - 16, (1,), max_lines=2) for s in lines]
        bh = sum(len(ww) * LINE * kk for kk, ww in banner_fit)
        free = L["subs"]["box"][1] if L["subs"] else H     # the subtitle box sits on the right, at the bottom
        y = max(2, free // 2 - bh // 2)
        for kk, ww in banner_fit:
            if t >= 1.0:
                for ln in ww:
                    text(img, W * 3 // 4 if sc.get("items") else W // 2, y, ln, NAVY, scale=kk, align="c")
                    y += LINE * kk
        return img
    _items(img, L, sc.get("items") or [], t, (x0, y0, x1, y1), t0=0.2, step=0.2)
    if t >= 1.2:
        y = y1 + 4
        for i, (kk, ww) in enumerate(fitted):
            for ln in ww:
                text(img, W // 2, y, ln, NAVY if i == 0 else INK, scale=kk, align="c")
                y += LINE * kk
            y += 4
    return img


def p_custom(plan, sc, t, dur, ctx):
    """A scene drawn by a Python function: module (path), function (default draw).
    The function gets (img, t, scene, ctx) and reads frame.W, frame.H for the layout."""
    fn = ctx.get("_fn")
    if fn is None:
        spec = importlib.util.spec_from_file_location("custom_" + sc["id"], path(plan, sc["module"]))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = ctx["_fn"] = getattr(mod, sc.get("function", "draw"))
    img = _bg(sc, t)
    L = layout()
    _heading(img, L, sc.get("title"))     # the same heading as the other scene types
    shows = {}                            # relation: the first time the scene shows it
    for b in sc.get("beats") or []:
        if "shows" in b:
            shows[b["shows"]] = min(shows.get(b["shows"], 1e9), float(b.get("t", 0)))
    fn(img, t, sc, dict(ctx, plan=plan, layout=L, dur=dur, shows=shows))
    _caption(img, L, sc, t)
    return img


PAINTERS = {k[2:]: v for k, v in globals().items() if k.startswith("p_")}


# ---------------------------------------------------------------- timeline

def prepare(plan):
    """Words of the voice-over in time (aligned, or estimated) and beats placed on their words.
    Runs once per plan; plan["_outdir"] is where voice/<scene>.words.json are. Returns problems."""
    global SUBS, TIMEBAR
    SUBS = bool(plan.get("subtitles"))
    TIMEBAR = bool(plan.get("timeline"))
    if "_words" in plan:
        return plan.get("_word_problems", [])
    WD.attach(plan, voiceover(plan), plan.get("_outdir"))
    plan["_word_problems"] = WD.resolve_beats(plan)
    return plan["_word_problems"]


def _sub_lines(ws, maxw):
    """Words into lines that fit maxw (scale 1): [[(i, word, x)]], x from the line start."""
    lines, cur, x = [], [], 0
    sp = text_w(" ")
    for i, w in enumerate(ws):
        ww = text_w(w)
        if cur and x + sp + ww > maxw:
            lines.append(cur)
            cur, x = [], 0
        if cur:
            x += sp
        cur.append((i, w, x))
        x += ww
    if cur:
        lines.append(cur)
    return lines


def subtitles(plan, times):
    """overlay(arr, T) for Timeline: the voice-over word for word in a box at the bottom.
    Each word types in letter by letter while it is said; the word being said is yellow."""
    if not SUBS:
        return None
    L = layout()
    x0, y0, x1, y1 = L["subs"]["box"]
    n = L["subs"]["lines"]
    maxw = x1 - x0 - 12
    allw = WD.timeline_words(plan, times)
    fits = lambda ws: len(_sub_lines(ws, maxw)) <= n
    pgs = WD.pages(allw, fits)
    spans = WD.page_spans(pgs, times[-1][1] if times else 0)
    laid = [_sub_lines([w[0] for w in p], maxw) for p in pgs]
    from PIL import Image
    import numpy as np

    st = plan.get("subtitles") if isinstance(plan.get("subtitles"), dict) else {}
    fill, edge, inner = st.get("fill", NAVY), st.get("border", BLACK), st.get("inner", XBLUE)
    ink, hi = st.get("text", WHITE), st.get("highlight", YELLOW)

    def box(img):
        d = ImageDraw.Draw(img)
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=C(fill), outline=C(edge))
        d.rectangle([x0 + 2, y0 + 2, x1 - 3, y1 - 3], outline=C(inner))

    def overlay(arr, T):
        k = next((i for i, (a, b) in enumerate(spans) if a <= T < b), None)
        img = Image.fromarray(arr)
        box(img)
        if k is not None:
            p = pgs[k]
            for r, line in enumerate(laid[k]):
                y = y0 + 5 + r * (LINE + 2)
                for i, w, x in line:
                    _, s, e = p[i]
                    if T < s:
                        continue
                    # letters appear over the first 80 % of the word, at least 1 letter
                    m = len(w) if T >= s + (e - s) * 0.8 else max(1, int(len(w) * (T - s) / max(1e-3, (e - s) * 0.8)))
                    col = hi if s <= T < e else ink
                    text(img, x0 + 6 + x, y, w[:m], col)
        return np.array(img)
    return overlay


def timeline(plan):
    """Builds the Timeline for the current format (frame.use). Returns (timeline, marks):
    marks are (time, label) for the storyboard."""
    prepare(plan)
    carry(plan)
    times = durations(plan)
    scenes, marks = [], []
    plan.pop("_world", None)
    for si, (sc, (a, b)) in enumerate(zip(plan["scenes"], times)):
        ctx = {"si": si}
        painter = PAINTERS[sc["type"]]
        dur = b - a
        scenes.append((a, b, lambda t, sc=sc, dur=dur, ctx=ctx, painter=painter: painter(plan, sc, t, dur, ctx),
                       sc.get("fade", True) and not sc.get("continue")))
        key = a + min(dur - 0.3, max(1.2, dur * float(sc.get("key", 0.75))))
        marks.append((key, f"{sc['id']} {sc['type']} {a:.1f}-{b:.1f}s"))
    over = [o for o in (_timebar(plan, times), subtitles(plan, times)) if o]

    def overlay(arr, T):
        for o in over:
            arr = o(arr, T)
        return arr
    return Timeline(scenes, overlay=overlay if over else None, fade_col=plan.get("fade_color", PAPER)), marks


def _timebar(plan, times):
    """overlay(arr, T) for Timeline: the timeline strip, over the dissolve; hidden in title and summary
    scenes and in a scene with timeline: false."""
    if not TIMEBAR:
        return None
    from PIL import Image
    import numpy as np
    L = layout()
    evs = timebar.events(plan, times)
    off = [(a, b) for sc, (a, b) in zip(plan["scenes"], times)
           if sc.get("type") in ("title", "summary") or sc.get("timeline") is False]

    def overlay(arr, T):
        if any(a <= T < b for a, b in off):
            return arr
        img = Image.fromarray(arr)
        timebar.draw(img, plan, L, evs, T, color=color)
        return np.array(img)
    return overlay
