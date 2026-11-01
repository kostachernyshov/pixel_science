# Word timing: when each word of the voice-over sounds, and so when each scene starts.
#
# Without a recording the words are timed from the text at WORDS_PER_S. With a recording, a
# transcript with word times (pixsci transcribe) is aligned to the voice-over text by fuzzy match;
# each scene starts on its first words, and beats can be keyed to words ("on: attacks").
#
#   from pixel_kit import words
#   tm = words.timing(scenes, texts, transcript_words=None)
#   tm[i]["start"], tm[i]["end"], tm[i]["words"] -> [(word, t)], tm[i]["drift"]
#   words.at(tm[i], "attacks")            time of a word in the scene (s from the video start)

import difflib, re

WORDS_PER_S = 2.7         # voice-over pace without a recording
LEAD = 0.3                # s of picture before the first word of a scene
TAIL = 0.5                # s after the last word
MIN_SCENE = 2.0
FINAL_HOLD = 3.0          # the last frame holds still this long after it has appeared
SUMMARY_IN = 1.5          # the summary appears in this time


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def tokens(text):
    return [(w, norm(w)) for w in text.split() if norm(w)]


def _estimate(scenes, toks):
    out, t = [], 0.0
    for sc, tk in zip(scenes, toks):
        n = len(tk)
        if sc.get("type") == "summary":
            d = max(SUMMARY_IN, LEAD + n / WORDS_PER_S) + FINAL_HOLD
        else:
            d = max(MIN_SCENE, LEAD + n / WORDS_PER_S + TAIL)
        d = float(sc.get("dur", d))
        wt = [(w, t + LEAD + i / WORDS_PER_S) for i, (w, _) in enumerate(tk)]
        out.append(dict(id=sc.get("id"), start=t, end=t + d, words=wt, drift=None))
        t += d
    return out


def _align(script, spoken):
    """script, spoken: lists of normalized words. Returns {script index: spoken index}."""
    sm = difflib.SequenceMatcher(None, script, spoken, autojunk=False)
    m = {}
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            for k in range(a1 - a0):
                m[a0 + k] = b0 + k
        elif op == "replace":
            # near words ("PD-L1" said as "PDL one"): pair them in order when they look alike
            j = b0
            for i in range(a0, a1):
                for jj in range(j, b1):
                    if difflib.SequenceMatcher(None, script[i], spoken[jj]).ratio() >= 0.6:
                        m[i] = jj
                        j = jj + 1
                        break
    return m


def _from_voice(scenes, toks, spoken_words):
    flat = [(si, w, n) for si, tk in enumerate(toks) for (w, n) in tk]
    sp = [norm(w) for w, _, _ in spoken_words]
    keep = [i for i, n in enumerate(sp) if n]
    spn = [sp[i] for i in keep]
    m = {i: keep[j] for i, j in _align([n for _, _, n in flat], spn).items()}
    # a time for every script word: matched -> the spoken time; else between its matched neighbours
    times = [None] * len(flat)
    for i, j in m.items():
        times[i] = spoken_words[j][1]
    known = [i for i, t in enumerate(times) if t is not None]
    for i in range(len(flat)):
        if times[i] is not None:
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        if prev is not None and nxt is not None:
            times[i] = times[prev] + (times[nxt] - times[prev]) * (i - prev) / (nxt - prev)
        elif prev is not None:
            times[i] = times[prev] + (i - prev) / WORDS_PER_S
        elif nxt is not None:
            times[i] = max(0.0, times[nxt] - (nxt - i) / WORDS_PER_S)
        else:
            times[i] = i / WORDS_PER_S
    out, k = [], 0
    for si, (sc, tk) in enumerate(zip(scenes, toks)):
        idx = list(range(k, k + len(tk)))
        k += len(tk)
        wt = [(flat[i][1], times[i]) for i in idx]
        start = 0.0 if si == 0 else ((wt[0][1] - LEAD) if wt else None)
        missing = [flat[i][1] for i in idx if i not in m]
        out.append(dict(id=sc.get("id"), start=start, end=None, words=wt,
                        drift=dict(matched=len(idx) - len(missing), total=len(idx), missing=missing, extra=[])))
    # scenes without words start after the scene before
    for i, s in enumerate(out):
        if s["start"] is None:
            s["start"] = out[i - 1]["start"] + float(scenes[i].get("dur", MIN_SCENE))
        if i and s["start"] < out[i - 1]["start"] + 0.5:
            s["start"] = out[i - 1]["start"] + 0.5
    last_word = spoken_words[-1][2] if spoken_words else 0.0
    for i, s in enumerate(out):
        if i + 1 < len(out):
            s["end"] = out[i + 1]["start"]
        else:
            end = max(last_word, s["words"][-1][1] if s["words"] else s["start"]) + TAIL
            if scenes[i].get("type") == "summary":
                end = max(end, s["start"] + SUMMARY_IN) + FINAL_HOLD
            s["end"] = max(end, s["start"] + float(scenes[i].get("dur", MIN_SCENE)))
    # said but not in the voice-over: spoken words that matched nothing, by the scene they fall in
    used = set(m.values())
    for j, (w, a, _) in enumerate(spoken_words):
        if j in used or not norm(w):
            continue
        for s in out:
            if s["start"] <= a < s["end"]:
                s["drift"]["extra"].append(w)
                break
    return out


def timing(scenes, texts, transcript_words=None):
    """scenes: plan scenes; texts: {scene id: voice-over text}; transcript_words: [(word, start, end)]."""
    toks = [tokens(texts.get(sc.get("id"), "")) for sc in scenes]
    if transcript_words:
        return _from_voice(scenes, toks, transcript_words)
    return _estimate(scenes, toks)


def at(scene_timing, phrase):
    """Time (from the video start) of a word or phrase of the scene's voice-over.
    "attacks" is the first one, "attacks#2" the second. None if it is not in the text."""
    nth = 1
    if "#" in phrase:
        phrase, k = phrase.rsplit("#", 1)
        nth = int(k)
    want = [norm(w) for w in phrase.split() if norm(w)]
    ws = [norm(w) for w, _ in scene_timing["words"]]
    seen = 0
    for i in range(len(ws) - len(want) + 1):
        if ws[i:i + len(want)] == want:
            seen += 1
            if seen == nth:
                return scene_timing["words"][i][1]
    return None


def drift_report(tm):
    """Lines for the person: how far the recording is from the voice-over text."""
    out = []
    for s in tm:
        d = s.get("drift")
        if not d or not d["total"]:
            continue
        share = d["matched"] / d["total"]
        if share < 1 or d["extra"]:
            line = f"{s['id']}: {d['matched']}/{d['total']} words found"
            if d["missing"]:
                line += f"; not said: {' '.join(d['missing'][:8])}"
            if d["extra"]:
                line += f"; said, not in the text: {' '.join(d['extra'][:8])}"
            out.append(line)
    return out
