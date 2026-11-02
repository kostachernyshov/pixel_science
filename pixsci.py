#!/usr/bin/env python3
# Pixel-art science explainers from a plan, in four video formats.
#
#   uv run --with pillow --with numpy --with pyyaml python3 pixsci.py <command> ...
#
#   formats                                   list the formats and their output sizes
#   sheet     OUT.png                         cast sheet: every sprite of the library
#   check     PLAN                            rules: sources, voice-over, sprites, captions, timing
#   board     PLAN OUTDIR [-f a,b]            storyboard for each format: OUTDIR/board-<format>.png
#   render    PLAN OUTDIR [-f a,b] [--gif]    video for each format: OUTDIR/<name>-<format>.mp4
#   frames    PLAN OUTDIR [-f a,b] [t ...]    single frames as PNG (default: the key frames)
#
# -f limits the formats (default: the plan's "formats", else all four).

import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pixel_kit import explain, frame


def _args(a):
    """Splits -f/--formats and --gif from the positional arguments."""
    pos, fmts, gif = [], None, False
    i = 0
    while i < len(a):
        if a[i] in ("-f", "--formats"):
            fmts = a[i + 1].split(",")
            i += 2
            continue
        if a[i] == "--gif":
            gif = True
        else:
            pos.append(a[i])
        i += 1
    return pos, fmts, gif


def _plan(p):
    return explain.load(p)


def _formats(plan, fmts):
    return fmts or plan.get("formats") or list(frame.FORMATS)


def _name(plan, plan_path):
    return plan.get("name") or os.path.splitext(os.path.basename(plan_path))[0]


def _stop_on_problems(plan):
    problems = explain.check(plan)
    if problems:
        print("CHECK FAILED:")
        for p in problems:
            print(" -", p)
        sys.exit(1)


def cmd_formats(a):
    for name, (w, h) in frame.FORMATS.items():
        print(f"{name:10} {w}x{h} px -> {w * frame.SCALE}x{h * frame.SCALE}")


def cmd_sheet(a):
    import runpy
    sys.argv = ["make_sheet.py", a[0]]
    runpy.run_path(os.path.join(HERE, "tools", "make_sheet.py"), run_name="__main__")


def cmd_check(a):
    plan = _plan(a[0])
    problems = explain.check(plan)
    times = explain.durations(plan)
    for sc, (s, e) in zip(plan["scenes"], times):
        print(f"{sc.get('id', '?'):5} {sc.get('type', '?'):8} {s:6.1f}-{e:6.1f} s  {sc.get('caption', '')}")
    print(f"total {times[-1][1]:.1f} s" if times else "no scenes")
    if problems:
        print("CHECK FAILED:")
        for p in problems:
            print(" -", p)
        sys.exit(1)
    print("CHECK PASSED")


def cmd_board(a):
    pos, fmts, _ = _args(a)
    plan = _plan(pos[0])
    _stop_on_problems(plan)
    os.makedirs(pos[1], exist_ok=True)
    for f in _formats(plan, fmts):
        frame.use(f)
        tl, marks = explain.timeline(plan)
        cols = 3 if frame.W >= frame.H else 4
        out = os.path.join(pos[1], f"board-{f}.png")
        tl.storyboard(out, [t for t, _ in marks], cols=cols, labels=[m.split()[0] for _, m in marks])
        print("board ->", out)


def cmd_render(a):
    pos, fmts, gif = _args(a)
    plan = _plan(pos[0])
    _stop_on_problems(plan)
    os.makedirs(pos[1], exist_ok=True)
    name = _name(plan, pos[0])
    for f in _formats(plan, fmts):
        frame.use(f)
        tl, _ = explain.timeline(plan)
        out = os.path.join(pos[1], f"{name}-{f}.mp4")
        print(f"[{f}] {frame.out_size()[0]}x{frame.out_size()[1]}")
        tl.render(out)
        print("video ->", out)
        if gif:
            g = os.path.join(pos[1], f"{name}-{f}.gif")
            tl.gif(g)
            print("gif ->", g)


def cmd_frames(a):
    pos, fmts, _ = _args(a)
    plan = _plan(pos[0])
    for f in _formats(plan, fmts):
        frame.use(f)
        tl, marks = explain.timeline(plan)
        times = [float(x) for x in pos[2:]] or [t for t, _ in marks]
        for p in tl.export_frames(os.path.join(pos[1], f), times):
            print(p)


COMMANDS = {k[4:]: v for k, v in globals().items() if k.startswith("cmd_")}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(open(__file__).read().split("\n\n")[0])
        sys.exit(2)
    COMMANDS[sys.argv[1]](sys.argv[2:])
