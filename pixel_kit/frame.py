# Video formats. The frame is drawn small (PICO-8 pixels) and scaled x4 with nearest neighbor.
#
#   from pixel_kit import frame
#   frame.use("vertical")        set the format before a scene is drawn
#   frame.W, frame.H             current frame size in pixels (read them at draw time, not at import)
#
# Each module reads frame.W and frame.H when it draws, so one process can render all formats.

FORMATS = {
    "landscape": (480, 270),     # 16:9  -> 1920x1080 (YouTube, slides)
    "vertical": (270, 480),      # 9:16  -> 1080x1920 (Reels, Shorts, TikTok)
    "square": (270, 270),        # 1:1   -> 1080x1080 (feed posts)
    "banner": (480, 120),        # 4:1   -> 1920x480  (site header, wide banner)
}
SCALE = 4

NAME = "landscape"
W, H = FORMATS[NAME]


def use(name):
    global NAME, W, H
    if name not in FORMATS:
        raise KeyError(f"unknown format {name!r}; use one of {', '.join(FORMATS)}")
    NAME = name
    W, H = FORMATS[name]
    return W, H


def out_size():
    return W * SCALE, H * SCALE
