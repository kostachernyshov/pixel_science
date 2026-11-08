# Proves that a change to the core leaves the frames of a plan as they were (CONTRIBUTING.md, Work on the core).
#   python3 tools/frame_hashes.py PLAN OUT.json [BEFORE.json]
# Builds the frames as `pixsci render` does (check, then a timeline per format), 12 per second, in all four
# formats (whatever the plan's `formats:`), and writes to OUT.json
#   {"check": [...], "frames": {"<format> <frame> <scene>": hash}}
# Subtitles replace the caption, so the formats split the two: vertical and banner (where the subtitle box sits
# apart: above the reel's buttons, on the banner's right third) are hashed with `subtitles: true`, landscape and
# square as the plan has it. A plan that sets `subtitles` keeps its value in all four.
# With BEFORE.json, prints what differs (the check output, then frames grouped by format and scene)
# and exits 1 when anything differs.
import hashlib, json, os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from pixel_kit import explain, frame, plan as P
FPS = 12
SUBTITLED = ("vertical", "banner")


def hashes(path):
    """{"check": problems of explain.check, "frames": {"<format> <frame> <scene>": sha1 of the frame}}."""
    plan = P.load(path)
    out = {"check": explain.check(plan), "frames": {}}
    ids = [(a, b, sc.get("id", "?")) for sc, (a, b) in zip(plan["scenes"], explain.durations(plan))]
    keep = "subtitles" in plan            # the layout reads it per format; places are kept per format
    for f in frame.FORMATS:
        if not keep:
            plan["subtitles"] = f in SUBTITLED
        with frame.using(f):
            tl, _ = explain.timeline(plan)
            for i in range(int(tl.duration * FPS)):
                t = i / FPS
                scene = next((s for a, b, s in ids if a <= t < b), ids[-1][2])
                out["frames"][f"{f} {i:05d} {scene}"] = hashlib.sha1(tl.frame(t).tobytes()).hexdigest()
    return out


def diff(before, after):
    """Lines that name what differs between two outputs of hashes(); empty when they are equal."""
    lines = []
    if before["check"] != after["check"]:
        lines.append("check output differs:")
        lines += [f" - {p}" for p in before["check"] if p not in after["check"]]
        lines += [f" + {p}" for p in after["check"] if p not in before["check"]]
    split = lambda d: {tuple(k.split()[:2]): (k.split()[2], h) for k, h in d["frames"].items()}
    b, a = split(before), split(after)
    groups = defaultdict(list)                 # (format, scene) -> frames that differ
    for key in sorted(set(b) | set(a)):
        if b.get(key) != a.get(key):
            scene = (a.get(key) or b.get(key))[0]
            groups[(key[0], scene)].append(int(key[1]))
    for (f, scene), frames in sorted(groups.items()):
        lines.append(f"{f} {scene}: {len(frames)} frames differ ({frames[0] / FPS:.2f}-{frames[-1] / FPS:.2f} s)")
    return lines


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(open(__file__).read().split("\nimport")[0])
        sys.exit(2)
    now = hashes(sys.argv[1])
    json.dump(now, open(sys.argv[2], "w"), indent=0, sort_keys=True)
    print(f"{len(now['frames'])} frames -> {sys.argv[2]}")
    if len(sys.argv) == 4:
        lines = diff(json.load(open(sys.argv[3])), now)
        print("\n".join(lines) or "EQUAL")
        sys.exit(1 if lines else 0)
