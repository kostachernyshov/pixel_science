# Pixel charts drawn from real data: survival curve (Kaplan-Meier), dots by group (strip),
# heatmap, volcano plot, distribution (histograms).
#
# Each function takes the frame, a box (x0, y0, x1, y1) and the data as lists of numbers.
# The numbers come from pixel_kit.data (files), never from the agent.
# k (0..1) reveals the chart: curves grow from left to right, dots appear one by one.
# Group colors are pairs (line, fill) from palette.FAVORABLE / UNFAVORABLE / NEUTRAL.
# Axis ticks use the 3x5 mini font; titles and labels use Unifont.

import math, random
from PIL import ImageDraw
from .palette import *
from .font import text, text_w, mini_text, mini_w
from .timing import clamp

AXIS = INK
GUIDE = (230, 220, 212)        # faint guide lines, off-palette like the background grid


# ---------------------------------------------------------------- scales and axes

def nice_ticks(lo, hi, n=5):
    """About n round tick values that cover [lo, hi]."""
    if hi <= lo:
        hi = lo + 1
    raw = (hi - lo) / max(1, n)
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), default=10 * mag)
    start = math.ceil(lo / step - 1e-9) * step
    out, v = [], start
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += step
    return out


def tick_txt(v):
    if abs(v) >= 1000 or (v != 0 and abs(v) < 0.01):
        return f"{v:.0e}".replace("e+0", "e").replace("e-0", "e-")
    if float(v).is_integer():
        return str(int(v))
    return f"{v:.2f}".rstrip("0").rstrip(".")


class Plot:
    """Maps data to pixels inside a box. The box includes room for the axes."""

    def __init__(self, img, box, xlim, ylim, left=22, bottom=12, top=4, right=4):
        self.img, self.d = img, ImageDraw.Draw(img)
        x0, y0, x1, y1 = box
        self.px0, self.px1 = x0 + left, x1 - right
        self.py0, self.py1 = y0 + top, y1 - bottom
        self.xlim, self.ylim = xlim, ylim

    def X(self, v):
        a, b = self.xlim
        return int(round(self.px0 + (v - a) / ((b - a) or 1) * (self.px1 - self.px0)))

    def Y(self, v):
        a, b = self.ylim
        return int(round(self.py1 - (v - a) / ((b - a) or 1) * (self.py1 - self.py0)))

    def axes(self, xticks=None, yticks=None, xlabel=None, ylabel=None, guides=True, xfmt=tick_txt, yfmt=tick_txt):
        d = self.d
        if guides and yticks:
            for v in yticks:
                d.line([self.px0 + 1, self.Y(v), self.px1, self.Y(v)], fill=GUIDE)
        d.line([self.px0, self.py0, self.px0, self.py1], fill=C(AXIS))
        d.line([self.px0, self.py1, self.px1, self.py1], fill=C(AXIS))
        for v in xticks or []:
            x = self.X(v)
            d.line([x, self.py1, x, self.py1 + 2], fill=C(AXIS))
            mini_text(self.img, x, self.py1 + 4, xfmt(v), AXIS, align="c")
        for v in yticks or []:
            y = self.Y(v)
            d.line([self.px0 - 2, y, self.px0, y], fill=C(AXIS))
            mini_text(self.img, self.px0 - 4, y - 2, yfmt(v), AXIS, align="r")
        if xlabel:
            text(self.img, (self.px0 + self.px1) // 2, self.py1 + 10, xlabel, DGREY, align="c")
        if ylabel:
            text(self.img, self.px0 + 4, self.py0 - 18, ylabel, DGREY)


def _swatch(d, x, y, col):
    d.rectangle([x, y, x + 7, y + 7], fill=C(col[1]), outline=C(col[0]))


def legend(img, x, y, items, gap=4):
    """items: [(label, color pair)] in one column. Returns the height."""
    d = ImageDraw.Draw(img)
    for i, (lab, col) in enumerate(items):
        yy = y + i * (16 + gap)
        _swatch(d, x, yy + 4, col)
        text(img, x + 12, yy, lab, col[0])
    return len(items) * (16 + gap)


# ---------------------------------------------------------------- Kaplan-Meier

def km_curve(times, events):
    """Kaplan-Meier estimate: [(t, S)] steps and the censor times. events: 1 = event, 0 = censored."""
    pairs = sorted(zip(times, events))
    n = len(pairs)
    s, out, cens = 1.0, [(0.0, 1.0)], []
    i = 0
    while i < n:
        t = pairs[i][0]
        d = c = 0
        while i < n and pairs[i][0] == t:
            if pairs[i][1]:
                d += 1
            else:
                c += 1
            i += 1
        at_risk = n - (i - d - c)
        if d:
            s *= 1 - d / at_risk
            out.append((t, s))
        if c:
            cens.append((t, s))
    return out, cens


def km(img, box, groups, k=1.0, tmax=None, xlabel="TIME", ylabel="SURVIVAL", time_scale=1.0, legend_xy=None,
       show_legend=True):
    """Survival curves. groups: [dict(label, times, events, col)]. time_scale divides times
    (for example 365.25 to show years). The legend shows each label with n."""
    tmax = tmax or max(max(g["times"]) for g in groups) / time_scale
    p = Plot(img, box, (0, tmax), (0, 1.0), left=24, bottom=30, top=20)
    p.axes(nice_ticks(0, tmax, 5), [0, 0.25, 0.5, 0.75, 1.0], xlabel, ylabel,
           yfmt=lambda v: f"{int(v * 100)}%")
    tcut = tmax * clamp(k)
    d = p.d
    for g in groups:
        steps, cens = km_curve([t / time_scale for t in g["times"]], g["events"])
        line = C(g["col"][0])
        prev = None
        for (t, s) in steps + [(tmax, steps[-1][1])]:
            t = min(t, tmax)
            if prev is not None:
                t0, s0 = prev
                if t0 > tcut:
                    break
                te = min(t, tcut)
                d.line([p.X(t0), p.Y(s0), p.X(te), p.Y(s0)], fill=line, width=2)
                if t <= tcut and t < tmax:
                    d.line([p.X(t), p.Y(s0), p.X(t), p.Y(s)], fill=line, width=2)
            prev = (t, s)
        for (t, s) in cens:
            if t <= tcut and t <= tmax:
                d.line([p.X(t), p.Y(s) - 2, p.X(t), p.Y(s) + 1], fill=line)
    if not show_legend:
        return p
    lx, ly = legend_xy or (p.px1 - 150, p.py0 + 2)
    legend(img, lx, ly, [(f"{g['label']} n={len(g['times'])}", g["col"]) for g in groups])
    return p


# ---------------------------------------------------------------- strip (dots by group)

def _median(v):
    s = sorted(v)
    n = len(s)
    return (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2) if n else float("nan")


def strip(img, box, groups, k=1.0, ylabel=None, ylim=None, show_median=True, dot=2, seed=1):
    """Dots by group with a median bar. groups: [dict(label, values, col)].
    Labels under the groups show the label and n."""
    allv = [v for g in groups for v in g["values"]]
    lo, hi = ylim or (min(allv), max(allv))
    pad = (hi - lo) * 0.05 or 1
    yt = nice_ticks(lo - pad, hi + pad, 5)
    p = Plot(img, box, (0, len(groups)), (min(yt[0], lo - pad), max(yt[-1], hi + pad)), left=26, bottom=36, top=20)
    p.axes(None, yt, None, ylabel)
    d = p.d
    slot = (p.px1 - p.px0) / len(groups)
    for gi, g in enumerate(groups):
        cx = p.px0 + slot * (gi + 0.5)
        half = min(slot * 0.32, 60)
        rnd = random.Random(seed + gi)
        vals = g["values"]
        nshow = int(len(vals) * clamp(k))
        for v in vals[:nshow]:
            x = int(cx + rnd.uniform(-half, half))
            y = p.Y(v)
            d.rectangle([x, y, x + dot - 1, y + dot - 1], fill=C(g["col"][0]))
        if show_median and k >= 1:
            m = _median(vals)
            d.rectangle([int(cx - half - 4), p.Y(m) - 1, int(cx + half + 4), p.Y(m)], fill=C(INK))
        text(img, int(cx), p.py1 + 4, g["label"], g["col"][0], align="c")
        text(img, int(cx), p.py1 + 18, f"n={len(vals)}", DGREY, align="c")
    return p


# ---------------------------------------------------------------- distribution (histograms)

def distribution(img, box, groups, k=1.0, bins=24, xlabel=None, xlim=None):
    """One histogram per group, stacked, on a shared x axis. groups: [dict(label, values, col)]."""
    allv = [v for g in groups for v in g["values"]]
    lo, hi = xlim or (min(allv), max(allv))
    xt = nice_ticks(lo, hi, 6)
    lo, hi = min(lo, xt[0]), max(hi, xt[-1])
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    band = (y1 - y0 - 30) / len(groups)
    left = x0 + 90
    p = None
    for gi, g in enumerate(groups):
        by0 = int(y0 + gi * band)
        by1 = int(y0 + (gi + 1) * band) - 4
        counts = [0] * bins
        for v in g["values"]:
            j = min(bins - 1, max(0, int((v - lo) / (hi - lo) * bins)))
            counts[j] += 1
        top = max(counts) or 1
        p = Plot(img, (left, by0, x1, by1), (lo, hi), (0, top), left=0, bottom=0, top=2, right=0)
        d.line([p.px0, p.py1, p.px1, p.py1], fill=C(AXIS))
        shown = int(bins * clamp(k) + 0.999)
        bw = (p.px1 - p.px0) / bins
        for j in range(min(shown, bins)):
            if counts[j]:
                bx0 = int(p.px0 + j * bw)
                bx1 = max(bx0, int(p.px0 + (j + 1) * bw) - 1)
                d.rectangle([bx0, p.Y(counts[j]), bx1, p.py1 - 1], fill=C(g["col"][1]), outline=C(g["col"][0]))
        text(img, x0, (by0 + by1) // 2 - 16, g["label"], g["col"][0])
        text(img, x0, (by0 + by1) // 2, f"n={len(g['values'])}", DGREY)
    for v in xt:
        x = p.X(v)
        d.line([x, p.py1, x, p.py1 + 2], fill=C(AXIS))
        mini_text(img, x, p.py1 + 4, tick_txt(v), AXIS, align="c")
    if xlabel:
        text(img, (p.px0 + p.px1) // 2, p.py1 + 10, xlabel, DGREY, align="c")
    return p


# ---------------------------------------------------------------- heatmap

def bin_color(v, lim, scale=DIVERGING):
    """Palette index for v in a scale. Diverging scales are symmetric around 0 in [-lim, lim]."""
    if v != v:  # NaN
        return None
    n = len(scale)
    if scale is SEQUENTIAL:
        j = int(clamp(v / lim) * n)
    else:
        j = int((clamp((v + lim) / (2 * lim))) * n)
    return scale[min(n - 1, j)]


def heatmap(img, box, matrix, row_labels=None, col_groups=None, group_cols=None, lim=None, k=1.0,
            scale=EXPRESSION, low="LOW", high="HIGH"):
    """Heatmap. matrix: rows x columns (for example genes x samples, values centered at 0).
    col_groups: a group index for each column (columns should be sorted by group);
    group_cols: color pairs for the group bar. Row labels show only if each row has >= 9 px.
    k reveals columns from left to right."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    nr, nc = len(matrix), len(matrix[0])
    lim = lim or max(abs(v) for row in matrix for v in row if v == v) or 1
    lab_w = (max(text_w(s) for s in row_labels) + 6) if row_labels else 0
    gx0, gy0 = x0 + lab_w, y0 + (8 if col_groups else 0)
    gy1 = y1 - 22
    cw = (x1 - gx0) / nc
    rh = (gy1 - gy0) / nr
    shown = int(nc * clamp(k) + 0.999)
    for c in range(min(shown, nc)):
        cx0, cx1 = int(gx0 + c * cw), int(gx0 + (c + 1) * cw) - (1 if cw >= 4 else 0)
        if col_groups and group_cols:
            d.rectangle([cx0, y0, max(cx0, cx1), y0 + 5], fill=C(group_cols[col_groups[c]][0]))
        for r in range(nr):
            col = bin_color(matrix[r][c], lim, scale)
            ry0, ry1 = int(gy0 + r * rh), int(gy0 + (r + 1) * rh) - (1 if rh >= 4 else 0)
            d.rectangle([cx0, ry0, max(cx0, cx1), max(ry0, ry1)], fill=C(col) if col is not None else GUIDE)
    if row_labels and rh >= 9:
        for r, s in enumerate(row_labels):
            text(img, gx0 - 4, int(gy0 + (r + 0.5) * rh) - 8, s, INK, align="r")
    # scale bar: words only, no numbers
    sx = x1 - len(scale) * 10 - text_w(high) - 4
    text(img, sx - 4, gy1 + 4, low, DGREY, align="r")
    for j, col in enumerate(scale):
        d.rectangle([sx + j * 10, gy1 + 8, sx + j * 10 + 9, gy1 + 15], fill=C(col))
    text(img, sx + len(scale) * 10 + 4, gy1 + 4, high, DGREY)
    return gx0, gy0, x1, gy1


# ---------------------------------------------------------------- volcano

def volcano(img, box, fc, logp, labels=None, fc_thr=1.0, p_thr=2.0, k=1.0, colors=None, top_n=5,
            xlabel="LOG2 FC", ylabel="-LOG10 P"):
    """Volcano plot. fc: effect (log2 fold change), logp: -log10 p (or q).
    colors: (down, up) color pairs; default neutral (grey, lavender): up or down is not good or bad by itself.
    Points pass the thresholds when |fc| >= fc_thr and logp >= p_thr. top_n labels by logp."""
    down, up = colors or (NEUTRAL[0], NEUTRAL[1])
    xm = max(abs(v) for v in fc) * 1.05 or 1
    ym = max(logp) * 1.08 or 1
    p = Plot(img, box, (-xm, xm), (0, ym), left=26, bottom=30, top=20)
    p.axes(nice_ticks(-xm, xm, 6), nice_ticks(0, ym, 4), xlabel, ylabel)
    d = p.d
    for v in (-fc_thr, fc_thr):
        x = p.X(v)
        for y in range(p.py0, p.py1, 3):
            d.point([x, y], fill=C(LGREY))
    y = p.Y(p_thr)
    for x in range(p.px0, p.px1, 3):
        d.point([x, y], fill=C(LGREY))
    order = sorted(range(len(fc)), key=lambda i: logp[i])
    nshow = int(len(order) * clamp(k))
    for i in order[:nshow]:
        sig = abs(fc[i]) >= fc_thr and logp[i] >= p_thr
        col = (down if fc[i] < 0 else up)[0] if sig else LGREY
        x, yy = p.X(fc[i]), p.Y(logp[i])
        d.rectangle([x, yy, x + 1, yy + 1], fill=C(col))
    if labels and k >= 1:
        sig = [i for i in range(len(fc)) if abs(fc[i]) >= fc_thr and logp[i] >= p_thr]
        placed = []
        for i in sorted(sig, key=lambda i: -logp[i])[:top_n]:
            x, yy = p.X(fc[i]), p.Y(logp[i])
            right = fc[i] >= 0
            w = text_w(labels[i])
            lx = min(x + 6, p.px1 - w) if right else max(x - 6 - w, p.px0 + 2)
            ly = max(p.py0, yy - 8)
            while any(abs(ly - py) < 16 and lx < px + pw and px < lx + w for (px, py, pw) in placed):
                ly += 16
            placed.append((lx, ly, w))
            d.line([x, yy, lx if right else lx + w, ly + 8], fill=C(DGREY))
            text(img, lx, ly, labels[i], INK, outline=True, shadow=PAPER)
    return p
