# Bio cast: characters drawn by code in PICO-8 palette indices.
# Immune cells: white body, color rim, firm eyes.
# Tumor cells: dark plum lumpy body, red rim, black outline, angry brows, red eyes.
# Normal body cells: soft warm bodies, dot eyes, no brows.

import math
import numpy as np
from .palette import *
from .pixdraw import (Spr, T, mask_radial, mask_circle, mask_superellipse, mask_capsule,
                      paint_body, outline, polar)

# ---------------------------------------------------------------- faces


def hero_face(s, ex0, ey, brow=NAVY, look=1, blink=False, alert=False, calm=False, gap=5):
    """Two eyes of 2 px: straight brow, pupil 1x2. ex0 is the left edge of the left eye."""
    for ex in (ex0, ex0 + gap):
        if calm:
            # half-closed lids: a calm look
            s.put(ex, ey - 1, brow); s.put(ex + 1, ey - 1, brow)
            s.put(ex + (1 if look > 0 else 0), ey, BLACK)
            continue
        s.put(ex, ey - 2, brow); s.put(ex + 1, ey - 2, brow)
        if blink:
            s.put(ex, ey + 1, BLACK); s.put(ex + 1, ey + 1, BLACK)
        else:
            px = ex + (1 if look > 0 else 0)
            s.put(px, ey, BLACK)
            if not alert:
                s.put(px, ey + 1, BLACK)


def villain_face(s, ci, cj, blink=False, texture=True):
    """Tumor face: angry brows, red eyes, tight mouth."""
    if texture:
        for (x, y) in [(ci + 2, cj + 3), (ci + 3, cj + 1), (ci - 2, cj + 3), (ci - 4, cj + 1)]:
            s.put(x, y, BLACK)
    s.put(ci - 4, cj - 3, BLACK); s.put(ci - 3, cj - 2, BLACK)
    s.put(ci + 2, cj - 2, BLACK); s.put(ci + 3, cj - 3, BLACK)
    if blink:
        s.put(ci - 3, cj, BLACK); s.put(ci + 2, cj, BLACK)
    else:
        for ex in (ci - 3, ci + 2):
            s.put(ex, cj - 1, BLACK); s.put(ex, cj, RED)
    s.put(ci - 1, cj + 2, BLACK); s.put(ci, cj + 2, BLACK); s.put(ci + 1, cj + 2, BLACK)


def civ_face(s, ci, cj, blink=False, blush=PINK, sleepy=False, gap=4):
    """Normal-cell face: dot eyes, blush, no brows."""
    for ex in (ci - gap // 2 - 1, ci + gap // 2):
        if sleepy or blink:
            s.put(ex, cj, BLACK); s.put(ex + (1 if ex > ci else -1), cj, BLACK) if sleepy else None
        else:
            s.put(ex, cj - 1, BLACK); s.put(ex, cj, BLACK)
    if blush is not None:
        s.put(ci - gap // 2 - 2, cj + 2, blush); s.put(ci + gap // 2 + 1, cj + 2, blush)


# ---------------------------------------------------------------- surface molecules

def lollipop(s, cx, cy, a, r0, col=YELLOW, cap=None):
    """MHC-I: stem 2 px and head 2x2. cap is the peptide on the head (1 px)."""
    dx, dy = math.cos(a), math.sin(a)
    for r in (r0, r0 + 1):
        s.put(math.floor(cx + dx * r), math.floor(cy + dy * r), col)
    hx, hy = math.floor(cx + dx * (r0 + 2.5) - 0.5), math.floor(cy + dy * (r0 + 2.5) - 0.5)
    for ox in (0, 1):
        for oy in (0, 1):
            s.put(hx + ox, hy + oy, col)
    if cap is not None:
        s.put(math.floor(cx + dx * (r0 + 3.9)), math.floor(cy + dy * (r0 + 3.9)), cap)


def plug(s, cx, cy, a, r0, col=PINK):
    """PD-L1: T-shaped plug, a stem and a cross bar."""
    dx, dy = math.cos(a), math.sin(a)
    px_, py_ = -dy, dx
    for r in (r0, r0 + 1):
        s.put(math.floor(cx + dx * r), math.floor(cy + dy * r), col)
    bx, by = cx + dx * (r0 + 2), cy + dy * (r0 + 2)
    for k in (-1.2, 0, 1.2):
        s.put(math.floor(bx + px_ * k), math.floor(by + py_ * k), col)


def cup(s, cx, cy, a, r0, col=LGREY):
    """Receptor cup (PD-1, CTLA-4): stem and a U that opens out."""
    dx, dy = math.cos(a), math.sin(a)
    px_, py_ = -dy, dx
    s.put(math.floor(cx + dx * r0), math.floor(cy + dy * r0), col)
    bx, by = cx + dx * (r0 + 1), cy + dy * (r0 + 1)
    for k in (-1.2, 0, 1.2):
        s.put(math.floor(bx + px_ * k), math.floor(by + py_ * k), col)
    for k in (-1.2, 1.2):
        s.put(math.floor(bx + px_ * k + dx), math.floor(by + py_ * k + dy), col)


def fork(s, cx, cy, a, r0, col):
    """T-cell receptor: a short Y fork."""
    dx, dy = math.cos(a), math.sin(a)
    px_, py_ = -dy, dx
    s.put(math.floor(cx + dx * r0), math.floor(cy + dy * r0), col)
    for k in (-1, 1):
        s.put(math.floor(cx + dx * (r0 + 1.2) + px_ * k * 0.9), math.floor(cy + dy * (r0 + 1.2) + py_ * k * 0.9), col)


# ---------------------------------------------------------------- tumor cells

def villain_body(s, m, cx, cy, rim_k=-3.0, rim=RED):
    """Tumor body: solid red rim, pink highlight at the top left, black outline outside.
    The black outline keeps the shape on a light background.
    """
    paint_body(s, m, cx, cy, PLUM, rim, rim_hi=PINK if rim == RED else None, rim_hi_k=rim_k - 3.0)
    outline(s, BLACK)


MHC_ANGLES = [math.radians(-112.5 + 45 * k) for k in range(8)]


MHC_KEEP = [MHC_ANGLES[1]]
MHC_LOSE_ORDER = [a for a in MHC_ANGLES if a not in MHC_KEEP]


def keep_angles(n):
    """n MHC-I molecules, lost one by one (n=8: all, n=1: one left)."""
    return MHC_KEEP + MHC_LOSE_ORDER[8 - n:] if n < 8 else list(MHC_ANGLES)


def _lumpy(a):
    return 6.3 + 0.7 * np.sin(3 * a + 0.4) + 0.4 * np.sin(5 * a + 1.3)


def tumor(angles=MHC_ANGLES, blink=False, flash=False, pdl1=(), stress=(), cap=None):
    """Tumor cell. angles: where the MHC-I molecules are."""
    S, c = 22, 11.0
    s = Spr(S, S)
    m = mask_radial(S, S, c, c, lambda a: _lumpy(a))
    if flash:
        s.a[m] = WHITE
    else:
        villain_body(s, m, c, c)
        villain_face(s, 11, 11, blink=blink)
    for a in angles:
        lollipop(s, c, c, a, 6.9, cap=cap)
    for a in pdl1:
        plug(s, c, c, a, 6.9)
    for a in stress:
        flag(s, c, c, a, 6.9)
    return s


def flag(s, cx, cy, a, r0, col=ORANGE):
    """Stress molecule (NKG2D ligand): a small flag."""
    dx, dy = math.cos(a), math.sin(a)
    x0, y0 = cx + dx * r0, cy + dy * r0
    for r in range(3):
        s.put(math.floor(x0 + dx * r), math.floor(y0 + dy * r), LGREY)
    tx, ty = math.floor(x0 + dx * 2), math.floor(y0 + dy * 2)
    s.put(tx + 1, ty, col); s.put(tx + 2, ty, col); s.put(tx + 1, ty + 1, col)


def tumor_dividing():
    """Division: two lumpy halves, each with a face."""
    W_, H_ = 26, 18
    s = Spr(W_, H_)
    r = lambda a: 5.6 + 0.5 * np.sin(3 * a + 0.4) + 0.3 * np.sin(5 * a + 1.3)
    m1 = mask_radial(W_, H_, 8.0, 9.0, r)
    m2 = mask_radial(W_, H_, 18.0, 9.0, lambda a: r(a + 1.0))
    m = m1 | m2
    villain_body(s, m, 13.0, 9.0, rim_k=-4.0)
    # constriction
    s.put(13, 4, BLACK); s.put(13, 13, BLACK)
    for (ci, cj) in ((8, 9), (18, 9)):
        s.put(ci - 3, cj - 3, BLACK); s.put(ci - 2, cj - 2, BLACK)
        s.put(ci + 1, cj - 2, BLACK); s.put(ci + 2, cj - 3, BLACK)
        for ex in (ci - 2, ci + 1):
            s.put(ex, cj - 1, BLACK); s.put(ex, cj, RED)
        s.put(ci - 1, cj + 2, BLACK); s.put(ci, cj + 2, BLACK)
    return s


def tumor_apoptosis(k=2):
    """Apoptosis: the cell shrinks and breaks into blebs (no explosion).
    k: 0 whole, 1 shrink, 2 blebs, 3 fragments."""
    S, c = 22, 11.0
    s = Spr(S, S)
    rr = [6.3, 5.0, 4.2, 0][k]
    if rr > 0:
        m = mask_radial(S, S, c, c, lambda a: rr + 0.5 * np.sin(6 * a))
        villain_body(s, m, c, c, rim=LAV if k >= 2 else RED)
        ci = 11
        # closed eyes
        s.put(ci - 3, ci - 1, BLACK); s.put(ci - 2, ci - 1, BLACK)
        s.put(ci + 1, ci - 1, BLACK); s.put(ci + 2, ci - 1, BLACK)
        s.put(ci - 1, ci + 1, BLACK); s.put(ci, ci + 1, BLACK)
    if k >= 2:
        blebs = [(-0.6, 6.4), (1.0, 6.8), (2.3, 6.2), (3.6, 6.9), (4.9, 6.5)] if k == 2 else \
                [(-0.6, 7.5), (0.6, 4.0), (1.0, 8.5), (2.3, 6.5), (3.0, 2.5), (3.6, 8.0), (4.9, 7.0), (5.6, 3.5)]
        for (a, r) in blebs:
            x, y = polar(c, c, a, r)
            s.rect(x, y, x + 1, y + 1, PLUM)
            s.put(x, y, LAV)
    return s


def blast():
    """Leukemic blast (APL): round, a blood cell, with granules."""
    S, c = 18, 9.0
    s = Spr(S, S)
    m = mask_circle(S, S, c, c, 6.6)
    villain_body(s, m, c, c)
    villain_face(s, 9, 9, texture=False)
    for (x, y) in [(5, 12), (12, 11), (8, 14), (11, 5), (6, 5)]:
        s.put(x, y, PINK)
    return s


# ---------------------------------------------------------------- immune cells


def _hero_round(S, c, r, rim):
    s = Spr(S, S)
    m = mask_circle(S, S, c, c, r)
    paint_body(s, m, c, c, WHITE, rim, shade=LGREY)
    return s


def nk(look=1, blink=False, alert=False, grey=False):
    """NK cell: round, granules, no receptor fork (innate patrol)."""
    S, c = 20, 10.0
    rim, gran = (LAV, LAV) if grey else (BLUE, BLUE)
    s = Spr(S, S)
    m = mask_circle(S, S, c, c, 7.6)
    paint_body(s, m, c, c, DGREY if grey else WHITE, rim, shade=DGREY if grey else LGREY)
    for (x, y) in [(5, 12), (7, 14), (12, 14), (14, 11), (10, 13)]:
        s.put(x, y, gran)
    if grey:
        for ex in (6, 11):
            s.put(ex, 8, BLACK); s.put(ex + 1, 8, BLACK)
    else:
        hero_face(s, 6, 8, look=look, blink=blink, alert=alert)
    return s


def t_cell(kind="cd8", look=1, blink=False, alert=False, grey=False):
    """T cell: round, T-cell receptor forks on top.
    cd8: killer (green, granules); cd4: helper (orange, signal antenna);
    treg: regulatory (lavender, CTLA-4 cups on the sides, calm look);
    cart: CAR-T (green, large engineered receptor at the front)."""
    rim = {"cd8": GREEN, "cd4": ORANGE, "treg": LAV, "cart": GREEN}[kind]
    S, c = 20, 10.0
    s = Spr(S, S)
    cy = 11.0
    m = mask_circle(S, S, c, cy, 6.8)
    paint_body(s, m, c, cy, DGREY if grey else WHITE, LAV if grey else rim, shade=DGREY if grey else LGREY)
    for a in (-2.0, -1.57, -1.14):
        fork(s, c, cy, a, 7.0, LAV if grey else rim)
    if kind == "cd8":
        for (x, y) in [(6, 14), (9, 15), (12, 14)]:
            s.put(x, y, LAV if grey else GREEN)
    if kind == "cd4":
        # antenna: the helper sends signals
        for k in range(3):
            s.put(15 + k // 2, 5 - k, LGREY)
        s.rect(16, 1, 17, 2, ORANGE)
    if kind == "treg":
        for a in (0.0, math.pi):
            cup(s, c, cy, a, 7.0, LAV)
    if kind == "cart":
        # engineered receptor: a claw at the front
        s.rect(17, 10, 17, 12, LGREY)
        s.put(18, 9, BLUE); s.put(19, 9, BLUE); s.put(18, 13, BLUE); s.put(19, 13, BLUE)
        s.put(18, 10, BLUE); s.put(18, 12, BLUE)
        s.put(10, 2, YELLOW); s.put(9, 3, YELLOW); s.put(10, 3, YELLOW); s.put(11, 3, YELLOW)
    if grey:
        for ex in (6, 11):
            s.put(ex, 10, BLACK); s.put(ex + 1, 10, BLACK)
    else:
        hero_face(s, 6, 10, look=look, blink=blink, alert=alert, calm=(kind == "treg"))
    return s


def b_cell(look=1, blink=False, alert=False):
    """B cell: round, small Y antibodies on the surface."""
    S, c = 20, 10.0
    s = Spr(S, S)
    cy = 11.0
    m = mask_circle(S, S, c, cy, 6.8)
    paint_body(s, m, c, cy, WHITE, DGREEN, shade=LGREY)
    for a in (-2.2, -1.57, -0.94):
        x, y = polar(c, cy, a, 7.0)
        s.put(x, y, DGREEN); s.put(x, y - 1, DGREEN)
        s.put(x - 1, y - 2, DGREEN); s.put(x + 1, y - 2, DGREEN)
    hero_face(s, 6, 10, look=look, blink=blink, alert=alert)
    return s


def dendritic(look=1, blink=False, carry=True, alert=False):
    """Dendritic cell: body with branched arms; carries fragments (peptides on MHC)."""
    S = 26
    c = 13.0
    s = Spr(S, S)
    m = mask_circle(S, S, c, c, 6.2)
    arms = [(-2.6, 12.0, -0.5), (-1.3, 12.2, 0.6), (-0.1, 12.0, -0.6), (1.2, 11.8, 0.5),
            (2.3, 12.0, -0.5), (3.4, 11.0, 0.5)]
    for (a, L, br) in arms:
        x1, y1 = c + math.cos(a) * L, c + math.sin(a) * L
        m |= mask_capsule(S, S, c, c, x1, y1, 1.25)
        xm, ym = c + math.cos(a) * L * 0.6, c + math.sin(a) * L * 0.6
        x2, y2 = xm + math.cos(a + br * 1.6) * 4.0, ym + math.sin(a + br * 1.6) * 4.0
        m |= mask_capsule(S, S, xm, ym, x2, y2, 1.0)
    paint_body(s, m, c, c, WHITE, PINK, shade=LGREY)
    hero_face(s, 9, 13, look=look, blink=blink, alert=alert)
    if carry:
        # the arm tips hold fragments
        for (a, L, br) in arms[:3]:
            x, y = polar(c, c, a, L - 0.6)
            s.put(x, y, ORANGE)
    return s


def macrophage(look=1, blink=False, mode="eat", mouth=2, alert=False):
    """Macrophage: large, irregular, with a mouth notch to engulf.
    mode="eat": cleaner and eater; mode="repair": tissue repair mode."""
    S = 26
    c = 13.0
    s = Spr(S, S)
    r = lambda a: 9.6 + 1.1 * np.sin(4 * a + 0.7) + 0.6 * np.sin(7 * a + 2.0)
    m = mask_radial(S, S, c, c, r)
    # mouth: a wedge notch on the right
    ys, xs = np.mgrid[0:S, 0:S]
    dx, dy = xs + 0.5 - c, ys + 0.5 - c
    ang = np.arctan2(dy, dx)
    if mode == "eat" and mouth > 0:
        m &= ~((np.abs(ang - 0.35) < [0, 0.2, 0.42][mouth]) & (np.hypot(dx, dy) > 4.5))
    paint_body(s, m, c, c, WHITE, BROWN, shade=LGREY)
    for (x, y) in [(8, 16), (11, 18), (14, 17), (7, 13)]:
        s.put(x, y, LGREY)
    s.put(10, 15, DGREY); s.put(11, 15, DGREY)
    hero_face(s, 8, 10, look=look, blink=blink, alert=alert, calm=(mode == "repair"), gap=5)
    return s


# ---------------------------------------------------------------- normal body cells


def _civ(m, S_w, S_h, cx, cy, body=PEACH, rim=BROWN, shade=PINK, hi=WHITE):
    s = Spr(S_w, S_h)
    paint_body(s, m, cx, cy, body, rim, shade=shade, hi=hi)
    return s


def epithelial(blink=False):
    """Epithelial cell: a tissue brick, soft colors."""
    w, h = 16, 18
    m = mask_superellipse(w, h, 8.0, 9.0, 6.6, 8.0, n=4.0)
    s = _civ(m, w, h, 8.0, 9.0)
    civ_face(s, 8, 8, blink=blink)
    return s


def stem(blink=False):
    """Stem cell (Lgr5 in the crypt): round, with a sprout: the source of new cells."""
    S = 18
    m = mask_circle(S, S, 9.0, 10.0, 6.4)
    s = _civ(m, S, S, 9.0, 10.0)
    s.put(9, 3, DGREEN); s.put(9, 2, DGREEN); s.put(10, 1, GREEN); s.put(11, 1, GREEN); s.put(8, 1, GREEN)
    civ_face(s, 9, 10, blink=blink)
    return s


def mutant(blink=False):
    """Cell with a mutation: the same normal cell with a DNA patch. This is not cancer."""
    s = epithelial(blink)
    for (x, y) in [(10, 12), (11, 13), (12, 12), (11, 14)]:
        s.put(x, y, LAV)
    s.put(4, 4, LAV); s.put(5, 5, LAV); s.put(4, 6, LAV)
    return s


def clone(kind="A", blink=False):
    """Clones: four shapes and four soft colors (lineage tracing)."""
    if kind == "A":   # circle
        S = 16
        m = mask_circle(S, S, 8.0, 8.0, 6.6)
        s = _civ(m, S, S, 8.0, 8.0, PEACH, BROWN, PINK)
        civ_face(s, 8, 8, blink=blink)
    elif kind == "B":  # square
        S = 16
        m = mask_superellipse(S, S, 8.0, 8.0, 6.6, 6.6, n=6.0)
        s = _civ(m, S, S, 8.0, 8.0, PINK, PLUM, LAV, hi=PEACH)
        civ_face(s, 8, 8, blink=blink, blush=PEACH)
    elif kind == "C":  # hexagon
        S = 16
        ys, xs = np.mgrid[0:S, 0:S]
        dx, dy = np.abs(xs + 0.5 - 8.0), np.abs(ys + 0.5 - 8.0)
        m = (dy <= 6.4) & (dx * 0.866 + dy * 0.5 <= 6.4)
        s = _civ(m, S, S, 8.0, 8.0, ORANGE, BROWN, BROWN, hi=YELLOW)
        civ_face(s, 8, 8, blink=blink, blush=PEACH)
    else:              # drop, long at the top
        w, h = 16, 18
        m = mask_radial(w, h, 8.0, 10.5, lambda a: 6.0 + 2.2 * np.maximum(0.0, -np.sin(a)) ** 3)
        s = _civ(m, w, h, 8.0, 10.5, BLUE, NAVY, NAVY, hi=WHITE)
        civ_face(s, 8, 10, blink=blink, blush=PINK)
    return s


def senescent(blink=False):
    """Senescent cell: a normal cell that stopped division for good.
    Old man: grey brows, beard, half-closed eyes."""
    w, h = 16, 20
    m = mask_superellipse(w, h, 8.0, 9.0, 6.6, 8.0, n=4.0)
    s = _civ(m, w, h, 8.0, 9.0, PEACH, BROWN, PINK)
    s.ascii(0, 5, [
        "...ww.....ww....",
        "................",
        "....kk....kk....",
        "................",
        "................",
        ".....wwwwww.....",
        "....wwwwwwwg....",
        "....wwwwwwgg....",
        ".....wwwwwg.....",
        "......wwwg......",
        ".......wg.......",
    ], {"w": WHITE, "g": LGREY, "k": BLACK})
    return s


def granulocyte(blink=False):
    """Mature granulocyte: normal blood cell with a lobed nucleus."""
    S = 18
    m = mask_circle(S, S, 9.0, 9.0, 6.6)
    s = _civ(m, S, S, 9.0, 9.0, PEACH, BROWN, PINK)
    for (x, y) in [(5, 12), (6, 13), (8, 13), (9, 12), (11, 13), (12, 12)]:
        s.put(x, y, LAV)
    civ_face(s, 9, 8, blink=blink)
    return s


# ---------------------------------------------------------------- molecule badges


ICONS = {
    "mhc":      [".....", ".yyy.", ".yyy.", "..y..", "..y.."],
    "mhc_self": ["..w..", ".yyy.", ".yyy.", "..y..", "..y.."],
    "mhc_neo":  ["..o..", ".yyy.", ".yyy.", "..y..", "..y.."],
    "tcr":      ["g...g", ".g.g.", "..g..", "..g..", "..g.."],
    "pd1":      ["l...l", "l...l", "lllll", "..l..", "..l.."],
    "ctla4":    ["v...v", "v...v", "vvvvv", "..v..", "..v.."],
    "pdl1":     [".....", "ppppp", "..p..", "..p..", "..p.."],
    "stress":   [".ooo.", ".oo..", ".o...", ".l...", ".l..."],
}
ICON_KEY = {"y": YELLOW, "w": WHITE, "o": ORANGE, "g": GREEN, "l": LGREY, "v": LAV, "p": PINK}


def badge(kind):
    """Molecule badge for labels and UI (vertical, 5x5)."""
    if kind in ICONS:
        s = Spr(7, 7)
        s.ascii(1, 1, ICONS[kind], ICON_KEY)
        return s
    s = Spr(11, 11)
    if kind == "antibody":
        s.ascii(0, 0, [
            "w.......w..",
            "bw.....wb..",
            ".bw...wb...",
            "..bw.wb....",
            "...bwb.....",
            "....w......",
            "....w......",
            "....w....y.",
            "....b...yyy",
            ".........y.",
            "...........",
        ], {"w": WHITE, "b": BLUE, "y": YELLOW})
    return s
