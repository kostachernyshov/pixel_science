# Words of the voice-over in time: what is said, when, and the subtitles drawn from it.
#
#   voiceover.md may write a word one way and say it another: [PD-L1|пи-ди-эль-один].
#   written(text)  the text for the screen ("PD-L1")      spoken(text)  the text for the voice
#
#   align() writes voice/<scene>.words.json: [{"w": "PD-L1", "s": 1.20, "e": 1.85}, ...] (seconds in the
#   scene's wav), by forced alignment of the known text to the audio. Without it, times are estimated.
#
#   A beat can start on a word: {word: "тормоз", dt: -0.3, actor: t, verb: alert}  (n: 2 for the 2nd time).
#   A custom scene asks for the same time with cue(plan, scene, "тормоз").
#   subtitles: true in the plan draws the words in a box at the bottom, each word when it is heard.

import json, os, re

MARK = re.compile(r"\[([^\]|]+)\|([^\]]+)\]")
EST_WPS = 2.5            # words a second, when there is no alignment
from .voice import LEAD  # silence before the words of a scene


def written(text):
    return MARK.sub(lambda m: m.group(1), text)


def spoken(text):
    return MARK.sub(lambda m: m.group(2), text)


def tokens(text):
    """Written words with the span of their spoken form: [(word, spoken_part)], in order."""
    out, pos = [], 0
    for m in MARK.finditer(text):
        for w in text[pos:m.start()].split():
            out.append((w, w))
        # a mark is one written word (or several), all timed over the whole spoken part;
        # punctuation right after the mark stays with it ("[PD-L1|...]." is one word "PD-L1.")
        tail = re.match(r"[^\s\[]*", text[m.end():]).group(0)
        out.append((m.group(1) + tail, m.group(2) + tail))
        pos = m.end() + len(tail)
    for w in text[pos:].split():
        out.append((w, w))
    return out


def norm(s):
    """Letters and digits only, lower case, ё as е: to compare words."""
    return re.sub(r"[^\w]", "", s.lower().replace("ё", "е")).replace("_", "")


def estimate(text):
    """Word times without alignment: EST_WPS words a second, longer words take longer."""
    toks = tokens(text)
    lens = [max(1, len(norm(sp))) for _, sp in toks]
    total = sum(lens) or 1
    dur = len(toks) / EST_WPS
    out, t = [], 0.0
    for (w, _), n in zip(toks, lens):
        d = dur * n / total
        out.append({"w": w, "s": round(t, 3), "e": round(t + d * 0.9, 3)})
        t += d
    return out


def from_alignment(text, items):
    """Maps aligned spoken units [{"text", "start", "end"}] back to the written words of text.
    Units are found in the spoken text by their letters, in order; a written word takes the time
    from the first to the last unit that overlaps its spoken part."""
    toks = tokens(text)
    # letters of the spoken text, with the index of the written token each letter belongs to
    owner, letters = [], []
    for i, (_, sp) in enumerate(toks):
        for ch in norm(sp):
            letters.append(ch)
            owner.append(i)
    stream = "".join(letters)
    times = [[None, None] for _ in toks]
    pos = 0
    for it in items:
        u = norm(it["text"])
        if not u:
            continue
        j = stream.find(u, pos)
        if j < 0 or j - pos > 40:          # not found near: skip the unit (the aligner changed it)
            continue
        for k in range(j, j + len(u)):
            i = owner[k]
            if times[i][0] is None:
                times[i][0] = it["start"]
            times[i][1] = it["end"]
        pos = j + len(u)
    out = []
    for (w, _), (s, e) in zip(toks, times):
        out.append({"w": w, "s": s, "e": e})
    # a word the aligner missed: between its neighbours
    for i, x in enumerate(out):
        if x["s"] is None:
            prev = next((out[k]["e"] for k in range(i - 1, -1, -1) if out[k]["e"] is not None), 0.0)
            nxt = next((out[k]["s"] for k in range(i + 1, len(out)) if out[k]["s"] is not None), prev + 0.3)
            x["s"], x["e"] = prev, max(prev, nxt)
    return [{"w": x["w"], "s": round(float(x["s"]), 3), "e": round(float(x["e"]), 3)} for x in out]


def _aligned(wav, text):
    """voice/<id>.words.json next to the wav, when it was aligned to this text and this audio."""
    p = os.path.splitext(wav)[0] + ".words.json"
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("text") == text and d.get("wav_mtime") == os.path.getmtime(wav):
            return d["words"]
    return None


def load_scene(wav, text):
    """Words of one scene with times in the scene's wav: aligned if the scene has a fresh wav (voice.fresh)
    and its words.json fits the text and the audio; else estimated. Returns (words, aligned)."""
    ws = _aligned(wav, text) if wav else None
    return (ws, True) if ws is not None else (estimate(text), False)


def attach(plan, texts, wavs):
    """Puts the words of each scene into plan.words = {scene id: [{"w","s","e"}]}, with times from
    the start of the scene (LEAD added). wavs: the fresh audio (voice.fresh). Returns the number of aligned scenes."""
    out, n = {}, 0
    for sc in plan["scenes"]:
        sid = sc.get("id")
        text = texts.get(sid, "").strip()
        if not text:
            continue
        ws, ok = load_scene(wavs.get(sid), text)
        n += ok
        out[sid] = [{"w": w["w"], "s": w["s"] + LEAD, "e": w["e"] + LEAD} for w in ws]
    plan.words = out
    return n


# ---------------------------------------------------------------- beats on words

def word_time(words, key, n=1):
    """Start of a word in the scene: key is an index (0 = first word) or a word. n: the n-th time it is said.
    The same word wins ("B" finds "B", not "because"); only if the scene does not have it, the start of a
    word is enough ("тормоз" finds "тормоза")."""
    if isinstance(key, int):
        return words[key]["s"] if 0 <= key < len(words) else None
    k = norm(str(key))
    same = [w["s"] for w in words if norm(w["w"]) == k]
    hits = same or [w["s"] for w in words if norm(w["w"]).startswith(k)]
    return hits[n - 1] if 0 < n <= len(hits) else None


def cue(plan, sc, key, n=1, dt=0.0, default=0.0):
    """For custom scenes: the time in the scene when a word is heard (see word_time), plus dt."""
    t = word_time(plan.words.get(sc.get("id")) or [], key, n)
    return default if t is None else t + dt


def resolve_beats(plan):
    """Sets t of each beat with `word:` from the words of its scene. Returns problems (strings)."""
    words = plan.words
    problems = []
    for sc in plan["scenes"]:
        ws = words.get(sc.get("id")) or []
        for b in sc.get("beats") or []:
            if "word" not in b:
                continue
            n = int(b.get("n", 1))
            t = word_time(ws, b["word"], n)
            if t is None:
                k = norm(str(b["word"]))
                same = sum(norm(w["w"]) == k for w in ws)
                said = same or sum(norm(w["w"]).startswith(k) for w in ws)
                how = " as a whole word (a whole word wins over the start of a longer one)" if same else ""
                problems.append(f"{sc.get('id')}: beat word {b['word']!r} is not in the voice-over of the scene"
                                if not said else f"{sc.get('id')}: beat word {b['word']!r} n: {n}, but the scene "
                                f"says it {said} time(s){how}")
                continue
            b["t"] = round(max(0.0, t + float(b.get("dt", 0))), 3)
    return problems


# ---------------------------------------------------------------- subtitles

GAP_BREAK = 0.45         # s: a pause this long starts a new page
END_HOLD = 0.7           # s: a page stays after its last word (if the next page has not begun)


def timeline_words(plan, times):
    """All words in video time: [(word, start, end)]. times: explain.durations(plan)."""
    words = plan.words
    out = []
    for sc, (a, _) in zip(plan["scenes"], times):
        for w in words.get(sc.get("id")) or []:
            out.append((w["w"], a + w["s"], a + w["e"]))
    return out


def pages(words, fits):
    """Groups words into pages: each page fits the box (fits(list of words) -> bool), breaks
    after the end of a sentence, at a long pause, and, if it can, after a comma or a colon."""
    out, cur = [], []
    for i, w in enumerate(words):
        if cur and not fits([x[0] for x in cur] + [w[0]]):
            # step back to the last comma in the page, if it leaves the page at least half full
            cut = max((j for j, x in enumerate(cur) if x[0][-1:] in ",:;—–"), default=-1)
            if cut >= len(cur) // 2 and cut < len(cur) - 1:
                out.append(cur[:cut + 1])
                cur = cur[cut + 1:]
            else:
                out.append(cur)
                cur = []
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        end_sentence = w[0][-1:] in ".!?…"
        pause = nxt is not None and nxt[1] - w[2] >= GAP_BREAK
        if end_sentence or pause:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def page_spans(pgs, video_end):
    """(start, end) on screen of each page: from its first word to the next page, or END_HOLD after."""
    spans = []
    for i, p in enumerate(pgs):
        s = p[0][1]
        nxt = pgs[i + 1][0][1] if i + 1 < len(pgs) else video_end
        e = min(nxt, p[-1][2] + END_HOLD) if i + 1 < len(pgs) else min(video_end, p[-1][2] + END_HOLD)
        spans.append((s, max(e, p[-1][2])))
    return spans


# ---------------------------------------------------------------- alignment of the spoken audio

FRAME = 0.01             # s: loudness frames for trim_silence
QUIET = 0.08             # a frame quieter than this share of the scene's loud frames is silence


def trim_silence(ws, wav):
    """The aligner gives each word a time in steps of 80 ms and sometimes stretches a word over the pause
    before or after it. Moves the start of each word to its first loud frame and the end to its last."""
    import wave
    import numpy as np
    with wave.open(wav, "rb") as w:
        rate = w.getframerate()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767
    n = int(rate * FRAME)
    if len(a) < n:
        return ws
    rms = np.sqrt(np.mean(a[:len(a) // n * n].reshape(-1, n) ** 2, axis=1))
    loud = rms > QUIET * np.percentile(rms, 90)
    out = []
    for x in ws:
        i0, i1 = int(x["s"] / FRAME), min(len(loud), int(np.ceil(x["e"] / FRAME)))
        idx = np.nonzero(loud[i0:i1])[0]
        if len(idx):
            s, e = (i0 + idx[0]) * FRAME, (i0 + idx[-1] + 1) * FRAME
            x = dict(x, s=round(s, 3), e=round(max(e, s + 0.05), 3))
        out.append(x)
    return out

ALIGNER = "Qwen/Qwen3-ForcedAligner-0.6B"
ALIGN_PITFALL = ("The aligner is not installed: word times are estimated. Install it into .venv:\n"
                 "  .venv/bin/pip install --no-deps qwen-asr==0.0.6")


def align(plan, texts, paths, outdir):
    """Writes voice/<id>.words.json for each scene whose audio or text changed: the written words of the
    scene with the times they are heard (Qwen3-ForcedAligner, Apache 2.0, ~1.8 GB on the first run).
    texts: {id: text with [written|spoken] marks}; paths: {id: wav}, fresh (voice.fresh).
    Returns the number of scenes aligned now."""
    from .voice import settings
    lang = settings(plan)["lang"]
    d = os.path.join(outdir, "voice")
    todo = []
    for sid, wav in paths.items():
        text = texts.get(sid, "").strip()
        if _aligned(wav, text) is not None:
            continue
        todo.append((sid, text, wav, os.path.join(d, f"{sid}.words.json")))
    if not todo:
        return 0
    try:
        import torch
        from qwen_asr import Qwen3ForcedAligner
    except ImportError:
        print(ALIGN_PITFALL)
        return 0
    dev = "cuda:0" if torch.cuda.is_available() else "cpu"
    m = Qwen3ForcedAligner.from_pretrained(ALIGNER, dtype=torch.float32, device_map=dev)
    for sid, text, wav, p in todo:
        # "пи-ди-эль-один" as one unit gets too little time: the aligner times each part when they are apart
        unit_text = re.sub(r"(?<=\w)-(?=\w)", " ", spoken(text))
        res = m.align(audio=wav, text=unit_text, language=lang)[0]
        units = [{"text": it.text, "start": float(it.start_time), "end": float(it.end_time)} for it in res.items]
        ws = trim_silence(from_alignment(text, units), wav)
        json.dump({"text": text, "wav_mtime": os.path.getmtime(wav), "aligner": ALIGNER, "words": ws},
                  open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(f"words {sid}: {len(ws)}", flush=True)
    return len(todo)
