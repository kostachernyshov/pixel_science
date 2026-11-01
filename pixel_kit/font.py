# Text in the frame: Unifont 16 px (pixel font, Latin and Cyrillic) and a title font 5x7.
# Rule: text in the frame is English, 2-3 words, large, on screen for >= 2 s.

import os
from PIL import Image, ImageDraw, ImageFont
from .palette import C, BLACK, LGREY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.environ.get("PIXEL_FONT", os.path.join(ROOT, "fonts", "unifont.otf"))
FONT = ImageFont.truetype(FONT_PATH, 16)
LINE = 16

_text_cache = {}


def text_mask(s, scale=1):
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
    outline=True: an outline in the shadow color on all sides (labels over a scene)."""
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
