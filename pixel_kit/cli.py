# pixsci: the command line of pixel_science. The /animate skill runs it; people can too.
# Every command takes --json and then prints one JSON object (ok, and the result or an error).
#
#   pixsci formats                                  formats and their output sizes
#   pixsci packs                                    packs on the search path
#   pixsci styles                                   styles
#   pixsci find WORDS [--kind sprite] [--pack P] [--group G]   search the catalog
#   pixsci catalog [--check]                        write packs/catalog.json (--check: is it fresh?)
#   pixsci sheet OUT.png [--style S] [--pack P]     cast sheet for people
#   pixsci check PLAN [--style S] [--fast]          rules, pace, numbers; --fast skips the motion check
#   pixsci board PLAN OUTDIR [-f a,b] [--style S] [--html] [--styles a,b]
#   pixsci render PLAN OUTDIR [-f a,b] [--style S] [--gif]
#   pixsci frames PLAN OUTDIR [-f a,b] [--style S] [--at t ...]
#   pixsci transcribe PLAN [--model small.en]       local transcript of voice.audio, with word times
#   pixsci align PLAN                               scene starts and word times from the recording; drift
#   pixsci animatic PLAN OUTDIR [-f a,b]            key frames held under the voice (fast)

import argparse, json, os, sys, traceback

from . import explain, frame, packs, style, catalog, words, voice


class Fail(Exception):
    pass


def _formats(plan, fmts):
    return fmts.split(",") if fmts else (plan.get("formats") or list(frame.FORMATS))


def _name(plan, p):
    return plan.get("name") or os.path.splitext(os.path.basename(p))[0]


def _plan(a):
    if not os.path.exists(a.plan):
        raise Fail(f"no plan file {a.plan}")
    plan = explain.load(a.plan)
    explain.prepare(plan, getattr(a, "style", None))
    return plan


def _gate(plan, a):
    probs, warn = explain.check(plan)
    if probs:
        raise Fail("CHECK FAILED:\n" + "\n".join(" - " + p for p in probs))
    return warn


# ---------------------------------------------------------------- commands: each returns (result, text)

def c_formats(a):
    r = {n: {"frame": [w, h], "video": [w * frame.SCALE, h * frame.SCALE]} for n, (w, h) in frame.FORMATS.items()}
    return r, "\n".join(f"{n:10} {v['frame'][0]}x{v['frame'][1]} px -> {v['video'][0]}x{v['video'][1]}" for n, v in r.items())


def c_packs(a):
    r = [{"name": p.name, "kind": p.kind, "description": p.description, "path": p.dir,
          "sprites": len(p.sprites()), "backgrounds": sorted(p.backgrounds())}
         for p in sorted(packs.find().values(), key=lambda p: p.name)]
    return r, "\n".join(f"{p['name']:15} {p['kind']:8} {p['sprites']:3} sprites  {p['description']}" for p in r)


def c_styles(a):
    r = [{"name": n, "pack": p.name, "description": p.style.get("description", "")} for n, p in sorted(packs.styles().items())]
    return r, "\n".join(f"{s['name']:9} {s['description']}" for s in r)


def c_find(a):
    r = catalog.find(" ".join(a.words), kind=a.kind, pack=a.pack, group=a.group)[: a.limit]
    lines = [f"{e['kind']:10} {e['name']:16} {e.get('pack') or 'core':10} "
             f"{', '.join(e.get('anims', [])) if e['kind'] == 'sprite' else ''}" for e in r]
    return r, "\n".join(lines) or "nothing found"


def c_catalog(a):
    if a.check:
        ok = catalog.is_fresh()
        if not ok:
            raise Fail("packs/catalog.json is stale: run pixsci catalog")
        return {"fresh": True}, "catalog is fresh"
    p = catalog.write()
    cat = catalog.build()
    return {"path": p, "sprites": len(cat["sprites"]), "backgrounds": len(cat["backgrounds"]),
            "styles": len(cat["styles"])}, f"catalog -> {p}"


def c_sheet(a):
    p = catalog.sheet(a.out, a.style or "paper", a.pack)
    return {"path": p}, f"sheet -> {p}"


def c_check(a):
    plan = _plan(a)
    probs, warn = explain.check(plan)
    if not a.fast and not probs:
        from . import pace
        probs += pace.motion(plan)
    tm = explain.timing(plan)
    rows = [{"id": sc.get("id"), "type": sc.get("type"), "start": round(s["start"], 2), "end": round(s["end"], 2),
             "caption": sc.get("caption", "")} for sc, s in zip(plan["scenes"], tm)]
    r = {"passed": not probs, "problems": probs, "warnings": warn, "scenes": rows,
         "length": round(tm[-1]["end"], 2) if tm else 0, "timed_from": "voice" if explain.spoken_words(plan) else "text"}
    lines = [f"{x['id']:5} {x['type']:8} {x['start']:6.1f}-{x['end']:6.1f} s  {x['caption']}" for x in rows]
    lines.append(f"total {r['length']:.1f} s (timed from the {r['timed_from']})")
    if warn:
        lines.append("WARNINGS (tell the person before the render):")
        lines += [" - " + w for w in warn]
    if probs:
        lines.append("CHECK FAILED:")
        lines += [" - " + p for p in probs]
    else:
        lines.append("CHECK PASSED")
    return r, "\n".join(lines)


def c_board(a):
    plan = _plan(a)
    warn = _gate(plan, a)
    os.makedirs(a.outdir, exist_ok=True)
    fmts = _formats(plan, a.formats)
    out = {"png": [], "html": None}
    for f in fmts:
        frame.use(f)
        from . import board
        out["png"].append(board.png_board(plan, os.path.join(a.outdir, f"board-{f}.png")))
    if a.html:
        from . import board
        styles = a.styles.split(",") if a.styles else style.names()
        out["html"] = board.html_board(plan, os.path.join(a.outdir, "board.html"), fmts, styles, warn)
    out["warnings"] = warn
    return out, "\n".join(["board -> " + p for p in out["png"]] + (["html -> " + out["html"]] if out["html"] else []))


def c_render(a):
    plan = _plan(a)
    warn = _gate(plan, a)
    os.makedirs(a.outdir, exist_ok=True)
    name = _name(plan, a.plan)
    st = style.current().name
    suffix = "" if st == plan.get("style", "paper") else f"-{st}"
    audio = explain.audio_path(plan)
    out = []
    for f in _formats(plan, a.formats):
        frame.use(f)
        tl, _ = explain.timeline(plan)
        path = os.path.join(a.outdir, f"{name}-{f}{suffix}.mp4")
        tl.render(path, progress=not a.json)
        if audio:
            tmp = path + ".voice.mp4"
            voice.mux(path, audio, tmp)
            os.replace(tmp, path)
        item = {"format": f, "video": path, "size": list(frame.out_size()), "voice": bool(audio)}
        if a.gif:
            item["gif"] = tl.gif(os.path.join(a.outdir, f"{name}-{f}{suffix}.gif"))
        out.append(item)
    return {"videos": out, "warnings": warn, "length": round(tl.duration, 2)}, \
        "\n".join(f"video -> {x['video']}" + (f"\ngif -> {x['gif']}" if x.get("gif") else "") for x in out)


def c_frames(a):
    plan = _plan(a)
    out = []
    for f in _formats(plan, a.formats):
        frame.use(f)
        tl, marks = explain.timeline(plan)
        times = a.at or [t for t, _ in marks]
        out += tl.export_frames(os.path.join(a.outdir, f), times)
    return {"frames": out}, "\n".join(out)


def c_transcribe(a):
    plan = explain.load(a.plan)
    audio = explain.audio_path(plan)
    if not audio:
        raise Fail("set voice.audio in the plan to a recording (WAV, MP3, M4A)")
    out = explain.transcript_path(plan)
    voice.transcribe(audio, out, a.model)
    n = len(voice.words(out))
    return {"transcript": out, "words": n, "model": a.model}, f"transcript -> {out} ({n} words)"


def c_align(a):
    plan = _plan(a)
    sw = explain.spoken_words(plan)
    tm = explain.timing(plan)
    rows = [{"id": s["id"], "start": round(s["start"], 2), "end": round(s["end"], 2),
             "words": [[w, round(t - s["start"], 2)] for w, t in s["words"]], "drift": s["drift"]} for s in tm]
    drift = words.drift_report(tm)
    lines = [f"{r['id']:5} {r['start']:6.2f}-{r['end']:6.2f} s  " +
             " ".join(f"{w}@{t:.1f}" for w, t in r["words"][:10]) + (" ..." if len(r["words"]) > 10 else "")
             for r in rows]
    lines.insert(0, "timed from the " + ("recording" if sw else "text (no transcript: pixsci transcribe)"))
    lines += ["drift: " + d for d in drift] or ["no drift: the recording follows the text"]
    return {"timed_from": "voice" if sw else "text", "scenes": rows, "drift": drift}, "\n".join(lines)


def c_animatic(a):
    plan = _plan(a)
    _gate(plan, a)
    os.makedirs(a.outdir, exist_ok=True)
    name = _name(plan, a.plan)
    out = []
    for f in _formats(plan, a.formats):
        frame.use(f)
        tl, marks = explain.timeline(plan)
        p = os.path.join(a.outdir, f"{name}-{f}-animatic.mp4")
        voice.animatic(tl, [0.0] + [t for t, _ in marks], explain.audio_path(plan), p)
        out.append(p)
    return {"animatics": out}, "\n".join("animatic -> " + p for p in out)


# ---------------------------------------------------------------- parser

def parser():
    ap = argparse.ArgumentParser(prog="pixsci", description="Pixel-art science explainers from a plan.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help):
        p = sub.add_parser(name, help=help)
        p.add_argument("--json", action="store_true", help="print one JSON object")
        p.set_defaults(fn=fn)
        return p

    add("formats", c_formats, "formats and output sizes")
    add("packs", c_packs, "packs on the search path")
    add("styles", c_styles, "styles")
    p = add("find", c_find, "search sprites, backgrounds, styles")
    p.add_argument("words", nargs="*")
    p.add_argument("--kind", choices=["sprite", "background", "style"])
    p.add_argument("--pack")
    p.add_argument("--group")
    p.add_argument("--limit", type=int, default=30)
    p = add("catalog", c_catalog, "write packs/catalog.json")
    p.add_argument("--check", action="store_true")
    p = add("sheet", c_sheet, "cast sheet PNG")
    p.add_argument("out")
    p.add_argument("--style")
    p.add_argument("--pack")
    for name, fn, help, outdir in (("check", c_check, "check a plan", False), ("board", c_board, "storyboards", True),
                                   ("render", c_render, "render videos", True), ("frames", c_frames, "single frames", True),
                                   ("transcribe", c_transcribe, "transcript of the recording", False),
                                   ("align", c_align, "align the recording to the text", False),
                                   ("animatic", c_animatic, "animatic under the voice", True)):
        p = add(name, fn, help)
        p.add_argument("plan")
        if outdir:
            p.add_argument("outdir")
            p.add_argument("-f", "--formats")
        p.add_argument("--style")
    sub.choices["check"].add_argument("--fast", action="store_true", help="skip the motion check")
    sub.choices["board"].add_argument("--html", action="store_true", help="also board.html with all styles")
    sub.choices["board"].add_argument("--styles", help="styles in board.html (default: all)")
    sub.choices["render"].add_argument("--gif", action="store_true")
    sub.choices["frames"].add_argument("--at", type=float, nargs="*")
    sub.choices["transcribe"].add_argument("--model", default=voice.MODEL)
    return ap


def main(argv=None):
    a = parser().parse_args(argv)
    try:
        r, txt = a.fn(a)
        ok = not (isinstance(r, dict) and r.get("passed") is False)
        if a.json:
            print(json.dumps({"ok": ok, "command": a.cmd, "result": r}, ensure_ascii=False, indent=1))
        else:
            print(txt)
        return 0 if ok else 1
    except (Fail, packs.PackError, KeyError, ValueError, FileNotFoundError) as e:
        msg = str(e).strip("'\"")
        if a.json:
            print(json.dumps({"ok": False, "command": a.cmd, "error": msg}, ensure_ascii=False, indent=1))
        else:
            print(msg, file=sys.stderr)
            if os.environ.get("PIXSCI_DEBUG"):
                traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
