# Color checks for the light theme: contrast to PAPER, and how far apart group colors are
# for normal vision, deuteranopia, protanopia, and in greyscale.
#
#   from pixel_kit import colorcheck as CC
#   rows, ok = CC.check([("favorable", XBLUE), ("unfavorable", BROWN)])
#   CC.panel(frame_rgb_array, "colors.png")     # one frame in four views
#
# Simulation: Machado, Oliveira, Fernandes (2009), severity 1.0, in linear RGB.
# Pass: line color vs PAPER >= 3:1 (WCAG 1.4.11), and Delta E (CIE76) >= 20 between each pair
# of group colors in normal, deutan, and protan views. Greyscale is a warning only: when two groups
# have the same lightness, the frame must also tell them apart by label or position.

import numpy as np
from PIL import Image
from .palette import P, PAPER, INK, C

MACHADO = {
    "protan": np.array([[0.152286, 1.052583, -0.204868],
                        [0.114503, 0.786281, 0.099216],
                        [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968],
                        [0.280085, 0.672501, 0.047413],
                        [-0.011820, 0.042940, 0.968881]]),
}
MIN_CONTRAST = 3.0
MIN_DE = 20.0
MIN_GREY_DL = 10.0


def _lin(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(l):
    l = np.clip(l, 0, 1)
    return np.where(l <= 0.0031308, l * 12.92, 1.055 * l ** (1 / 2.4) - 0.055) * 255.0


def simulate(rgb, kind):
    """rgb: (..., 3) uint8 or float 0-255. kind: normal / deutan / protan / grey."""
    rgb = np.asarray(rgb, np.float64)
    if kind == "normal":
        return rgb
    lin = _lin(rgb)
    if kind == "grey":
        y = lin @ np.array([0.2126, 0.7152, 0.0722])
        return np.repeat(_srgb(y)[..., None], 3, axis=-1)
    return _srgb(lin @ MACHADO[kind].T)


def luminance(rgb):
    return float(_lin(rgb) @ np.array([0.2126, 0.7152, 0.0722]))


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def lab(rgb):
    x = _lin(rgb) @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    x = x / np.array([0.95047, 1.0, 1.08883])
    f = np.where(x > 216 / 24389, np.cbrt(x), (24389 / 27 * x + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def delta_e(a, b):
    return float(np.linalg.norm(lab(a) - lab(b)))


def check(colors, bg=PAPER):
    """colors: [(name, palette index)]. Returns (rows, ok). Each row: name, contrast to bg, and the smallest
    Delta E to the other colors in each view (and the smallest lightness difference in grey)."""
    rows, ok = [], True
    bgc = C(bg)
    for i, (name, idx) in enumerate(colors):
        c = C(idx)
        row = {"name": name, "color": idx, "contrast": round(contrast(c, bgc), 2)}
        if row["contrast"] < MIN_CONTRAST:
            ok = False
        for kind in ("normal", "deutan", "protan"):
            ds = [delta_e(simulate(c, kind), simulate(C(j), kind)) for k2, (_, j) in enumerate(colors) if k2 != i]
            row[kind] = round(min(ds), 1) if ds else None
            if ds and min(ds) < MIN_DE:
                ok = False
        gs = [abs(lab(simulate(c, "grey"))[0] - lab(simulate(C(j), "grey"))[0])
              for k2, (_, j) in enumerate(colors) if k2 != i]
        row["grey_dL"] = round(min(gs), 1) if gs else None
        rows.append(row)
    return rows, ok


def report(rows, ok):
    lines = ["color\tindex\tcontrast_to_paper\tdE_normal\tdE_deutan\tdE_protan\tgrey_dL\tnote"]
    for r in rows:
        note = []
        if r["contrast"] < MIN_CONTRAST:
            note.append("LOW CONTRAST")
        for k in ("normal", "deutan", "protan"):
            if r[k] is not None and r[k] < MIN_DE:
                note.append(f"CLOSE IN {k.upper()}")
        if r["grey_dL"] is not None and r["grey_dL"] < MIN_GREY_DL:
            note.append("same lightness in grey: label directly")
        lines.append(f"{r['name']}\t{r['color']}\t{r['contrast']}\t{r['normal']}\t{r['deutan']}\t{r['protan']}\t"
                     f"{r['grey_dL']}\t{'; '.join(note)}")
    lines.append(f"RESULT\t{'PASS' if ok else 'FAIL'}")
    return "\n".join(lines)


def panel(arr, out, labels=("NORMAL", "DEUTERANOPIA", "PROTANOPIA", "GREYSCALE")):
    """One frame (HxWx3) in four views, 2x2, with labels."""
    from .font import text
    arr = np.asarray(arr)
    h, w = arr.shape[:2]
    gap = 24
    sheet = Image.new("RGB", (w * 2 + gap * 3, (h + gap) * 2 + gap), C(PAPER))
    for i, kind in enumerate(("normal", "deutan", "protan", "grey")):
        im = Image.fromarray(simulate(arr, kind).round().astype(np.uint8))
        x, y = gap + (i % 2) * (w + gap), gap + (i // 2) * (h + gap)
        sheet.paste(im, (x, y))
        text(sheet, x, y - 18, labels[i], INK)
    sheet.save(out)
    return out
