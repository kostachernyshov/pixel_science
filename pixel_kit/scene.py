# Scene timeline and output: frame (frame.W x frame.H) -> x4 nearest -> mp4 (ffmpeg), gif, or PNG.
# Text is on a grid FINE (2) times finer than the frame (font.py): Timeline.frame() returns the frame
# at FINE x size with the text on it, and the output scales it by SCALE / FINE.
#
#   from pixel_kit.scene import Timeline
#   tl = Timeline([(0.0, 3.0, scene_title), (3.0, 9.5, scene_design), ...])
#   tl.render("out.mp4")                   full render
#   tl.gif("out.gif", scale=2)             short loop for a slide
#   tl.export_frames("dir", [1.0, 5.5])    single frames as PNG (x4)
#   tl.storyboard("board.png", [..])       storyboard grid
# Between scenes: a Bayer dissolve to PAPER (FADE s), except at the very start.
# Scanlines are off in the light theme (they make grey stripes on a light background).

import os, shutil, subprocess, sys
import numpy as np
from PIL import Image
from .palette import PAPER, C

from . import frame, font
SCALE, FPS = frame.SCALE, 30
FINE = font.FINE


def ffmpeg_exe():
    """ffmpeg: $PIXSCI_FFMPEG, else ffmpeg on PATH, else the binary of the imageio-ffmpeg package."""
    exe = os.environ.get("PIXSCI_FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("ffmpeg not found: install it (brew install ffmpeg; apt install ffmpeg) or pip install imageio-ffmpeg")
FADE = 0.25
SCANLINES = False

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])
_bayer_cache = {}


def dither_mask(h, w, a):
    """Pixels a Bayer dissolve covers at amount a (0: none, 1: all)."""
    if (h, w) not in _bayer_cache:
        _bayer_cache[(h, w)] = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w]
    return _bayer_cache[(h, w)] < a * 16


def dither_to(arr, a, col=PAPER):
    """Dissolve to one color with a Bayer matrix (a=0: none, a=1: all col). arr is HxWx3."""
    if a <= 0:
        return arr
    arr[dither_mask(*arr.shape[:2], a)] = C(col)
    return arr


def upscale(arr, scale=SCALE, scan=None):
    """A Timeline frame (FINE x the frame size) to `scale` x the frame size, nearest.
    scan=True darkens each 4th row by 20 % (CRT scanlines, dark theme only)."""
    scan = SCANLINES if scan is None else scan
    k = max(1, scale // FINE)
    big = np.repeat(np.repeat(arr, k, axis=0), k, axis=1)
    if scan and scale == SCALE:
        mask = np.ones((big.shape[0], 1, 1), np.float32)
        mask[3::SCALE] = 0.80
        big = (big.astype(np.float32) * mask).astype(np.uint8)
    return big


class Timeline:
    def __init__(self, scenes, fade=FADE, fps=FPS, fade_col=PAPER, overlay=None):
        """scenes: [(start, end, fn(t_local) -> PIL.Image RGB of the frame size, fade=True)].
        fade=False: no dissolve into this scene (a continuous shot, for example a camera move)."""
        self.scenes = scenes
        self.fade = fade
        self.fps = fps
        self.fade_col = fade_col
        self.overlay = overlay      # overlay(arr, T) -> arr: drawn over the dissolve (subtitles)

    @property
    def duration(self):
        return self.scenes[-1][1]

    def frame(self, T):
        """The frame at time T, FINE x the frame size, with its text."""
        font.capture()
        try:
            arr, a = self._frame(T)
        finally:
            layer = font.release()
        fade = dither_mask(*arr.shape[:2], a) if a > 0 else None
        if self.overlay:
            font.capture()
            try:
                arr = self.overlay(arr, T)
            finally:
                over = font.release()
            # the overlay (subtitles) is not dissolved, and its box covers the scene text
            big = font.compose(arr, layer, fade)
            if over:
                img = Image.fromarray(big)
                for x, y, m, col in over:
                    img.paste(C(col), (x, y), m)
                big = np.array(img)
            return big
        return font.compose(arr, layer, fade)

    def _frame(self, T):
        """(frame pixels with the dissolve, dissolve amount)."""
        last_end = self.scenes[-1][1]
        for i, sc in enumerate(self.scenes):
            a, b, fn = sc[:3]
            if a <= T < b or (b == last_end and T >= a):
                arr = np.array(fn(T - a))
                fade_in = sc[3] if len(sc) > 3 else True
                nxt = self.scenes[i + 1] if i + 1 < len(self.scenes) else None
                fade_out = nxt is not None and (nxt[3] if len(nxt) > 3 else True)
                fade = 0.0
                if T - a < self.fade and a > 0 and fade_in:
                    fade = 1 - (T - a) / self.fade
                if b - T < self.fade and b != last_end and fade_out:
                    fade = max(fade, 1 - (b - T) / self.fade)
                return dither_to(arr, fade, self.fade_col), fade
        return np.full((frame.H, frame.W, 3), C(self.fade_col), np.uint8), 0.0

    def render(self, out, dur=None, progress=True):
        dur = dur or self.duration
        cmd = [ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{frame.W * SCALE}x{frame.H * SCALE}", "-r", str(self.fps), "-i", "-",
               "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", out]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n = int(dur * self.fps)
        for i in range(n):
            p.stdin.write(upscale(self.frame(i / self.fps)).tobytes())
            if progress and i % 150 == 0:
                print(f"{i}/{n}", flush=True)
        p.stdin.close()
        p.wait()
        return out

    def gif(self, out, scale=2, fps=15, dur=None):
        """GIF loop for slides: x2 by default (960x540), 15 fps. Exact palette colors, no dithering."""
        dur = dur or self.duration
        frames = []
        for i in range(int(dur * fps)):
            frames.append(Image.fromarray(upscale(self.frame(i / fps), scale=scale, scan=False)))
        # One palette for the whole loop, from frames across the video (not only the first frame:
        # the title frame has few colors, and later charts became grey).
        sample = [self.frame(t) for t in np.arange(0, dur, 0.5)]
        mosaic = Image.fromarray(np.concatenate(sample, axis=0))  # FINE x frames: same colors
        pal = mosaic.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        frames = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
        # GIF stores delays in 1/100 s: spread the rounding, so that the loop has the length of the video
        cs = [round(100 * (i + 1) / fps) - round(100 * i / fps) for i in range(len(frames))]
        frames[0].save(out, save_all=True, append_images=frames[1:], duration=[10 * c for c in cs], loop=0,
                       optimize=True)
        return out

    def export_frames(self, d, times):
        os.makedirs(d, exist_ok=True)
        out = []
        for ts in times:
            path = os.path.join(d, f"{float(ts):05.1f}s.png")
            Image.fromarray(upscale(self.frame(float(ts)))).save(path)
            out.append(path)
        return out

    def storyboard(self, path, times, cols=3, gap=12, labels=None):
        """Grid of key frames at x2. labels: optional text under each frame (scene id and time)."""
        from .font import text
        from .palette import INK
        lab_h = 20 if labels else 0
        tiles = [Image.fromarray(upscale(self.frame(t), scale=2)) for t in times]
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (frame.W * 2 + gap) + gap, rows * (frame.H * 2 + gap + lab_h) + gap), (220, 212, 206))
        for i, im in enumerate(tiles):
            x, y = gap + (i % cols) * (frame.W * 2 + gap), gap + (i // cols) * (frame.H * 2 + gap + lab_h)
            sheet.paste(im, (x, y))
            if labels:
                text(sheet, x + 4, y + frame.H * 2 + 2, labels[i], INK)
        sheet.save(path)
        return path
