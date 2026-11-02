# UI kit for the light theme: frames, top bar, chapter banner, character cards, pips and meters
# without numbers, results table, HYPOTHESIS frame, status labels, captions.
# Sizes read the current frame (frame.W, frame.H). Text is INK on PAPER, or PAPER on a dark plate.

from PIL import ImageDraw
from .palette import *
from .font import text, text_w, title_text
from .timing import clamp, seg, ease, lerp
from . import sprites as S, frame



def box(d, x0, y0, x1, y1, fill=PAPER, border=INK, inner=LGREY):
    """RPG-style frame: fill, outer line, inner line 2 px inside."""
    d.rectangle([x0, y0, x1, y1], fill=C(fill))
    d.rectangle([x0, y0, x1, y1], outline=C(border))
    if inner is not None:
        d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], outline=C(inner))


def hud(img, title, middle="", status=None):
    """Top bar 18 px: title on the left, a step in the middle, status on the right.
    status = (sprite, anim, frame, label, color) or None."""
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, frame.W - 1, 17], fill=C(NAVY))
    text(img, 6, 1, title, WHITE)
    if middle:
        text(img, frame.W // 2, 1, middle, LGREY, align="c")
    if status:
        spr, anim, i, label, col = status
        tx = frame.W - 6 - text_w(label)
        S.draw(img, spr, anim, 0, tx - 12, 9, i=i)
        text(img, tx, 1, label, col)


def chapter_banner(img, t, label, sub=""):
    """Chapter screen ("DESIGN", "RESULT"): the label slides in from the right. t: time from start."""
    img.paste(C(PAPER), (0, 0, frame.W, frame.H))
    k = ease(seg(t, 0, 0.25))
    x = int(lerp(frame.W + 160, frame.W // 2, k))
    text(img, x, 96, label, NAVY, scale=3, align="c", shadow=LGREY)
    if sub and t > 0.3:
        text(img, frame.W // 2, 154, sub, DGREY, scale=2, align="c")


def title_screen(img, t, title, sub=None, credit=None):
    """Title: the title (5x7 font) drops from the top, then the subtitle."""
    y = int(lerp(-60, 70, ease(seg(t, 0, 0.6))))
    k = 6 if len(title) <= 12 else (5 if len(title) <= 15 else 4)
    title_text(img, frame.W // 2, y, title, k, XBLUE, NAVY, back=LGREY)
    if sub and t > 0.5:
        text(img, frame.W // 2, 140, sub, INK, scale=2 if text_w(sub, 2) < frame.W - 40 else 1, align="c")
    if credit and t > 0.8:
        text(img, frame.W // 2, 190, credit, DGREY, align="c")


def card(img, x0, y0, title, col):
    """Empty character card 145x169: portrait window and name."""
    d = ImageDraw.Draw(img)
    box(d, x0, y0, x0 + 144, y0 + 168, fill=PAPER, border=col, inner=LGREY)
    d.rectangle([x0 + 8, y0 + 10, x0 + 136, y0 + 84], fill=(246, 236, 228))
    text(img, x0 + 72, y0 + 90, title, col, align="c")


def character_card(img, x0, y0, t, sprite, title, col, role=None, anim="idle", flip=False):
    """Card with a portrait: the same sprite x3, name, and role (1-2 words)."""
    card(img, x0, y0, title, col)
    S.idle(img, sprite, t, x0 + 72, y0 + 47, scale=3, flip=flip) if anim == "idle" else \
        S.draw(img, sprite, anim, t, x0 + 72, y0 + 47, scale=3, flip=flip)
    if role:
        text(img, x0 + 72, y0 + 118, role, INK, align="c")


def pips(img, x, y, n, total=8, on=XBLUE, off=LGREY, w=5, h=8, gap=2):
    """Pips without numbers (a level, "how much is left")."""
    d = ImageDraw.Draw(img)
    for k in range(total):
        d.rectangle([x + k * (w + gap), y, x + k * (w + gap) + w - 1, y + h - 1], fill=C(on if k < n else off))


def meter(img, x, y, k, w=60, h=6, col=XBLUE, back=LGREY):
    """Solid bar 0..1 without numbers (only "more" or "less")."""
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=C(back))
    if k > 0:
        d.rectangle([x, y, x + int((w - 1) * clamp(k)), y + h - 1], fill=C(col))


def status(img, x, y, label, col=NAVY, scale=2):
    """Large status label over a scene (centered on x), with a PAPER halo."""
    text(img, x, y, label, col, scale=scale, align="c", outline=True, shadow=PAPER)


def caption(img, s, y=232, scale=2, col=WHITE, plate=NAVY):
    """Large caption at the bottom on a dark plate. Rule: 2-3 words, on screen for >= 2 s."""
    d = ImageDraw.Draw(img)
    w = text_w(s, scale)
    d.rectangle([frame.W // 2 - w // 2 - 6, y - 3, frame.W // 2 + w // 2 + 6, y + 16 * scale + 1], fill=C(plate))
    text(img, frame.W // 2, y, s, col, scale=scale, align="c")


def panel_frame(img, x0, y0, w, h, label, col):
    """Panel frame with a header (side-by-side comparison)."""
    d = ImageDraw.Draw(img)
    d.rectangle([x0 - 2, y0 - 2, x0 + w + 1, y0 + h + 1], outline=C(DGREY))
    d.rectangle([x0, y0, x0 + w - 1, y0 + 17], fill=C(col))
    text(img, x0 + w // 2, y0 + 1, label, WHITE, align="c")


def results_table(img, t, x0, y0, x1, cols, rows, row_h=24, step=0.45, t0=0.3):
    """Results table: cols = [(x, sprite, label, color)], rows = [(label, [(text, color), ...])].
    The rows appear one by one every step seconds."""
    d = ImageDraw.Draw(img)
    for (x, spr, lab, col) in cols:
        if spr:
            S.draw(img, spr[0], spr[1], 0, x + 2, y0 + 18, i=spr[2])
        text(img, x + 16, y0 + 10, lab, col)
    d.line([x0 + 10, y0 + 32, x1 - 10, y0 + 32], fill=C(DGREY))
    for r, (lab, cells) in enumerate(rows):
        if t < t0 + step * r:
            continue
        y = y0 + 40 + row_h * r
        text(img, x0 + 12, y, lab, INK)
        for (x, _, _, _), (s, col) in zip(cols, cells):
            text(img, x, y, s, col)


def hypothesis(img, t, y0, title, lines, x0=10, x1=None, y1=None, col=XORANGE, cps=60):
    """HYPOTHESIS frame: everything in it is an assumption, not an observation.
    The text types letter by letter (cps characters per second)."""
    x1 = x1 or frame.W - 11
    d = ImageDraw.Draw(img)
    box(d, x0, y0, x1, y1 or y0 + 34 + 18 * len(lines), fill=PAPER, border=col, inner=LGREY)
    text(img, x0 + 12, y0 + 8, title, BROWN)
    n = int(max(0, t) * cps)
    for i, ln in enumerate(lines):
        k = clamp(n - sum(len(m) for m in lines[:i]), 0, len(ln))
        text(img, x0 + 12, y0 + 30 + 18 * i, ln[:int(k)], INK)


def blink_text(img, t, x, y, s, col=DGREY, rate=3, align="c"):
    if int(t * rate) % 2 == 0:
        text(img, x, y, s, col, align=align)
