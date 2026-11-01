# Animation timed to a recorded voice: transcript -> cues with times, animatic, mux with audio.
#
#   from pixel_kit import voice
#   cues = voice.load("voice/transcript.srt", start=0.0, end=None)    # the part of the recording
#   voice.table(cues)                       # id, time, text, speech rate
#   c = voice.cue(cues, "C03")              # or voice.find(cues, "survival")
#   t = voice.at(cues, "survival")          # time of a word (word timestamps, or share of characters in the cue)
#   voice.animatic(TIMELINE, [1.0, 4.2, ...], "voice/insert.wav", "animatic.mp4")
#   cut = voice.snap(c.start, voice.silences("voice/voice.wav"))  # scene boundary -> to a pause
#   voice.mux("insert.mp4", "voice/insert.wav", "insert_preview.mp4")
#
# Cue times are local: 0 = start. Transcript formats:
# SRT, VTT, Whisper JSON (segments[].words[]), plain text "0:12 text" / "[00:12.5] text" /
# "0:12-0:15 text" (end = start of the next line if not given).

import json, os, re, subprocess

import numpy as np

_TC = r"(?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d+)?|\d+(?:[.,]\d+)?"


def _sec(s):
    s = s.strip().replace(",", ".")
    parts = s.split(":")
    v = 0.0
    for p in parts:
        v = v * 60 + float(p)
    return v


class Cue:
    def __init__(self, id, start, end, text, words=None):
        self.id, self.start, self.end, self.text = id, start, end, text.strip()
        self.words = words or []          # [(word, start, end)] if there are word timestamps

    @property
    def dur(self):
        return self.end - self.start

    def __repr__(self):
        return f"{self.id} {self.start:6.2f}-{self.end:6.2f}  {self.text}"


def _parse_srt_vtt(txt):
    out = []
    pat = re.compile(rf"({_TC})\s*-->\s*({_TC})")
    blocks = re.split(r"\n\s*\n", txt.replace("\r", ""))
    for b in blocks:
        lines = [l for l in b.strip().split("\n") if l.strip()]
        for i, l in enumerate(lines):
            m = pat.search(l)
            if m:
                text = " ".join(lines[i + 1:])
                text = re.sub(r"<[^>]+>", "", text)
                out.append((_sec(m.group(1)), _sec(m.group(2)), text, []))
                break
    return out


def _parse_json(txt):
    d = json.loads(txt)
    segs = d.get("segments", d) if isinstance(d, dict) else d
    out = []
    for s in segs:
        words = [(w.get("word", w.get("text", "")).strip(), float(w["start"]), float(w["end"]))
                 for w in s.get("words", []) if "start" in w]
        out.append((float(s["start"]), float(s["end"]), s.get("text", ""), words))
    return out


def _parse_plain(txt):
    rows = []
    pat = re.compile(rf"^\s*\[?\s*({_TC})\s*(?:[-–—]\s*({_TC}))?\s*\]?\s*[:.\-–—|]?\s*(.*)$")
    for line in txt.replace("\r", "").split("\n"):
        if not line.strip():
            continue
        m = pat.match(line)
        if m and (":" in m.group(1) or line.lstrip().startswith("[")):
            rows.append([_sec(m.group(1)), _sec(m.group(2)) if m.group(2) else None, m.group(3)])
        elif rows:
            rows[-1][2] += " " + line.strip()      # the cue continues on the next line
    out = []
    for i, (a, b, t) in enumerate(rows):
        if b is None:
            b = rows[i + 1][0] if i + 1 < len(rows) else a + max(1.0, len(t.split()) / 2.3)
        out.append((a, b, t, []))
    return out


def parse(path):
    txt = open(path, encoding="utf-8-sig").read()
    if path.endswith(".json"):
        raw = _parse_json(txt)
    elif "-->" in txt:
        raw = _parse_srt_vtt(txt)
    else:
        raw = _parse_plain(txt)
    return [Cue(f"C{i + 1:02d}", a, b, t, w) for i, (a, b, t, w) in enumerate(raw) if t.strip()]


def load(path, start=0.0, end=None):
    """Cues from the transcript, cut to [start, end) of the recording and shifted so that start -> 0.
    ids keep the numbering of the whole transcript."""
    out = []
    for c in parse(path):
        if c.end <= start or (end is not None and c.start >= end):
            continue
        hi = (end if end is not None else c.end) - start
        w = [(s, a - start, b - start) for s, a, b in c.words]
        out.append(Cue(c.id, max(0.0, c.start - start), min(c.end - start, hi), c.text, w))
    return out


def cue(cues, id):
    for c in cues:
        if c.id == id:
            return c
    raise KeyError(id)


def find(cues, needle):
    n = needle.lower()
    for c in cues:
        if n in c.text.lower():
            return c
    raise KeyError(needle)


def at(cues, needle, edge="start"):
    """Time when a word or fragment sounds. From word timestamps if they exist; else from the share of characters
    in the cue (about 0.3-0.5 s accuracy; check key moments with `voice_sync.py silences`
    or by ear in the preview)."""
    n = needle.lower()
    for c in cues:
        low = c.text.lower()
        if n not in low:
            continue
        for s, a, b in c.words:
            if n.split()[0] in s.lower():
                return a if edge == "start" else b
        i = low.index(n)
        k = (i + (len(n) if edge == "end" else 0)) / max(1, len(low))
        return c.start + k * c.dur
    raise KeyError(needle)


def table(cues):
    """Prints cues with speech rate (words/s) and pauses: the base of the timing table."""
    prev = None
    for c in cues:
        if prev is not None and c.start - prev > 0.3:
            print(f"      pause {c.start - prev:4.1f} s")
        nw = len(c.text.split())
        print(f"{c.id}  {c.start:6.2f}-{c.end:6.2f}  ({c.dur:4.1f} s, {nw / max(c.dur, 0.1):3.1f} w/s)  {c.text}")
        prev = c.end


def dump(cues, path):
    json.dump([dict(id=c.id, start=round(c.start, 3), end=round(c.end, 3), text=c.text,
                    words=[dict(word=s, start=round(a, 3), end=round(b, 3)) for s, a, b in c.words])
               for c in cues], open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------------------------------------------------------------- audio and video

def probe(path):
    """Duration, video fps (if any), and if there is audio."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,r_frame_rate,width,height",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    info = dict(duration=float(d["format"]["duration"]), fps=None, size=None, audio=False)
    for s in d.get("streams", []):
        if s["codec_type"] == "video" and info["fps"] is None:
            a, b = s["r_frame_rate"].split("/")
            info["fps"] = round(float(a) / float(b), 3)
            info["size"] = (s.get("width"), s.get("height"))
        if s["codec_type"] == "audio":
            info["audio"] = True
    return info


def extract(src, start, end, out):
    """Cuts [start, end) of a recording (video or audio) to WAV 48 kHz."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
                    "-i", src, "-vn", "-ac", "2", "-ar", "48000", out], check=True)
    return out


def silences(src, start=0.0, end=None, noise="-35dB", d=0.15):
    """Pauses in speech [(start, end)] in local time: use them to find the start of phrases."""
    cmd = ["ffmpeg", "-hide_banner", "-ss", f"{start:.3f}"]
    if end is not None:
        cmd += ["-to", f"{end:.3f}"]
    cmd += ["-i", src, "-vn", "-af", f"silencedetect=noise={noise}:d={d}", "-f", "null", "-"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    out, a = [], None
    for line in r.stderr.split("\n"):
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            a = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and a is not None:
            out.append((a, float(m.group(1))))
            a = None
    return out


def snap(t, sil, within=0.6):
    """Moves a scene boundary to the nearest start of speech after a pause, if it is near."""
    best = min((e for _, e in sil), key=lambda e: abs(e - t), default=None)
    return best if best is not None and abs(best - t) <= within else t


def mux(video, audio, out, audio_start=0.0):
    """Video + voice -> preview to check sync (video is copied, not encoded again)."""
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-ss", f"{audio_start:.3f}", "-i", audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", out], check=True)
    return out


def animatic(timeline, times, audio, out, audio_start=0.0, dur=None):
    """Animatic: storyboard key frames hold until the next one, on the real voice.
    Shows the pace and the sync points before the full animation; renders in seconds."""
    from .scene import upscale, SCALE
    from . import frame
    dur = dur or timeline.duration
    times = sorted(float(t) for t in times)
    stills = [upscale(timeline.frame(t)) for t in times]
    fps = timeline.fps
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{frame.W * SCALE}x{frame.H * SCALE}", "-r", str(fps), "-i", "-"]
    if audio:
        cmd += ["-ss", f"{audio_start:.3f}", "-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(dur * fps)):
        t = i / fps
        k = max(0, int(np.searchsorted(times, t, side="right")) - 1)
        p.stdin.write(stills[k].tobytes())
    p.stdin.close()
    p.wait()
    return out


# ---------------------------------------------------------------- words and transcription

def words(path, start=0.0, end=None):
    """All words of a transcript as [(word, start, end)]. Cues without word times get them from the
    share of characters in the cue."""
    out = []
    for c in load(path, start, end):
        if c.words:
            out += [(w, a, b) for w, a, b in c.words if w.strip()]
            continue
        toks = c.text.split()
        total = sum(len(w) + 1 for w in toks) or 1
        t = c.start
        for w in toks:
            d = c.dur * (len(w) + 1) / total
            out.append((w, t, t + d))
            t += d
    return out


MODEL = "small.en"


def ensure_whisper():
    """Imports faster-whisper; installs it into this Python on first use."""
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        import sys
        print("installing faster-whisper (first use) ...", flush=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "faster-whisper"], check=True)
    import faster_whisper
    return faster_whisper


def transcribe(audio, out, model=MODEL):
    """Local transcript with word times (faster-whisper, CPU, int8). The model (about 460 MB for small.en)
    downloads on first use. Writes Whisper JSON: segments[].words[] with start and end."""
    fw = ensure_whisper()
    m = fw.WhisperModel(model, device="cpu", compute_type="int8")
    segs, info = m.transcribe(audio, language="en", word_timestamps=True, vad_filter=True)
    data = {"model": model, "language": "en", "segments": []}
    for s in segs:
        data["segments"].append({"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(),
                                 "words": [{"word": w.word.strip(), "start": round(w.start, 3),
                                            "end": round(w.end, 3)} for w in (s.words or [])]})
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out
