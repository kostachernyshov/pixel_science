# Styles. A style pack (kind: style) has a "style:" block in pack.yaml:
#
#   style:
#     name: arcade
#     roles: {paper: [10, 8, 24], ink: [255, 241, 232], ...}   # see palette.ROLE_NAMES
#     colors: {NAVY: [41, 173, 255]}        # UI and effect colors, by palette name
#     sprite_colors: {}                     # sprite pixels, by palette name
#     sprite: {shading: false, outline: BLACK, glow: [29, 43, 83]}
#     redraw: true                          # draw code sprites again with the sprite parameters
#     background: {filter: dark, strength: 1.5}     # none | dark
#     frame: {filter: quantize, colors: [[15, 56, 15], ...], cuts: [70, 150, 228]}
#     scanlines: true
#
# The sprite cascade (sprites.py): a PNG in the style pack's sprites/ > a code sprite drawn again
# with the style's sprite parameters > the base PNG recolored with sprite_colors.
#
#   from pixel_kit import style
#   style.use("arcade")
#   style.current().name

import numpy as np
from PIL import Image
from . import palette as PL
from . import pixdraw, packs

BASE_NAME = "paper"


class Style:
    def __init__(self, spec, pack=None):
        spec = spec or {}
        self.spec = spec
        self.pack = pack
        self.name = spec.get("name", BASE_NAME)
        self.description = spec.get("description", "")
        self.dark = bool(spec.get("dark", False))
        self.redraw = bool(spec.get("redraw", False))
        self.scanlines = bool(spec.get("scanlines", False))
        sp = spec.get("sprite") or {}
        self.shading = bool(sp.get("shading", True))
        self.outline = _index(sp.get("outline", "BLACK"))
        self.glow = tuple(sp["glow"]) if sp.get("glow") else None
        self.background = spec.get("background") or {"filter": "none"}
        self.frame_filter = spec.get("frame") or {"filter": "none"}
        # UI colors: base, then colors, then roles
        ui = list(PL.BASE)
        for k, v in (spec.get("colors") or {}).items():
            ui[_index(k)] = tuple(v)
        for k, v in (spec.get("roles") or {}).items():
            if k not in PL.ROLE_NAMES:
                raise ValueError(f"style {self.name}: unknown role {k!r}; roles: {', '.join(PL.ROLE_NAMES)}")
            ui[PL.ROLE_NAMES[k]] = tuple(v)
        self.ui = ui
        spr = list(PL.P)
        for k, v in (spec.get("sprite_colors") or {}).items():
            spr[_index(k)] = tuple(v)
        self.sprite_colors = spr
        self._lut = None

    @property
    def is_base(self):
        return self.name == BASE_NAME

    def sprite_params(self):
        return {"shading": self.shading, "outline": self.outline}

    # ---------------------------------------------------------------- sprites

    def finish_sprite(self, arr):
        """Index sheet -> RGBA in this style: outline color, glow ring, sprite colors."""
        a = arr.copy()
        if self.outline != PL.BLACK:
            m = a >= 0
            edge = m & ~_erode(m)
            a[edge & (a == PL.BLACK)] = self.outline
        im = np.zeros(a.shape + (4,), np.uint8)
        for i, col in enumerate(self.sprite_colors):
            sel = a == i
            if sel.any():
                im[sel] = tuple(col) + (255,)
        if self.glow:
            m = a >= 0
            ring = _dilate(m) & ~m
            im[ring] = self.glow + (255,)
        return Image.fromarray(im, "RGBA")

    # ---------------------------------------------------------------- whole frames

    def filter_background(self, img):
        f = self.background.get("filter", "none")
        if f == "none":
            return img
        if f == "dark":
            k = float(self.background.get("strength", 1.5))
            a = np.asarray(img).astype(np.float32)
            base = np.array(PL.BASE[PL.PAPER], np.float32)
            bgc = np.array(self.ui[PL.PAPER], np.float32)
            out = bgc + np.clip(base - a, 0, 255) * k
            return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        raise ValueError(f"style {self.name}: unknown background filter {f!r}")

    def filter_frame(self, arr):
        """HxWx3 uint8 -> the same, after the style's frame filter (quantize: a 4-shade screen)."""
        f = self.frame_filter.get("filter", "none")
        if f == "none":
            return arr
        if f == "quantize":
            if self._lut is None:
                cols = np.array(self.frame_filter["colors"], np.uint8)
                cuts = self.frame_filter.get("cuts", [70, 150, 228])
                lum = np.arange(256)
                idx = np.searchsorted(np.array(cuts), lum, side="right")
                self._lut = cols[idx]
            a = arr.astype(np.uint32)
            lum = (a[..., 0] * 77 + a[..., 1] * 150 + a[..., 2] * 29) >> 8
            return self._lut[lum]
        raise ValueError(f"style {self.name}: unknown frame filter {f!r}")


def _index(name):
    if isinstance(name, int):
        return name
    n = str(name).upper()
    if n not in PL.NAMES:
        raise ValueError(f"unknown palette color {name!r}; use one of {', '.join(PL.NAMES)}")
    return PL.NAMES.index(n)


def _erode(m):
    e = m.copy()
    e[1:, :] &= m[:-1, :]
    e[:-1, :] &= m[1:, :]
    e[:, 1:] &= m[:, :-1]
    e[:, :-1] &= m[:, 1:]
    return e


def _dilate(m):
    g = m.copy()
    g[1:, :] |= m[:-1, :]
    g[:-1, :] |= m[1:, :]
    g[:, 1:] |= m[:, :-1]
    g[:, :-1] |= m[:, 1:]
    return g


_current = Style({"name": BASE_NAME})
_by_name = {}


def names():
    return sorted(packs.styles())


def load(name):
    if name not in _by_name:
        st = packs.styles()
        if name not in st:
            if name == BASE_NAME:
                _by_name[name] = Style({"name": BASE_NAME})
            else:
                raise packs.PackError(f"unknown style {name!r}; styles: {', '.join(sorted(st))}")
        else:
            _by_name[name] = Style(st[name].style, st[name])
    return _by_name[name]


def use(name):
    """Makes a style active: UI colors, sprite parameters; clears the sprite and background caches."""
    global _current
    s = load(name or BASE_NAME)
    if s is _current:
        return s
    _current = s
    PL.set_active(s.ui)
    pixdraw.PARAMS.update(s.sprite_params())
    from . import sprites, bg
    sprites.clear()
    bg.clear()
    return s


def current():
    return _current


class base:
    """with style.base(): ...   draws in the base colors (backgrounds), then restores the style."""
    def __enter__(self):
        self.saved = list(PL._active)
        PL.set_active(PL.BASE)

    def __exit__(self, *a):
        PL.set_active(self.saved)
