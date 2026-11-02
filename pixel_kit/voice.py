# Voice-over audio: voiceover.md spoken by Kokoro (local TTS, English, Apache 2.0).
#
#   pixsci voice  PLAN OUTDIR             OUTDIR/voice/<scene>.wav and OUTDIR/<name>-voice.wav
#   pixsci render PLAN OUTDIR --voice     the same audio, scenes timed to it, sound in each mp4
#
# Kokoro is optional: pip install -r requirements-voice.txt (Python 3.10 to 3.12), and espeak-ng.
# The first run downloads the model (~330 MB) and the voice from Hugging Face.
# Each scene is synthesized once; a scene is spoken again only when its text, voice, or speed changes.

import json, os, wave
import numpy as np

RATE = 24000             # Hz, Kokoro output
VOICE = "af_heart"       # American English, female; `tts: {voice: ...}` in the plan
LEAD = 0.25              # s of silence before the words of a scene (the fade between scenes)
TAIL = 0.6               # s after them
PITFALL = ("Kokoro is not installed. Install it (Python 3.10 to 3.12):\n"
           "  .venv/bin/pip install -r requirements-voice.txt\n"
           "  brew install espeak-ng      # Linux: apt install espeak-ng")


def settings(plan):
    """(voice, speed) from `tts:` in the plan."""
    t = plan.get("tts") or {}
    return str(t.get("voice", VOICE)), float(t.get("speed", 1.0))


def kokoro(voice, speed):
    """A function text -> float32 samples at RATE, made with Kokoro."""
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")   # Apple Silicon: ops that MPS lacks run on CPU
    try:
        from kokoro import KPipeline
    except ImportError:
        raise SystemExit(PITFALL)
    pipe = KPipeline(lang_code=voice[0])   # the first letter of a voice is its language: a = American, b = British

    def say(text):
        parts = []
        for r in pipe(text, voice=voice, speed=speed):
            if r.audio is not None:
                a = r.audio
                parts.append(np.asarray(a.cpu() if hasattr(a, "cpu") else a, np.float32))
        return np.concatenate(parts) if parts else np.zeros(0, np.float32)
    return say


def read_wav(p):
    with wave.open(p, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767


def write_wav(p, samples):
    pcm = (np.clip(samples, -1, 1) * 32767).astype(np.int16)
    with wave.open(p, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())


def attach(plan, texts, outdir, say=None):
    """Speaks the voice-over of each scene into outdir/voice/<id>.wav (only what changed) and puts the
    length of the words of each scene into plan["_spoken"], so that `explain.durations` times scenes to
    the audio. texts: {scene id: text} (explain.voiceover). say: text -> samples; default Kokoro.
    Returns {scene id: wav path}."""
    voice, speed = settings(plan)
    d = os.path.join(outdir, "voice")
    os.makedirs(d, exist_ok=True)
    meta_p = os.path.join(d, "meta.json")
    meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
    paths, spoken = {}, {}
    for sc in plan["scenes"]:
        sid = sc.get("id")
        text = texts.get(sid, "").strip()
        if not text:
            continue
        p = os.path.join(d, f"{sid}.wav")
        key = {"text": text, "voice": voice, "speed": speed}
        if meta.get(sid) != key or not os.path.exists(p):
            say = say or kokoro(voice, speed)
            print(f"voice {sid}: {text[:60]}")
            write_wav(p, say(text))
            meta[sid] = key
            json.dump(meta, open(meta_p, "w"), indent=1)
        paths[sid] = p
        spoken[sid] = LEAD + len(read_wav(p)) / RATE + TAIL
    plan["_spoken"] = spoken
    return paths


def mix(plan, paths, times, out):
    """One track: the audio of each scene from the start of its scene. times: explain.durations(plan)."""
    track = np.zeros(int(round(times[-1][1] * RATE)) + 1, np.float32) if times else np.zeros(1, np.float32)
    for sc, (a, _) in zip(plan["scenes"], times):
        p = paths.get(sc.get("id"))
        if p:
            s = read_wav(p)
            i = int(round((a + LEAD) * RATE))
            track[i:i + len(s)] += s[:max(0, len(track) - i)]
    write_wav(out, track)
    return out


def mux(video, audio):
    """Puts the audio into the mp4 in place (video stream copied, audio AAC)."""
    import subprocess
    tmp = video + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, video)
    return video
