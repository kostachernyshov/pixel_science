# Pace rules (pixsci check):
#   - a shot changes every 2 to 4 s: a scene, a camera cut (zoom) or a pan starts a shot
#   - in an action or contact scene something new happens at least every 1.5 s (a beat, a generator, the camera)
#   - something moves in every frame (motion(): renders the video small and compares frames)
#   - the final frame holds 3 s; the story lasts 20 to 60 s
#   - the voice-over goes at about 2.7 words/s (with a recording: warn above 3.5 words/s)

from . import camera, gen, words

SHOT_MIN, SHOT_MAX = 2.0, 4.0
ACTION_GAP = 1.5
SLACK = 0.15
STILL_MAX = 0.5          # s without any change in the picture
MAX_RATE = 3.5


def _events(sc):
    """Points and intervals (s from the scene start) when something new happens in an action scene."""
    pts, spans = [0.0], []
    for b in sc.get("beats") or []:
        pts.append(b["_t"])
        if "move_to" in b:
            spans.append((b["_t"], b["_t"] + float(b.get("dur", 1.0))))
        if "do" in b or "undo" in b:
            spans.append((b["_t"], b["_t"] + 0.6))
    for g in sc.get("swarm") or []:
        pts.append(g["_t"])
        if g.get("rule", "wander") in ("seek", "flee"):
            spans.append((g["_t"], g["_t"] + float(g.get("dur", 1.2)) + float(g.get("stagger", 0.08)) * int(g.get("n", 8))))
    for g in sc.get("grow") or []:
        spans.append((g["_t"], gen.grow_end(g)))
    for g in sc.get("field") or []:
        pts.append(g["_t"])
        if g.get("kind") == "gradient" or g.get("appear"):
            spans.append((g["_t"], g["_t"] + float(g.get("dur", 1.5))))
    for c in sc.get("camera") or []:
        pts.append(c["_t"])
        if "pan_to" in c:
            spans.append((c["_t"], c["_t"] + float(c.get("dur", 0.8))))
        if "shake" in c:
            spans.append((c["_t"], c["_t"] + float(c["shake"])))
    return pts, spans


def _gaps(pts, spans, end):
    """Longest stretches in [0, end] that no point or interval touches."""
    covered = sorted([(p, p) for p in pts] + spans)
    out, cur = [], 0.0
    for a, b in covered:
        if a > cur:
            out.append((cur, a))
        cur = max(cur, b)
    if end > cur:
        out.append((cur, end))
    return out


def check(plan):
    from .explain import timing
    probs, warn = [], []
    tm = timing(plan)
    scenes = plan["scenes"]
    for i, (sc, s) in enumerate(zip(scenes, tm)):
        sid, typ = sc.get("id", "?"), sc.get("type")
        d = s["end"] - s["start"]
        last = i == len(scenes) - 1
        if typ == "summary":
            if last and d < words.SUMMARY_IN + words.FINAL_HOLD - SLACK:
                probs.append(f"{sid}: the final frame holds {d - words.SUMMARY_IN:.1f} s (min {words.FINAL_HOLD:.0f} s)")
            continue
        if d < SHOT_MIN - SLACK:
            probs.append(f"{sid}: scene lasts {d:.1f} s (a shot is {SHOT_MIN:.0f} to {SHOT_MAX:.0f} s)")
        cuts = [0.0] + [c for c in camera.shots(sc.get("camera") or []) if 0 < c < d] + [d]
        for a, b in zip(cuts, cuts[1:]):
            if b - a > SHOT_MAX + SLACK:
                probs.append(f"{sid}: one shot runs {a:.1f}-{b:.1f} s ({b - a:.1f} s, max {SHOT_MAX:.0f} s): "
                             f"add a camera move (zoom, pan) or split the scene")
        if typ in ("action", "contact"):
            pts, spans = _events(sc)
            for a, b in _gaps(pts, spans, d):
                if b - a > ACTION_GAP + SLACK:
                    probs.append(f"{sid}: nothing new from {a:.1f} to {b:.1f} s (max {ACTION_GAP} s): "
                                 f"add a beat, a generator, or a camera move")
        if s.get("drift") and len(s["words"]) > 3:
            span = s["words"][-1][1] - s["words"][0][1]
            if span > 0 and len(s["words"]) / span > MAX_RATE:
                warn.append(f"{sid}: the voice goes at {len(s['words']) / span:.1f} words/s (aim at {words.WORDS_PER_S})")
    story = (tm[-2]["end"] if len(tm) > 1 and scenes[-1].get("type") == "summary" else tm[-1]["end"]) if tm else 0
    limit = float(plan.get("max_s", 60))
    if story > limit:
        probs.append(f"length before the summary {story:.0f} s: keep it at 20-60 s ({limit:.0f} s at most, max_s)")
    elif story < 20:
        warn.append(f"length before the summary {story:.0f} s: a video is usually 20 to 60 s")
    return probs, warn


def motion(plan, fmt="landscape", fps=10):
    """Renders the video at fps (small frames) and finds still stretches longer than STILL_MAX s
    before the final hold. Returns problems."""
    import numpy as np
    from . import frame
    from .explain import timeline, timing
    frame.use(fmt)
    tl, _ = timeline(plan)
    tm = timing(plan)
    hold_from = tm[-1]["start"] + words.SUMMARY_IN if plan["scenes"][-1].get("type") == "summary" else tl.duration
    out, prev, still_from = [], None, None
    n = int(hold_from * fps)
    for i in range(n + 1):
        t = i / fps
        cur = tl.frame(t)
        if prev is not None and np.array_equal(cur, prev):
            if still_from is None:
                still_from = (i - 1) / fps
        else:
            if still_from is not None and t - still_from > STILL_MAX + 1e-6:
                out.append(_where(tm, plan, still_from, t))
            still_from = None
        prev = cur
    if still_from is not None and hold_from - still_from > STILL_MAX + 1e-6:
        out.append(_where(tm, plan, still_from, hold_from))
    return out


def _where(tm, plan, a, b):
    for sc, s in zip(plan["scenes"], tm):
        if s["start"] <= a < s["end"]:
            return f"{sc.get('id')}: the picture stands still from {a - s['start']:.1f} to {b - s['start']:.1f} s"
    return f"the picture stands still from {a:.1f} to {b:.1f} s"
