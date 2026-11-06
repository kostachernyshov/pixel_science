# A custom scene of the setup check: the tool draws the background and the title, this draws the rest.
# ctx["shows"] has the time of each relation the scene shows (its beats with shows:).
from pixel_kit import frame, sprites as S


def draw(img, t, scene, ctx):
    if t >= ctx["shows"]["drawn"]:
        S.idle(img, "nk", t, frame.W // 2, frame.H // 2, scale=2)
