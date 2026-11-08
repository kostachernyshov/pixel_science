#!/usr/bin/env python3
# Pixel-art science explainers from a plan, in four video formats.
#
#   uv run --with pillow --with numpy --with pyyaml python3 pixsci.py <command> ...
#
#   doctor                                    what the tool needs (Python, ffmpeg, packs, voice) and what is missing
#   formats                                   list the formats and their output sizes
#   sheet     OUT.png                         cast sheet: every sprite of the library
#   verbs     [OUT.png] [-p pack,...]       verbs (actions for beats); OUT.png: a contact sheet of each verb
#   check     PLAN [OUTDIR]                   rules: sources, voice-over, sprites, captions, timing (OUTDIR: its voice)
#   board     PLAN OUTDIR [-f a,b]            storyboard for each format: OUTDIR/board-<format>.png
#   render    PLAN OUTDIR [-f a,b] [--gif]    video for each format: OUTDIR/<name>-<format>.mp4
#   frames    PLAN OUTDIR [-f a,b] [t ...]    single frames as PNG (default: the key frames)
#   voice     PLAN OUTDIR                     voice-over spoken (Qwen3-TTS) and its words timed: OUTDIR/voice/
#
# -f limits the formats (default: the plan's "formats", else all four).
# Scenes and word beats are timed to the fresh voice in OUTDIR/voice/ when it is there.
# --voice (board, render, frames): first speak and align what is missing; render puts the sound in the mp4.

import contextlib, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pixel_kit import explain, frame, plan as P


def _args(a):
    """Splits -f/--formats, --gif, and --voice from the positional arguments."""
    pos, fmts, gif, vo = [], None, False, False
    i = 0
    while i < len(a):
        if a[i] in ("-f", "--formats"):
            fmts = a[i + 1].split(",")
            i += 2
            continue
        if a[i] == "--gif":
            gif = True
        elif a[i] == "--voice":
            vo = True
        else:
            pos.append(a[i])
        i += 1
    return pos, fmts, gif, vo


@contextlib.contextmanager
def _quiet(log):
    """Sends stderr (progress bars and warnings of torch and Hugging Face) to the file log, one run per file;
    stdout stays. An agent reads only the short result, not thousands of progress lines."""
    if sys.stderr:
        sys.stderr.flush()
    f = open(log, "w")
    keep = os.dup(2)
    os.dup2(f.fileno(), 2)
    try:
        yield
    except BaseException as e:
        stop = not (isinstance(e, SystemExit) and e.code in (None, 0))
        raise
    else:
        stop = False
    finally:
        if sys.stderr:
            sys.stderr.flush()
        os.dup2(keep, 2)
        os.close(keep)
        f.close()
        if stop and os.path.getsize(log):
            print(f"voice: stopped; details in {log}", file=sys.stderr)


def _plan(p, outdir=None, speak=False):
    """The plan, timed to the fresh voice in OUTDIR/voice/. speak (--voice): first speak and align what is missing;
    model output goes to OUTDIR/voice/log.txt."""
    if not speak:
        return P.load(p, outdir)
    os.makedirs(os.path.join(outdir, "voice"), exist_ok=True)
    with _quiet(os.path.join(outdir, "voice", "log.txt")):
        return P.load(p, outdir, speak=True)


def _warn(plan):
    for w in _split(plan.problems)[1]:
        if " voice " in w:
            print(w)


def _formats(plan, fmts):
    return fmts or plan.get("formats") or list(frame.FORMATS)


def _name(plan, plan_path):
    return plan.get("name") or os.path.splitext(os.path.basename(plan_path))[0]


def _split(problems):
    """(errors, warnings): a problem that starts with "warning:" does not stop a render."""
    return [p for p in problems if not p.startswith("warning:")], [p for p in problems if p.startswith("warning:")]


def _stop_on_problems(plan):
    problems, warnings = _split(explain.check(plan))
    for w in warnings:
        print(w)
    if problems:
        print("CHECK FAILED:")
        for p in problems:
            print(" -", p)
        sys.exit(1)


def cmd_doctor(a):
    """Prints what the tool finds, then READY or NOT READY. Voice is optional: it never makes NOT READY."""
    import importlib.util, shutil
    from pixel_kit import packs
    have = lambda m: importlib.util.find_spec(m) is not None
    ready = True
    print(f"python  {sys.version.split()[0]} ({sys.executable})")
    ff = os.environ.get("PIXSCI_FFMPEG") or shutil.which("ffmpeg") or ("imageio-ffmpeg" if have("imageio_ffmpeg") else None)
    print(f"ffmpeg  {ff or 'MISSING: brew install ffmpeg, apt install ffmpeg, or pip install imageio-ffmpeg'}")
    ready = ready and bool(ff)
    found = packs.find()
    print(f"packs   {', '.join(found) or 'NONE'} ({os.pathsep.join(packs.search_path())})")
    ready = ready and bool(found)
    missing = [m for m in ("torch", "qwen_tts", "qwen_asr") if not have(m)]
    if missing:
        print(f"voice   not installed (optional; missing {', '.join(missing)}): docs/tool.md, Voice and subtitles")
    else:
        import torch
        dev = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"voice   ready (torch {torch.__version__}, {dev})")
    if not (3, 10) <= sys.version_info[:2] <= (3, 12):
        print("        the voice packages need Python 3.10 to 3.12")
    print("READY" if ready else "NOT READY")
    sys.exit(0 if ready else 1)


def cmd_formats(a):
    for name, (w, h) in frame.FORMATS.items():
        print(f"{name:10} {w}x{h} px -> {w * frame.SCALE}x{h * frame.SCALE}")


def cmd_sheet(a):
    import runpy
    sys.argv = ["make_sheet.py", a[0]]
    runpy.run_path(os.path.join(HERE, "tools", "make_sheet.py"), run_name="__main__")


def cmd_verbs(a):
    from pixel_kit import verbs, fx
    pos, packs_, _, _ = _args([x if x != "-p" else "-f" for x in a])
    verbs.use(packs_)
    for name, v in sorted(verbs.all().items(), key=lambda kv: (kv[1]["pack"] != "core", kv[1]["pack"], kv[0])):
        tgt = " target" if v.get("target") else ""
        print(f"{v['pack']:10} {name:12}{tgt:8} {v.get('desc', '')}")
    if not pos:
        return
    from PIL import Image, ImageDraw
    from pixel_kit.font import text
    names = sorted(verbs.all())
    cw, ch, n = 160, 90, 6
    sheet = Image.new("RGB", (80 + cw * n, ch * len(names)), (251, 250, 247))
    for row, name in enumerate(names):
        text(sheet, 4, row * ch + ch // 2 - 4, name, 1)
        d = verbs.duration(name)
        for i in range(n):
            img = Image.new("RGB", (cw, ch), (251, 250, 247))
            base = img.copy()
            dr = ImageDraw.Draw(img)
            for x in (40, 120):                            # two grey stand-ins: actor, target
                dr.ellipse([x - 12, 33, x + 12, 57], fill=(194, 195, 199), outline=(95, 87, 79))
            cv = fx.Canvas(img, base)
            verbs.play(cv, name, d * i / (n - 1) * 0.98, {"actor": (40, 45, 12), "target": (120, 45, 12)}, seed=1)
            sheet.paste(cv.image(), (80 + i * cw, row * ch))
    sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
    sheet.save(pos[0])
    print("sheet ->", pos[0])


def cmd_check(a):
    plan = _plan(a[0], a[1] if len(a) > 1 else None)
    problems, warnings = _split(explain.check(plan))
    times = explain.durations(plan)
    for sc, (s, e) in zip(plan["scenes"], times):
        print(f"{sc.get('id', '?'):5} {sc.get('type', '?'):8} {s:6.1f}-{e:6.1f} s  {sc.get('caption', '')}")
    print(f"total {times[-1][1]:.1f} s" if times else "no scenes")
    for w in warnings:
        print(w)
    if problems:
        print("CHECK FAILED:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("CHECK PASSED")


def cmd_board(a):
    pos, fmts, _, vo = _args(a)
    plan = _plan(pos[0], pos[1], vo)
    _stop_on_problems(plan)
    os.makedirs(pos[1], exist_ok=True)
    for f in _formats(plan, fmts):
        with frame.using(f):
            tl, marks = explain.timeline(plan)
            cols = 3 if frame.W >= frame.H else 4
            out = os.path.join(pos[1], f"board-{f}.png")
            tl.storyboard(out, [t for t, _ in marks], cols=cols, labels=[m.split()[0] for _, m in marks])
        print("board ->", out)


def cmd_render(a):
    pos, fmts, gif, vo = _args(a)
    plan = _plan(pos[0], pos[1], vo)
    _stop_on_problems(plan)
    os.makedirs(pos[1], exist_ok=True)
    name = _name(plan, pos[0])
    track = None
    if vo and plan.wavs:
        from pixel_kit import voice
        track = voice.mix(plan, plan.wavs, explain.durations(plan), os.path.join(pos[1], f"{name}-voice.wav"))
    for f in _formats(plan, fmts):
        with frame.using(f):
            tl, _ = explain.timeline(plan)
            out = os.path.join(pos[1], f"{name}-{f}.mp4")
            print(f"[{f}] {frame.out_size()[0]}x{frame.out_size()[1]}")
            tl.render(out)
            if track:
                voice.mux(out, track)
            print("video ->", out)
            if gif:
                g = os.path.join(pos[1], f"{name}-{f}.gif")
                tl.gif(g)
                print("gif ->", g)


def cmd_frames(a):
    pos, fmts, _, vo = _args(a)
    plan = _plan(pos[0], pos[1], vo)
    _warn(plan)
    for f in _formats(plan, fmts):
        with frame.using(f):
            tl, marks = explain.timeline(plan)
            times = [float(x) for x in pos[2:]] or [t for t, _ in marks]
            for p in tl.export_frames(os.path.join(pos[1], f), times):
                print(p)


def cmd_voice(a):
    from pixel_kit import voice
    pos, _, _, _ = _args(a)
    os.makedirs(pos[1], exist_ok=True)
    plan = _plan(pos[0], pos[1], speak=True)
    if not plan.wavs:
        print("no voice-over text: check `voiceover:` in the plan")
        sys.exit(1)
    times = explain.durations(plan)
    for sc, (s, e) in zip(plan["scenes"], times):
        print(f"{sc.get('id', '?'):5} {s:6.1f}-{e:6.1f} s")
    out = voice.mix(plan, plan.wavs, times, os.path.join(pos[1], f"{_name(plan, pos[0])}-voice.wav"))
    print("voice ->", out)


COMMANDS = {k[4:]: v for k, v in globals().items() if k.startswith("cmd_")}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(open(__file__).read().split("\n\n")[0])
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
