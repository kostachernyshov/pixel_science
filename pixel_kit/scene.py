# Scene timeline and output: frame (frame.W x frame.H) -> x4 nearest -> mp4 (ffmpeg), gif, or PNG.
#
#   from pixel_kit.scene import Timeline
#   tl = Timeline([(0.0, 3.0, scene_title), (3.0, 9.5, scene_design), ...])
#   tl.render("out.mp4")                   full render
#   tl.gif("out.gif", scale=2)             short loop for a slide
#   tl.export_frames("dir", [1.0, 5.5])    single frames as PNG (x4)
#   tl.storyboard("board.png", [..])       storyboard grid
# Between scenes: a Bayer dissolve to PAPER (FADE s), except at the very start.
# The active style adds its frame filter (gameboy: four shades) and scanlines (arcade).

import os, subprocess
import numpy as np
from PIL import Image
from .fx import dither_to
from .palette import PAPER, C

from . import frame
SCALE, FPS = frame.SCALE, 30
FADE = 0.25


def upscale(arr, scale=SCALE, scan=None):
    """x4 nearest. scan=True darkens each 4th row by 20 % (CRT scanlines; default: the style's)."""
    if scan is None:
        from . import style
        scan = style.current().scanlines
    big = np.repeat(np.repeat(arr, scale, axis=0), scale, axis=1)
    if scan and scale == SCALE:
        mask = np.ones((big.shape[0], 1, 1), np.float32)
        mask[3::SCALE] = 0.80
        big = (big.astype(np.float32) * mask).astype(np.uint8)
    return big


class Timeline:
    def __init__(self, scenes, fade=FADE, fps=FPS, fade_col=PAPER):
        """scenes: [(start, end, fn(t_local) -> PIL.Image RGB of the frame size, fade=True)].
        fade=False: no dissolve into this scene (a continuous shot, for example a camera move)."""
        self.scenes = scenes
        self.fade = fade
        self.fps = fps
        self.fade_col = fade_col

    @property
    def duration(self):
        return self.scenes[-1][1]

    def frame(self, T):
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
                return self._finish(dither_to(arr, fade, self.fade_col))
        return self._finish(np.full((frame.H, frame.W, 3), C(self.fade_col), np.uint8))

    def _finish(self, arr):
        from . import style
        return style.current().filter_frame(arr)

    def render(self, out, dur=None, progress=True):
        dur = dur or self.duration
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
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
        mosaic = Image.fromarray(np.concatenate(sample, axis=0))
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
        tiles = [Image.fromarray(self.frame(t)).resize((frame.W * 2, frame.H * 2), Image.NEAREST) for t in times]
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (frame.W * 2 + gap) + gap, rows * (frame.H * 2 + gap + lab_h) + gap), (220, 212, 206))
        for i, im in enumerate(tiles):
            x, y = gap + (i % cols) * (frame.W * 2 + gap), gap + (i // cols) * (frame.H * 2 + gap + lab_h)
            sheet.paste(im, (x, y))
            if labels:
                text(sheet, x + 4, y + frame.H * 2 + 2, labels[i], INK)
        sheet.save(path)
        return path
