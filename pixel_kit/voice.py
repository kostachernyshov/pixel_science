# Voice-over audio: voiceover.md spoken by Qwen3-TTS (local, Apache 2.0, Russian, English and 8 more languages).
#
#   pixsci voice  PLAN OUTDIR             OUTDIR/voice/<scene>.wav and OUTDIR/<name>-voice.wav
#   pixsci render PLAN OUTDIR --voice     speaks what is missing, then the sound in each mp4
#
# A plan times itself to the fresh voice in OUTDIR/voice/ (plan.load), with or without --voice.
#
# Optional: requirements-voice.txt (Python 3.10 to 3.12, PyTorch; see docs/tool.md, Voice). The first run downloads
# the model from Hugging Face (1.7B: ~4.5 GB). Each scene is spoken once; a scene is spoken again only when
# its text or the `tts:` settings change. After the voice, words.align times each word (subtitles, beats).

import json, os, wave
from typing import NamedTuple
import numpy as np

RATE = 24000             # Hz, Qwen3-TTS output
MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
VOICE = "ryan"           # speakers of the CustomVoice model: ryan, aiden (English); vivian, serena... (Chinese)
LANGS = {"en": "English", "ru": "Russian", "de": "German", "fr": "French", "es": "Spanish",
         "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "ko": "Korean", "zh": "Chinese"}
LEAD = 0.25              # s of silence before the words of a scene (the fade between scenes)
TAIL = 0.6               # s after them
PITFALL = ("Qwen3-TTS is not installed. Install it (Python 3.10 to 3.12 in .venv):\n"
           "  .venv/bin/pip install -r requirements-voice.txt\n"
           "  .venv/bin/pip install --no-deps qwen-asr==0.0.6")


def settings(plan):
    """`tts:` in the plan with defaults: voice, lang (from the plan's lang), instruct, model, seed."""
    t = dict(plan.get("tts") or {})
    t["voice"] = str(t.get("voice", VOICE)).lower()
    t["lang"] = str(t.get("lang") or LANGS.get(plan.get("lang", "en"), "English"))
    t.setdefault("model", MODEL)
    t.setdefault("seed", 1)
    t.setdefault("instruct", "")
    return t


def qwen3(t):
    """A function text -> float32 samples at RATE. t: settings(plan)."""
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")   # Apple Silicon: ops that MPS lacks run on CPU
    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except ImportError:
        raise SystemExit(PITFALL)
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    m = Qwen3TTSModel.from_pretrained(t["model"], device_map=dev,
                                      dtype=torch.bfloat16 if dev != "cpu" else torch.float32)

    def say(text):
        torch.manual_seed(int(t["seed"]))   # sampling: the same seed and text give the same take
        kw = {"instruct": t["instruct"]} if t["instruct"] else {}
        wavs, sr = m.generate_custom_voice(text=text, speaker=t["voice"], language=t["lang"], **kw)
        a = np.asarray(wavs[0], np.float32)
        if sr != RATE:
            a = np.interp(np.arange(0, len(a), sr / RATE), np.arange(len(a)), a).astype(np.float32)
        return a
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


class Voice(NamedTuple):
    """The voice in OUTDIR/voice/ for the current text. wavs: {scene id: wav} whose audio fits the scene's text and
    the tts: settings. stale: scenes with text and no such audio, in a folder that has a voice."""
    wavs: dict
    stale: list


def _key(t, text):
    return {"text": text, **{k: t[k] for k in ("voice", "lang", "instruct", "model", "seed")}}


def _meta(outdir):
    p = os.path.join(outdir, "voice", "meta.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def fresh(plan, texts, outdir):
    """The Voice of these texts ({scene id: spoken text}, words.spoken) in OUTDIR/voice/. One rule for scene lengths
    and word times: a scene uses its audio only when it is fresh."""
    if not outdir:
        return Voice({}, [])
    t, meta = settings(plan), _meta(outdir)
    wavs, stale = {}, []
    for sc in plan["scenes"]:
        sid = sc.get("id")
        text = texts.get(sid, "").strip()
        if not text:
            continue
        p = os.path.join(outdir, "voice", f"{sid}.wav")
        if meta.get(sid) == _key(t, text) and os.path.exists(p):
            wavs[sid] = p
        elif meta:
            stale.append(sid)
    return Voice(wavs, stale)


def speak(plan, texts, outdir, say=None):
    """Speaks each scene that has no fresh audio into OUTDIR/voice/<id>.wav. texts: {scene id: spoken text}
    (words.spoken). say: text -> samples; default Qwen3-TTS. Returns the Voice after it."""
    t = settings(plan)
    os.makedirs(os.path.join(outdir, "voice"), exist_ok=True)
    meta, have = _meta(outdir), fresh(plan, texts, outdir).wavs
    for sc in plan["scenes"]:
        sid = sc.get("id")
        text = texts.get(sid, "").strip()
        if not text or sid in have:
            continue
        say = say or qwen3(t)
        print(f"voice {sid}: {text[:60]}", flush=True)
        write_wav(os.path.join(outdir, "voice", f"{sid}.wav"), say(text))
        meta[sid] = _key(t, text)
        json.dump(meta, open(os.path.join(outdir, "voice", "meta.json"), "w"), indent=1, ensure_ascii=False)
    return fresh(plan, texts, outdir)


def lengths(wavs):
    """{scene id: s}: how long each scene's audio lasts, with the silence before and after its words."""
    return {sid: LEAD + len(read_wav(p)) / RATE + TAIL for sid, p in wavs.items()}


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
    from .scene import ffmpeg_exe
    tmp = video + ".tmp.mp4"
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", video, "-i", audio, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, video)
    return video
