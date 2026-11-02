# Palette: PICO-8 (lospec.com/palette-list/pico-8). No transparency, no anti-aliasing.
# Indices 0-15: the main 16 colors. Sprites use only these.
# Indices 16-31: the PICO-8 "secret" colors. Only charts and color scales use them.
# Index 32: PAPER, the background. Sprites do not use it.
# Meaning of colors in charts: see STYLE.md (blue = better outcome, orange = worse, neutral = no direction).

P = [(0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81), (171, 82, 54), (95, 87, 79),
     (194, 195, 199), (255, 241, 232), (255, 0, 77), (255, 163, 0), (255, 236, 39),
     (0, 228, 54), (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
     # secret palette (PICO-8 indices 128-143)
     (41, 24, 20), (17, 29, 53), (66, 33, 54), (18, 83, 89), (116, 47, 41), (73, 51, 59),
     (162, 136, 121), (243, 239, 125), (190, 18, 80), (255, 108, 36), (168, 231, 46),
     (0, 181, 67), (6, 90, 181), (117, 70, 101), (255, 110, 89), (255, 157, 129),
     # 32: the background only (off-palette: whiter and cooler than PICO-8 white)
     (251, 250, 247)]
BLACK, NAVY, PLUM, DGREEN, BROWN, DGREY, LGREY, WHITE, RED, ORANGE, YELLOW, GREEN, BLUE, LAV, PINK, PEACH = range(16)
(XBROWN, XNAVY, XPLUM, XTEAL, XRUST, XMAUVE, XTAUPE, XLEMON, XCRIMSON, XORANGE, XLIME,
 XGREEN, XBLUE, XPURPLE, XSALMON, XAPRICOT) = range(16, 32)
NAMES = ["BLACK", "NAVY", "PLUM", "DGREEN", "BROWN", "DGREY", "LGREY", "WHITE",
         "RED", "ORANGE", "YELLOW", "GREEN", "BLUE", "LAV", "PINK", "PEACH",
         "XBROWN", "XNAVY", "XPLUM", "XTEAL", "XRUST", "XMAUVE", "XTAUPE", "XLEMON",
         "XCRIMSON", "XORANGE", "XLIME", "XGREEN", "XBLUE", "XPURPLE", "XSALMON", "XAPRICOT", "PAPER"]

# Light theme. PAPER is the background, INK is text and axes.
PAPER = 32                      # near white, a little cool. Sprite bodies stay WHITE (warm) with an outline.
INK = BLACK
GRID_LINE = (236, 234, 230)     # faint dotted grid on PAPER (off-palette, like the muted backgrounds)

# Group colors for charts: (line or mark, fill). A line uses the first color: it has >= 3:1 on PAPER.
# The sets pass colorcheck (Delta E >= 20 in normal, deutan, protan views) inside each set.
# Better outcome, response, no side effects: shades of blue.
FAVORABLE = [(XBLUE, BLUE), (NAVY, XBLUE), (XNAVY, NAVY)]
# Worse outcome, no response: shades of orange.
UNFAVORABLE = [(BROWN, ORANGE), (XRUST, XORANGE), (XBROWN, BROWN)]
# No direction (subtypes, phenotypes without "better" or "worse").
NEUTRAL = [(DGREY, LGREY), (LAV, LAV), (XBROWN, XTAUPE)]
# Diverging scale when low is better and high is worse (for example a risk score): blue -> grey -> orange.
DIVERGING = [XNAVY, XBLUE, BLUE, LGREY, ORANGE, XORANGE, BROWN]
# Expression scale for heatmaps (z-scores): dark purple -> teal -> green -> yellow, like viridis.
# It does not use blue or orange, so it does not say "better" or "worse". Readable with deutan and protan.
EXPRESSION = [XPLUM, NAVY, XTEAL, DGREEN, XLIME, YELLOW]
# Sequential scale (one direction, for example a level).
SEQUENTIAL = [LGREY, BLUE, XBLUE, NAVY, XNAVY]


def C(i):
    return P[i]


def CA(i):
    return P[i] + (255,)
