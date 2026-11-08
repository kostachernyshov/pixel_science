# A plan (explainer.yaml) and what is derived from it once: word times, scene lengths of the voice, the beats as
# they play (stage.resolve), the model's world. The format is not part of it (docs/adr/0003).
#
#   from pixel_kit import plan as P
#   plan = P.load("my-video/explainer.yaml", outdir)   # prepared: plan.problems, plan.words, ...
#   plan["scenes"]                                     # the file's fields, as in the YAML

import os
from . import explain, frame, sprites as S, stage, verbs, words as WD


class Plan(dict):
    """The fields of the plan file, plus what load derives from them. Two plans in one process are independent."""

    def __init__(self, data, dir, outdir=None, spoken=None):
        super().__init__(data)
        self.dir = dir              # the plan file's folder: paths in the plan are relative to it
        self.outdir = outdir        # where voice/ is: the voice and its word times
        self.spoken = dict(spoken or {})   # {scene id: s}: length of the scene's audio
        self.words = {}             # {scene id: [{"w", "s", "e"}]}: when each word is heard (words.attach)
        self.problems = []          # what preparing found
        self.placed = {}            # stage: contact places per (scene, format)
        self.resolved = False       # True once stage.resolve has made the beats as they play
        self.world = None           # model.world, kept once the plan is resolved


def load(path, outdir=None, spoken=None):
    """The plan of the file at path, prepared: words in time (aligned in OUTDIR/voice/, or estimated), beats on
    their words, then the plan as it plays (stage.resolve: continue, behaviors). spoken: {scene id: s} of audio."""
    import yaml
    plan = Plan(yaml.safe_load(open(path, encoding="utf-8")), os.path.dirname(os.path.abspath(path)), outdir, spoken)
    plan.setdefault("scenes", [])
    plan.setdefault("lang", "en")
    plan.setdefault("formats", list(frame.FORMATS))
    S.use(plan.get("packs"))              # packs: [biology]; without it, every pack
    verbs.use(plan.get("packs"))
    WD.attach(plan, explain.voiceover(plan), outdir)
    plan.problems = WD.resolve_beats(plan)
    plan.problems += stage.resolve(plan, explain.durations(plan))
    plan.resolved = True
    return plan
