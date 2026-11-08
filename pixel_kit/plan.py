# A plan (explainer.yaml) and what is derived from it once: word times, scene lengths of the voice, the beats as
# they play (stage.resolve), the model's world. The format is not part of it (docs/adr/0003).
#
#   from pixel_kit import plan as P
#   plan = P.load("my-video/explainer.yaml", outdir)   # prepared: plan.problems, plan.words, ...
#   plan["scenes"]                                     # the file's fields, as in the YAML

import os
from . import explain, frame, sprites as S, stage, verbs, voice, words as WD


class Plan(dict):
    """The fields of the plan file, plus what load derives from them. Two plans in one process are independent,
    except the packs they use (sprites.use, verbs.use: #70)."""

    def __init__(self, data, dir, outdir=None):
        super().__init__(data)
        self.dir = dir              # the plan file's folder: paths in the plan are relative to it
        self.outdir = outdir        # where voice/ is: the voice and its word times
        self.wavs = {}              # {scene id: wav}: the fresh voice of a scene (voice.fresh)
        self.spoken = {}            # {scene id: s}: how long it lasts
        self.stale = []             # scenes with text and no fresh voice, in a folder that has a voice
        self.words = {}             # {scene id: [{"w", "s", "e"}]}: when each word is heard (words.attach)
        self.problems = []          # what preparing found
        self.placed = {}            # stage: contact places per (scene, format)
        self.resolved = False       # True once stage.resolve has made the beats as they play
        self.world = None           # model.world, kept once the plan is resolved


def load(path, outdir=None, speak=False):
    """The plan of the file at path, prepared, in the order of the work: text, voice, timing. Scenes with a fresh
    voice in OUTDIR/voice/ last as long as it, and their words are aligned to it; other scenes are estimated.
    Then beats go on their words and the plan is resolved as it plays (stage.resolve: continue, behaviors).
    speak: first speak and align what has no fresh voice (Qwen3-TTS, Qwen3-ForcedAligner); the models' output
    goes to OUTDIR/voice/log.txt."""
    import yaml
    plan = Plan(yaml.safe_load(open(path, encoding="utf-8")), os.path.dirname(os.path.abspath(path)), outdir)
    plan.setdefault("scenes", [])
    plan.setdefault("lang", "en")
    plan.setdefault("formats", list(frame.FORMATS))
    S.use(plan.get("packs"))              # packs: [biology]; without it, every pack
    verbs.use(plan.get("packs"))
    texts = explain.voiceover(plan)
    said = {k: WD.spoken(v) for k, v in texts.items()}
    if speak:
        with voice.quiet(os.path.join(outdir, "voice", "log.txt")):
            vo = voice.speak(plan, said)
            n = WD.align(plan, texts, vo.wavs)
        if n:
            print(f"word times: {n} scenes aligned")
    else:
        vo = voice.fresh(plan, said)
    plan.wavs, plan.stale, plan.spoken = vo.wavs, vo.stale, voice.lengths(vo.wavs)
    WD.attach(plan, texts, plan.wavs)
    plan.problems = [f"warning: {sid}: voice is missing or older than its text; run pixsci voice" for sid in plan.stale]
    plan.problems += WD.resolve_beats(plan)
    plan.problems += stage.resolve(plan, explain.durations(plan))
    plan.resolved = True
    return plan
