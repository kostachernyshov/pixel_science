# explainer.yaml -> Timeline, for each video format and style. The agent writes the plan; this module draws it.
# The plan format is in .agents/skills/animate/PLAN.md. Paths in the plan are relative to the plan file.
#
#   from pixel_kit import explain, frame
#   plan = explain.load("my-video/explainer.yaml")
#   explain.prepare(plan, style="arcade")     # packs and style of the plan (or another style)
#   problems, warnings = explain.check(plan)  # rules: sources, sprites, words, captions, pace
#   frame.use("vertical")
#   tl, marks = explain.timeline(plan)        # marks: key times for the storyboard
#
# Scene types: title, cast, action, contact, fact, flow, summary, custom.
# Layout is relative to the frame, so one plan renders in every format of frame.FORMATS.
# Timing comes from words (words.py): the voice-over text at 2.7 words/s, or a recording.

import importlib.util, os, re
from PIL import ImageDraw
from .palette import *
from .font import text, text_w, title_text, TITLE_GLYPHS, LINE
from .timing import clamp, seg, ease, lerp
from . import sprites as S, fx, ui, bg, voice, frame, words, gen, camera, style, packs, contact, mechanism
from .scene import Timeline

TYPES = ("title", "cast", "action", "contact", "fact", "flow", "summary", "custom")
COLOR_NAMES = {
    "favorable": FAVORABLE[0], "favorable2": FAVORABLE[1], "favorable3": FAVORABLE[2],
    "unfavorable": UNFAVORABLE[0], "unfavorable2": UNFAVORABLE[1], "unfavorable3": UNFAVORABLE[2],
    "neutral": NEUTRAL[0], "neutral2": NEUTRAL[1], "neutral3": NEUTRAL[2],
    "ink": (INK, INK), "navy": (ACCENT, ACCENT), "accent": (ACCENT, ACCENT),
}
TIMED = ("beats", "swarm", "grow", "field", "camera")     # lists whose items take t or on


# ---------------------------------------------------------------- plan, voice-over, timing

def _yaml_loader():
    """YAML with only true/false as booleans: "on", "off", "yes", "no" stay words (on: attacks, on: off)."""
    import re as _re, yaml

    class Loader(yaml.SafeLoader):
        pass
    Loader.yaml_implicit_resolvers = {k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:bool"]
                                      for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
    Loader.add_implicit_resolver("tag:yaml.org,2002:bool", _re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
                                 list("tTfF"))
    return Loader


def load(path):
    import yaml
    plan = yaml.load(open(path, encoding="utf-8"), Loader=_yaml_loader())
    plan["_dir"] = os.path.dirname(os.path.abspath(path))
    plan["_path"] = os.path.abspath(path)
    plan.setdefault("scenes", [])
    plan.setdefault("lang", "en")
    plan.setdefault("formats", list(frame.FORMATS))
    plan.setdefault("style", style.BASE_NAME)
    return plan


def prepare(plan, style_name=None):
    """Sets the plan's packs (bottom -> top) and its style (or style_name)."""
    S.use(plan.get("packs") or [p.name for p in sorted(packs.content(), key=lambda p: p.name)])
    style.use(style_name or plan.get("style") or style.BASE_NAME)


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


def audio_path(plan):
    p = path(plan, (plan.get("voice") or {}).get("audio"))
    return p if p and os.path.exists(p) else None


def transcript_path(plan):
    v = plan.get("voice") or {}
    p = path(plan, v.get("transcript"))
    if p:
        return p
    a = path(plan, v.get("audio"))
    return os.path.splitext(a)[0] + ".words.json" if a else None


def spoken_words(plan):
    """Words of the recording [(word, start, end)], or None without a transcript."""
    tr = transcript_path(plan)
    if tr and os.path.exists(tr):
        v = plan.get("voice") or {}
        return voice.words(tr, float(v.get("start", 0.0)), v.get("end"))
    return None


def timing(plan):
    """Per scene: start, end, words [(word, t)], drift. Cached in the plan."""
    if "_timing" not in plan:
        plan["_timing"] = words.timing(plan["scenes"], voiceover(plan), spoken_words(plan))
        _resolve(plan)
    return plan["_timing"]


def durations(plan):
    return [(s["start"], s["end"]) for s in timing(plan)]


def _resolve(plan):
    """Gives each timed item (beat, generator, camera move) "_t": seconds from the scene start.
    "on: attacks" is the time of that word, plus "offset"."""
    probs = plan["_resolve_problems"] = []
    for sc, tm in zip(plan["scenes"], plan["_timing"]):
        for key in TIMED:
            for it in sc.get(key) or []:
                if "on" in it:
                    w = words.at(tm, str(it["on"]))
                    if w is None:
                        probs.append(f"{sc.get('id')}: {key} 'on: {it['on']}' is not a word of its voice-over")
                        it["_t"] = 0.0
                    else:
                        it["_t"] = max(0.0, w - tm["start"] + float(it.get("offset", 0.0)))
                else:
                    it["_t"] = float(it.get("t", 0.0))


def color(name):
    if isinstance(name, (list, tuple)):
        return tuple(name)
    if name not in COLOR_NAMES:
        raise KeyError(f"unknown color {name!r}; use one of {', '.join(COLOR_NAMES)}")
    return COLOR_NAMES[name]


# ---------------------------------------------------------------- layout for the current format

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
    return dict(W=W, H=H, tall=tall, banner=banner, cap_scale=cap_scale, cap_y=cap_y,
                head_h=head_h, stage=(0, head_h, W, cap_y - 4), sprite_scale=2)


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
    sw, sh = S.cell(name)
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


def _sprites(sc, plan=None):
    for key in ("items", "steps"):
        for it in sc.get(key) or []:
            yield it.get("sprite"), it.get("anim", "idle")
    for a in (sc.get("actors") or {}).values():
        yield a.get("sprite"), a.get("anim", "idle")
        if a.get("badge"):
            yield a["badge"], "idle"
    if sc.get("type") == "contact" and plan is not None:
        things, _ = mechanism.model(plan)
        for side in ("left", "right"):
            sp = (things.get(sc.get(side)) or {}).get("sprite")
            if sp:
                yield sp, "idle"
                for b in sc.get("beats") or []:
                    if b.get("cell") == side and b.get("anim"):
                        yield sp, b["anim"]


def check(plan):
    """Rules of the skill. Returns (problems, warnings). Problems stop a render; warnings go to the person."""
    out, warn = [], []
    if not plan.get("sources"):
        out.append("sources: list at least one source for the science in the video")
    vo = voiceover(plan)
    if not vo:
        out.append(f"voiceover not found or empty: {plan.get('voiceover')}")
    for f in plan.get("formats") or []:
        if f not in frame.FORMATS:
            out.append(f"formats: unknown format {f!r}; use {', '.join(frame.FORMATS)}")
    try:
        prepare(plan, style.current().name)
    except (packs.PackError, KeyError, ValueError) as e:
        return [str(e)], warn
    tm = timing(plan)
    out += plan.get("_resolve_problems", [])
    times = [(s["start"], s["end"]) for s in tm]
    seen = set()
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
        for name, anim in _sprites(sc, plan):
            if name not in meta:
                out.append(f"{sid}: unknown sprite {name!r} (find one: pixsci find <word>)")
            elif anim not in meta[name]["anims"]:
                out.append(f"{sid}: sprite {name} has no animation {anim!r}; it has {', '.join(meta[name]['anims'])}")
        if sc.get("bg", "paper") not in bg.names():
            out.append(f"{sid}: unknown background {sc.get('bg')!r}; backgrounds: {', '.join(bg.names())}")
        for key in ("items", "steps"):
            if len(sc.get(key) or []) > 4:
                out.append(f"{sid}: {key} has more than 4 entries (they do not fit a vertical frame)")
        actors = sc.get("actors") or {}
        for beat in sc.get("beats") or [] if typ != "contact" else []:
            if beat.get("actor") not in actors:
                out.append(f"{sid}: beat {beat.get('on', beat.get('t'))} names an unknown actor {beat.get('actor')!r}")
        for key in ("swarm", "field", "camera", "grow"):
            for it in sc.get(key) or []:
                for f in ("target", "drag", "at", "pan_to"):
                    v = it.get(f)
                    if isinstance(v, str) and v not in (actors if typ != "contact" else ("left", "right", "gap")):
                        out.append(f"{sid}: {key} {f}: {v!r} is not an actor of the scene")
        cap = sc.get("caption")
        if cap and len(cap.split()) > 3:
            out.append(f"{sid}: caption has {len(cap.split())} words (max 3): {cap!r}")
        if cap and b - a < 2.0:
            out.append(f"{sid}: caption is on screen {b - a:.1f} s (min 2 s)")
        for f, s in _texts(sc):
            if plan.get("lang") == "en" and not s.isascii():
                out.append(f"{sid}: {f} is not plain English text (lang: en): {s!r}")
            for num in re.findall(r"(?<![A-Za-z0-9-])\d[\d.,]*", s):
                if not _sourced(plan, num):
                    warn.append(f"{sid}: number {num!r} on screen ({f}): is it from a source? "
                                f"If yes, list it under 'numbers:' with its source")
        for key, field in (("swarm", "n"), ("grow", "max"), ("field", "n")):
            for it in sc.get(key) or []:
                if field in it:
                    warn.append(f"{sid}: {key} {field}={it[field]} is a schematic count (invented, not on screen)")
        if typ == "title":
            for ch in (sc.get("title") or "").upper():
                if ch not in TITLE_GLYPHS:
                    out.append(f"{sid}: title character {ch!r} is not in the title font (A-Z, 0-9, - ! . ? :)")
        if typ == "fact" and len(sc.get("text") or []) > 3:
            out.append(f"{sid}: a fact has 3 lines of text or fewer")
    # text must fit in each format
    for f in plan.get("formats") or []:
        if f not in frame.FORMATS:
            continue
        frame.use(f)
        L = layout()
        for sc in plan["scenes"]:
            cap = sc.get("caption")
            if cap:
                k, lines = fit_text(cap, L["W"] - 16, (L["cap_scale"], 1), max_lines=1 if L["banner"] else 2)
                if len(lines) > (1 if L["banner"] else 2):
                    out.append(f"{sc.get('id')}: caption {cap!r} does not fit the {f} frame")
    frame.use("landscape")
    out += mechanism.check(plan)
    if not plan["scenes"] or plan["scenes"][-1].get("type") != "summary":
        out.append("the last scene must be a summary")
    from . import pace
    p2, w2 = pace.check(plan)
    out += p2
    warn += w2
    for line in words.drift_report(tm):
        warn.append("voice: " + line)
    return out, warn


def _sourced(plan, num):
    nums = plan.get("numbers") or {}
    keys = nums.keys() if isinstance(nums, dict) else nums
    return any(num.strip(".,") in str(k) for k in keys)


# ---------------------------------------------------------------- shared drawing

def _bg(sc, t):
    return bg.get(sc.get("bg", "paper"), t)


def _heading(img, L, s):
    if s and not L["banner"]:
        k, lines = fit_text(s, L["W"] - 24, (1,), max_lines=1)
        text(img, 12, 8, lines[0], ACCENT)
        ImageDraw.Draw(img).line([12, 26, 12 + text_w(lines[0]), 26], fill=C(ACCENT))


def _caption(img, L, sc, t):
    cap = sc.get("caption")
    if not cap or t < 0.3:
        return
    k, lines = fit_text(cap, L["W"] - 16, (L["cap_scale"], 1), max_lines=1 if L["banner"] else 2)
    lh = LINE * k + 2
    y = L["cap_y"] - (len(lines) - 1) * lh
    d = ImageDraw.Draw(img)
    w = max(text_w(s, k) for s in lines)
    cx = L["W"] // 2
    d.rectangle([cx - w // 2 - 6, y - 3, cx + w // 2 + 6, y + lh * len(lines) - 1], fill=C(PLATE))
    for i, s in enumerate(lines):
        text(img, cx, y + lh * i, s, PLATE_INK, scale=k, align="c")


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
    pts, cw, ch = grid(n, box, L["tall"])
    # one scale for all items, so that sizes compare
    common = min([best_scale(it["sprite"], cw, ch, room=22 if labels else 4, top=2 if L["banner"] else 4)
                  for it in items] or [1])
    # labels of one row stand on one line, under the tallest sprite of the row
    row_h = {}
    for it, (x, y) in zip(items, pts):
        row_h[y] = max(row_h.get(y, 0), S.cell(it["sprite"])[1] * int(it.get("scale") or common))
    for i, (it, (x, y)) in enumerate(zip(items, pts)):
        ti = t0 + step * i
        if t < ti and not still:
            continue
        k = int(it.get("scale") or common)
        cy = y - (9 if labels and it.get("label") else 0)
        _sprite(img, it["sprite"], it.get("anim", "idle"), 0.0 if still else t - ti, x, cy, k, seed=i)
        if labels and it.get("label"):
            _label(img, x, cy + row_h[y] // 2 + 3, it["label"], color(it.get("color", "ink"))[0], cw - 4)
    return pts


# ---------------------------------------------------------------- scene painters

def p_title(plan, sc, t, dur, ctx):
    img = bg.get("paper")
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
    y = int(lerp(-th - 10, top, ease(seg(t, 0, 0.6)))) - (int(t * 2) % 2 if t > 0.6 else 0)
    title_text(img, W // 2, y, s, k, XBLUE, ACCENT, back=LGREY)
    if sub and t > 0.5:
        for i, ln in enumerate(sub):
            text(img, W // 2, top + th + 12 + i * LINE * sub_k, ln, INK, scale=sub_k, align="c")
    if sc.get("credit") and t > 0.8 and not L["banner"]:
        text(img, W // 2, H - 26, sc["credit"], DIM, align="c")
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
            sw = S.cell(st["sprite"])[0] * k
            _sprite(img, st["sprite"], st.get("anim", "idle"), t - ti, x - sw // 2 - 4, y, k, seed=i)
            k2, lines = fit_text(st.get("label", ""), L["W"] // 2 - 12, (1,), max_lines=2)
            for j, ln in enumerate(lines):
                text(img, x + 6, y - LINE * len(lines) // 2 + LINE * j, ln, INK)
            if i + 1 < n and t > ti + step_t * 0.6:
                _arrow(d, x, int(y + ch / 2 - 6), x, int(y + ch / 2 + 6), DIM)
        else:
            k = int(st.get("scale") or best_scale(st["sprite"], cw - 24, ch, room=22, top=2 if L["banner"] else 3))
            sh = S.cell(st["sprite"])[1] * k
            sw = S.cell(st["sprite"])[0] * k
            cy = y - 9
            _sprite(img, st["sprite"], st.get("anim", "idle"), t - ti, x, cy, k, seed=i)
            _label(img, x, cy + sh // 2 + 3, st.get("label", ""), INK, cw - 8)
            if i + 1 < n and t > ti + step_t * 0.6:
                xa = int(x + max(sw // 2 + 4, cw * 0.32))
                xb = int(pts[i + 1][0] - max(sw // 2 + 4, cw * 0.32))
                if xb - xa >= 8:
                    _arrow(d, xa, cy, xb, cy, DIM)
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
        ty = sy + (S.cell(name)[1] * k // 2 + 10 if name else 0)
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
            text(img, tx, y, ln[:k_vis], ACCENT if i == 0 else INK, scale=kk, align=align)
            y += LINE * kk
        y += 6
    _caption(img, L, sc, t)
    return img


def _actor_state(a, beats, name, t):
    """Position (fractions of the stage), sprite, animation, the time in that animation, flip, badge,
    shown, hold (a fixed frame of the animation, or None)."""
    x, y = a.get("at", [0.5, 0.5])
    sprite, anim, a_t0, hold = a["sprite"], a.get("anim", "idle"), 0.0, a.get("hold")
    flip, badge, shown = bool(a.get("flip", False)), a.get("badge"), not a.get("hidden", False)
    for b in sorted((b for b in beats if b.get("actor") == name), key=lambda b: b["_t"]):
        bt = b["_t"]
        if t < bt:
            break
        if "move_to" in b:
            d = float(b.get("dur", 1.0))
            k = ease(seg(t, bt, bt + d))
            tx, ty = b["move_to"]
            x, y = lerp(x, tx, k), lerp(y, ty, k)
        if "sprite" in b:
            sprite = b["sprite"]
        if "anim" in b:
            anim, a_t0, hold = b["anim"], bt, b.get("hold")
        if "flip" in b:
            flip = bool(b["flip"])
        if "badge" in b:
            badge = b["badge"]
        if "show" in b:
            shown = bool(b["show"])
    return dict(x=x, y=y, sprite=sprite, anim=anim, at=t - a_t0, flip=flip, badge=badge, shown=shown, hold=hold)


def _stage_px(L, fx_, fy_):
    x0, y0, x1, y1 = L["stage"]
    return int(x0 + fx_ * (x1 - x0)), int(y0 + fy_ * (y1 - y0))


def p_action(plan, sc, t, dur, ctx):
    """Actors on a stage, timed beats, generators (swarm, grow, field), effects, and a camera.
    Positions are fractions of the stage (0..1), so the scene fits every format."""
    img = _bg(sc, t)
    L = layout()
    actors = sc.get("actors") or {}
    beats = sc.get("beats") or []
    seed = int(sc.get("seed", plan.get("seed", 1)))

    def actor_xy(name, tt):
        st = _actor_state(actors[name], beats, name, tt)
        return st["x"], st["y"]

    def target(v, tt):
        """Stage fractions of an actor name or [x, y]."""
        return actor_xy(v, tt) if isinstance(v, str) else (float(v[0]), float(v[1]))

    def target_px(v):
        return lambda tt: _stage_px(L, *target(v, tt))

    for i, g in enumerate(sc.get("field") or []):
        gen.draw_field(img, g, t, L["stage"], target_px(g.get("drag") or g.get("at") or [0.5, 0.5]), seed + i)
    k_default = int(sc.get("scale", L["sprite_scale"]))
    for g in sc.get("grow") or []:
        g["_at"] = target(g.get("at", [0.5, 0.5]), t)
        for (gx, gy, name, anim, at) in gen.grow_state(g, t):
            px, py = _stage_px(L, gx, gy)
            _sprite(img, name, anim, at, px, py, int(g.get("scale", k_default)), seed=int(gx * 97))
    for i, (name, a) in enumerate(actors.items()):
        st = _actor_state(a, beats, name, t)
        if not st["shown"]:
            continue
        k = int(a.get("scale", k_default))
        px, py = _stage_px(L, st["x"], st["y"])
        if st["hold"] is not None:
            # a held frame still breathes: a 1 px bob, like an idle animation
            bob = (int((t + i * 0.17) * 3) % 2) * k
            S.draw(img, st["sprite"], st["anim"], 0, px, py - bob, flip=st["flip"], scale=k, i=int(st["hold"]))
        else:
            _sprite(img, st["sprite"], st["anim"], st["at"], px, py, k, seed=i, flip=st["flip"])
        sh = S.cell(st["sprite"])[1] * k
        badge = st["badge"]
        if badge:
            # the badge stands on the top of the body, a little into it
            by = py - S.body_top(st["sprite"]) * k - (S.body_top(badge) - 1) * k + k
            S.draw(img, badge, "idle", 0, px, max(S.body_top(badge) * k + 1, by), scale=k)
        if a.get("label") and not L["banner"]:
            text(img, px, py + sh // 2 + 2, a["label"], color(a.get("color", "ink"))[0], align="c")
    for i, g in enumerate(sc.get("swarm") or []):
        members = gen.swarm_state(g, t, lambda tt, v=g.get("target", [0.5, 0.5]): target(v, tt), seed + 100 + i)
        for j, (gx, gy, name, anim, at, flip) in enumerate(members):
            px, py = _stage_px(L, gx, gy)
            _sprite(img, name, anim, at, px, py, int(g.get("scale", 1)), seed=j, flip=flip)
    for b in beats:
        bt = b["_t"]
        if not b.get("fx") or t < bt or b.get("actor") not in actors:
            continue
        px, py = _stage_px(L, *actor_xy(b["actor"], t))
        if b.get("dur") is not None and "move_to" not in b and t > bt + float(b["dur"]):
            continue
        if b["fx"] == "hit":
            fx.hit_flash(img, px, py, t - bt)
        elif b["fx"] == "alert" and t - bt < 1.2:
            fx.alert(img, px, py - 30, t - bt)
        elif b["fx"] == "sparkle" and t - bt < 1.0:
            fx.sparkle(img, px, py - 20, t - bt)
        elif b["fx"] == "particles":
            fx.particles(img, px, py, t - bt, seed=int(bt * 10))
        elif b["fx"] == "wave":
            fx.wave(img, px, py, t - bt)
        elif b["fx"] == "zzz":
            fx.zzz(img, px, py, t - bt)
        elif b["fx"] == "flash" and t - bt < 0.2:
            fx.border_flash(img, top=0, col=ACCENT)
    cams = sc.get("camera") or []
    if cams:
        z, cx, cy, dx, dy = camera.state(cams, t, lambda v, tt: _stage_px(L, *target(v, tt)))
        img = camera.apply(img, z, cx, cy, dx, dy, fill=C(PAPER))
    _heading(img, L, sc.get("title"))
    _caption(img, L, sc, t)
    return img


def p_contact(plan, sc, t, dur, ctx):
    """Two bodies face to face, their parts on stalks, drawn from the plan's mechanism model (contact.py).
    The scene starts in the state the last scene left."""
    img = _bg(sc, t)
    L = layout()
    if "_start" not in ctx:
        i = plan["scenes"].index(sc)
        ctx["_start"] = mechanism.world(plan)[i]
    cams = sc.get("camera") or []
    z = 1
    if cams:
        z, cx, cy, dx, dy = camera.state(cams, t, lambda v, tt: _stage_px(L, *v) if not isinstance(v, str)
                                         else contact.where(plan, sc, L, v))
    # labels only in the wide shot: a close-up would cut them and push them under the caption
    contact.draw(img, plan, sc, t, L, ctx["_start"], labels=z == 1)
    if cams:
        img = camera.apply(img, z, cx, cy, dx, dy, fill=C(PAPER))
    _heading(img, L, sc.get("title"))
    _caption(img, L, sc, t)
    return img


def p_summary(plan, sc, t, dur, ctx):
    """The last frame: a heading, up to 4 sprites with labels, and 1 or 2 lines of conclusion.
    It appears in about 1.5 s and then holds still."""
    img = bg.get("plain")
    L = layout()
    W, H = L["W"], L["H"]
    _heading(img, L, sc.get("title") or plan.get("title"))
    lines = sc.get("text") or []
    lines = [lines] if isinstance(lines, str) else lines
    fitted = [_one_line(s, W - 20, (1,) if L["banner"] else (2, 1)) for s in lines]
    text_h = sum(len(ww) * LINE * kk + 4 for kk, ww in fitted)
    x0, y0, x1, y1 = 0, L["head_h"], W, H - text_h - (int(H * 0.2) if L["tall"] else 8)
    if L["banner"]:
        # one low row: sprites on the left half, conclusion on the right half
        _items(img, L, sc.get("items") or [], t, (0, 4, W // 2, H - 4), t0=0.2, step=0.2, labels=False)
        y = H // 2 - text_h // 2
        for kk, ww in (fit_text(s, W // 2 - 16, (1,), max_lines=2) for s in lines):
            if t >= 1.0:
                for ln in ww:
                    text(img, W * 3 // 4, y, ln, ACCENT, scale=kk, align="c")
                    y += LINE * kk
        return img
    _items(img, L, sc.get("items") or [], t, (x0, y0, x1, y1), t0=0.2, step=0.2)
    if t >= 1.2:
        y = y1 + 4
        for i, (kk, ww) in enumerate(fitted):
            for ln in ww:
                text(img, W // 2, y, ln, ACCENT if i == 0 else INK, scale=kk, align="c")
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
    fn(img, t, sc, dict(ctx, plan=plan, layout=L, dur=dur))
    _caption(img, L, sc, t)
    return img


PAINTERS = {k[2:]: v for k, v in globals().items() if k.startswith("p_")}


# ---------------------------------------------------------------- timeline

def timeline(plan):
    """Builds the Timeline for the current format (frame.use) and style. Returns (timeline, marks):
    marks are (time, label) for the storyboard."""
    times = durations(plan)
    scenes, marks = [], []
    for sc, (a, b) in zip(plan["scenes"], times):
        ctx = {}
        painter = PAINTERS[sc["type"]]
        dur = b - a
        scenes.append((a, b, lambda t, sc=sc, dur=dur, ctx=ctx, painter=painter: painter(plan, sc, t, dur, ctx),
                       sc.get("fade", True)))
        key = a + min(dur - 0.3, max(1.2, dur * float(sc.get("key", 0.75))))
        marks.append((key, f"{sc['id']} {sc['type']} {a:.1f}-{b:.1f}s"))
    return Timeline(scenes), marks
