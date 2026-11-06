# Text in the frame: Medeo Pixel (OFL 1.1, fonts/LICENSE_medeo.txt), Latin and Cyrillic, and a title font 5x7.
# Rule: text in the frame is English, 2-3 words, large, on screen for >= 2 s.
#
# Fine grid: the text grid is FINE (2) times finer than the frame grid. One text pixel is half a frame
# pixel, so Medeo (cap height 19 font pixels) at scale 1 is as tall as Unifont 16 px was (cap 10).
# Sizes and positions stay in frame pixels: LINE * scale per line, text_w() in frame pixels.
# How: while a frame is drawn (capture()), text() does not draw on the image; it records the text,
# and the Timeline composes it over the frame at FINE x size (compose()). Text is drawn over sprites.
# Outside capture() (sheets, tools), text() draws Unifont 16 px on the image, as before.
# PIXEL_TEXT_FONT=unifont: Unifont everywhere (old look).

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .palette import C, BLACK, LGREY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.environ.get("PIXEL_FONT", os.path.join(ROOT, "fonts", "unifont.otf"))
FONT = ImageFont.truetype(FONT_PATH, 16)
LINE = 16
FINE = 2
FACE = os.environ.get("PIXEL_TEXT_FONT", "medeo")

# Medeo Pixel: one font pixel is 38 units (1000 per em). The face is drawn 8 times larger and
# read at the center of each cell, so every glyph lands on the grid exactly (no hinting errors).
MEDEO_PATH = os.path.join(ROOT, "fonts", "MedeoPixel.ttf")
_SS = 8
_MEDEO = None
_BOX, _BASE = LINE * FINE, 14 * FINE   # Medeo line box in fine pixels; baseline where Unifont has it

_text_cache = {}
_layer = None                           # list of recorded text while a frame is drawn, else None


def _medeo():
    global _MEDEO
    if _MEDEO is None:
        _MEDEO = ImageFont.truetype(MEDEO_PATH, 1000 * _SS / 38)
    return _MEDEO


def medeo_mask(s, scale=1, box=_BOX, base=_BASE):
    """Mask of s in Medeo Pixel at a whole scale, `box` rows high, baseline at row `base` (font pixels)."""
    key = ("medeo", s, scale, box, base)
    if key not in _text_cache:
        F = _medeo()
        w = max(1, int(round(F.getlength(s) / _SS)))
        big = Image.new("L", (w * _SS, box * _SS), 0)
        d = ImageDraw.Draw(big)
        d.fontmode = "1"
        d.text((0, base * _SS), s, font=F, fill=255, anchor="ls")
        # NEAREST reads the center of each _SS x _SS cell
        m = big.resize((w, box), Image.NEAREST, box=(0, 0, w * _SS, box * _SS))
        if scale > 1:
            m = m.resize((m.width * scale, m.height * scale), Image.NEAREST)
        _text_cache[key] = m
    return _text_cache[key]


def _fine():
    return FACE == "medeo" and _layer is not None


def capture():
    """Start recording text for one frame (the Timeline calls it)."""
    global _layer
    _layer = []


def release():
    """Stop recording; returns the recorded text."""
    global _layer
    out, _layer = _layer or [], None
    return out


def compose(arr, layer, fade=None):
    """arr (H x W x 3, frame pixels) -> FINE x larger, with the recorded text drawn on it.
    fade: a frame-size bool mask (True: dissolved to the fade color): text there is not drawn."""
    big = np.repeat(np.repeat(arr, FINE, axis=0), FINE, axis=1)
    if not layer:
        return big
    img = Image.fromarray(big)
    for x, y, m, col in layer:
        img.paste(C(col), (x, y), m)
    out = np.array(img)
    if fade is not None and fade.any():
        f = np.repeat(np.repeat(fade, FINE, axis=0), FINE, axis=1)
        out[f] = big[f]
    return out


def text_mask(s, scale=1):
    """Unifont mask of s (frame pixels)."""
    key = (s, scale)
    if key not in _text_cache:
        w = int(FONT.getlength(s)) + 1
        m = Image.new("L", (max(w, 1), 16), 0)
        d = ImageDraw.Draw(m)
        d.fontmode = "1"
        d.text((0, 0), s, font=FONT, fill=255)
        if scale > 1:
            m = m.resize((m.width * scale, m.height * scale), Image.NEAREST)
        _text_cache[key] = m
    return _text_cache[key]


def text(img, x, y, s, col, scale=1, align="l", shadow=None, outline=False):
    """align: l / c / r. shadow: color of a 1 px drop shadow (None: no shadow);
    outline=True: an outline in the shadow color on all sides (labels over a scene).
    Returns the width in frame pixels."""
    if _fine():
        m = medeo_mask(s, scale)
        x, y = int(x * FINE), int(y * FINE)
        if align == "c":
            x -= m.width // 2
        elif align == "r":
            x -= m.width
        k = scale                   # shadow and outline: one font pixel
        if outline:
            shadow = BLACK if shadow is None else shadow
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                _layer.append((x + dx * k, y + dy * k, m, shadow))
        elif shadow is not None:
            _layer.append((x + k, y + k, m, shadow))
        _layer.append((x, y, m, col))
        return -(-m.width // FINE)
    m = text_mask(s, scale)
    if align == "c":
        x -= m.width // 2
    elif align == "r":
        x -= m.width
    x, y = int(x), int(y)
    if outline:
        shadow = BLACK if shadow is None else shadow
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            img.paste(C(shadow), (x + dx * scale, y + dy * scale), m)
    elif shadow is not None:
        img.paste(C(shadow), (x + scale, y + scale), m)
    img.paste(C(col), (x, y), m)
    return m.width


def text_w(s, scale=1):
    """Width in frame pixels: Medeo on the fine grid (rounded up), or Unifont."""
    if FACE == "medeo":
        return -(-int(round(_medeo().getlength(s) / _SS)) * scale // FINE)
    return int(FONT.getlength(s)) * scale


# Title font 5x7: in Unifont, a large W reads as N
TITLE_GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "J": ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    "-": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    " ": ["....."] * 7,
}


def title_text(img, cx, y, s, k, col, shade, back=LGREY):
    """Title: 5x7 letters of k px, top 4 rows in col, lower rows in shade, drop shadow in back.
    Unknown characters raise KeyError: check the text first."""
    w = len(s) * 6 * k - k
    x0 = cx - w // 2
    d = ImageDraw.Draw(img)
    for n, ch in enumerate(s):
        for r, row in enumerate(TITLE_GLYPHS[ch]):
            for q, b in enumerate(row):
                if b == "#":
                    x, yy = x0 + (n * 6 + q) * k, y + r * k
                    d.rectangle([x + k // 2, yy + k // 2, x + k // 2 + k - 1, yy + k // 2 + k - 1], fill=C(back))
    for n, ch in enumerate(s):
        for r, row in enumerate(TITLE_GLYPHS[ch]):
            for q, b in enumerate(row):
                if b == "#":
                    x, yy = x0 + (n * 6 + q) * k, y + r * k
                    d.rectangle([x, yy, x + k - 1, yy + k - 1], fill=C(col if r < 4 else shade))


# Mini font 3x5 for axis ticks: digits and a few signs. One pixel of space between characters.
MINI_GLYPHS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", "..#", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
    ".": ["...", "...", "...", "...", ".#."], "-": ["...", "...", "###", "...", "..."],
    "+": ["...", ".#.", "###", ".#.", "..."], "e": ["...", "##.", "###", "#..", ".##"],
    "%": ["#.#", "..#", ".#.", "#..", "#.#"], " ": ["...", "...", "...", "...", "..."],
    "n": ["...", "##.", "#.#", "#.#", "#.#"], "=": ["...", "###", "...", "###", "..."],
}


def mini_w(s, scale=1):
    return (len(s) * 4 - 1) * scale if s else 0


def mini_text(img, x, y, s, col, scale=1, align="l"):
    """Draws s with the 3x5 mini font. Unknown characters raise KeyError."""
    w = mini_w(s, scale)
    if align == "c":
        x -= w // 2
    elif align == "r":
        x -= w
    d = ImageDraw.Draw(img)
    for n, ch in enumerate(s):
        for r, row in enumerate(MINI_GLYPHS[ch]):
            for q, b in enumerate(row):
                if b == "#":
                    xx, yy = int(x) + (n * 4 + q) * scale, int(y) + r * scale
                    d.rectangle([xx, yy, xx + scale - 1, yy + scale - 1], fill=C(col))
    return w
