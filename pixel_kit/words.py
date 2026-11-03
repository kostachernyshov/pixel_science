# Words of the voice-over in time: what is said, when, and the subtitles drawn from it.
#
#   voiceover.md may write a word one way and say it another: [PD-L1|пи-ди-эль один].
#   written(text)  the text for the screen ("PD-L1")      spoken(text)  the text for the voice
#
#   voice/<scene>.words.json  [{"w": "PD-L1", "s": 1.20, "e": 1.85}, ...]  (s, e: seconds in the scene's wav)
#   comes from align.py (forced alignment of the spoken text to the wav). Without it, times are estimated.
#
#   A beat can start on a word: {word: "тормоз", dt: -0.3, actor: t, verb: alert}  (n: 2 for the 2nd time)
#   subtitles: true in the plan draws the words in a box at the bottom, each word when it is heard.

import json, os, re

MARK = re.compile(r"\[([^\]|]+)\|([^\]]+)\]")
EST_WPS = 2.5            # words a second, when there is no alignment
LEAD = 0.25              # the same as voice.LEAD: silence before the words of a scene


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


def load_scene(outdir, sid, text):
    """Words of one scene with times in the scene's wav: aligned if voice/<sid>.words.json fits the text."""
    p = os.path.join(outdir, "voice", f"{sid}.words.json") if outdir else None
    if p and os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        if d.get("text") == text:
            return d["words"], True
    return estimate(text), False


def attach(plan, texts, outdir=None):
    """Puts the words of each scene into plan["_words"] = {scene id: [{"w","s","e"}]}, with times from
    the start of the scene (LEAD added). Returns the number of aligned scenes."""
    out, n = {}, 0
    for sc in plan["scenes"]:
        sid = sc.get("id")
        text = texts.get(sid, "").strip()
        if not text:
            continue
        ws, ok = load_scene(outdir, sid, text)
        n += ok
        out[sid] = [{"w": w["w"], "s": w["s"] + LEAD, "e": w["e"] + LEAD} for w in ws]
    plan["_words"] = out
    return n


# ---------------------------------------------------------------- beats on words

def word_time(words, key, n=1):
    """Start of a word in the scene: key is an index (0 = first word) or a word ("тормоз" matches
    "тормоза": the start of the word is enough). n: the n-th time it is said."""
    if isinstance(key, int):
        return words[key]["s"] if 0 <= key < len(words) else None
    k = norm(str(key))
    seen = 0
    for w in words:
        if norm(w["w"]).startswith(k):
            seen += 1
            if seen == n:
                return w["s"]
    return None


def cue(plan, sc, key, n=1, dt=0.0, default=0.0):
    """For custom scenes: the time in the scene when a word is heard (see word_time), plus dt."""
    t = word_time((plan.get("_words") or {}).get(sc.get("id")) or [], key, n)
    return default if t is None else t + dt


def resolve_beats(plan):
    """Sets t of each beat with `word:` from the words of its scene. Returns problems (strings)."""
    words = plan.get("_words") or {}
    problems = []
    for sc in plan["scenes"]:
        ws = words.get(sc.get("id")) or []
        for b in sc.get("beats") or []:
            if "word" not in b:
                continue
            t = word_time(ws, b["word"], int(b.get("n", 1)))
            if t is None:
                problems.append(f"{sc.get('id')}: beat word {b['word']!r} is not in the voice-over of the scene")
                continue
            b["t"] = round(max(0.0, t + float(b.get("dt", 0))), 3)
    return problems


# ---------------------------------------------------------------- subtitles

GAP_BREAK = 0.45         # s: a pause this long starts a new page
END_HOLD = 0.7           # s: a page stays after its last word (if the next page has not begun)


def timeline_words(plan, times):
    """All words in video time: [(word, start, end)]. times: explain.durations(plan)."""
    words = plan.get("_words") or {}
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

LANGS = {"ru": "Russian", "en": "English", "de": "German", "fr": "French", "es": "Spanish"}


def align(plan, texts, paths, outdir):
    """Writes voice/<id>.words.json for each scene whose audio or text changed: the written words of
    the scene with the times they are heard. texts: {id: text with [written|spoken] marks};
    paths: {id: wav} from voice.attach. Returns the number of scenes aligned now."""
    from . import align as AL
    lang = (plan.get("tts") or {}).get("lang") or LANGS.get(plan.get("lang", "en"), "English")
    d = os.path.join(outdir, "voice")
    jobs, todo = [], []
    for sid, wav in paths.items():
        text = texts.get(sid, "").strip()
        p = os.path.join(d, f"{sid}.words.json")
        if os.path.exists(p):
            old = json.load(open(p, encoding="utf-8"))
            if old.get("text") == text and old.get("wav_mtime") == os.path.getmtime(wav):
                continue
        # "пи-ди-эль-один" as one unit gets too little time: the aligner times each part when they are apart
        unit_text = re.sub(r"(?<=\w)-(?=\w)", " ", spoken(text))
        jobs.append({"wav": os.path.abspath(wav), "text": unit_text, "lang": lang,
                     "out": os.path.join(d, f"{sid}.units.json")})
        todo.append((sid, text, wav, p))
    if not AL.run(jobs, d):
        return 0
    for (sid, text, wav, p), j in zip(todo, jobs):
        units = json.load(open(j["out"], encoding="utf-8"))
        ws = trim_silence(from_alignment(text, units), wav)
        json.dump({"text": text, "wav_mtime": os.path.getmtime(wav), "aligner": AL.MODEL, "words": ws},
                  open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return len(todo)
