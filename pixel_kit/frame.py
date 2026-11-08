# Video formats. The frame is drawn small (PICO-8 pixels) and scaled x4 with nearest neighbor.
#
#   from pixel_kit import frame
#   with frame.using("vertical"):    the format while a scene is drawn; the one before comes back on exit
#       frame.W, frame.H             current frame size in pixels (read them at draw time, not at import)
#
# Each module reads frame.W and frame.H when it draws, so one process can render all formats.

import contextlib

FORMATS = {
    "landscape": (480, 270),     # 16:9  -> 1920x1080 (YouTube, slides)
    "vertical": (270, 480),      # 9:16  -> 1080x1920 (Reels, Shorts, TikTok)
    "square": (270, 270),        # 1:1   -> 1080x1080 (feed posts)
    "banner": (480, 120),        # 4:1   -> 1920x480  (site header, wide banner)
}
SCALE = 4

NAME = "landscape"
W, H = FORMATS[NAME]


@contextlib.contextmanager
def using(name):
    """The format `name` inside the block; the format before it comes back after."""
    global NAME, W, H
    if name not in FORMATS:
        raise KeyError(f"unknown format {name!r}; use one of {', '.join(FORMATS)}")
    before = NAME
    NAME, (W, H) = name, FORMATS[name]
    try:
        yield
    finally:
        NAME, (W, H) = before, FORMATS[before]


def out_size():
    return W * SCALE, H * SCALE
