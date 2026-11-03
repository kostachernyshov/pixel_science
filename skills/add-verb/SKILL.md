---
name: add-verb
description: Add a missing action (a verb) for the beats of a pixel_science scene, in the right place - a pack verb in YAML, a new primitive in the core, or a sprite animation. Use when a plan needs an action that `pixsci.py verbs` does not list, or when `pixsci.py check` says a verb is missing.
---

# Add a verb

Terms (see `GLOSSARY.md`): a **beat** names a **verb**; a verb is YAML in a **pack** and lists **primitives**;
a primitive is a Python function in the **core** (`pixel_kit/fx.py`) with no topic.

## Where the tool is

- Installed as a plugin: `ROOT` is `${CLAUDE_PLUGIN_ROOT}` and `VENV` is `${CLAUDE_PLUGIN_DATA}/venv`.
- If these two are empty or read literally as `${...}`, the skill runs from a clone of the repo:
  `ROOT` is the repo root and `VENV` is `ROOT/.venv`.
- Run the tool from the person's working folder: `"VENV/bin/python" "ROOT/pixsci.py" <command> ...`.
  Below, `pixsci.py <command>` means this. Other paths of the tool (`packs/`, `pixel_kit/`, README.md,
  CONTRIBUTING.md, GLOSSARY.md) are under `ROOT`.
- No `VENV/bin/python`, no ffmpeg (`pixsci.py formats` says so), or a video with a voice and no voice packages:
  run the `setup` skill first, then come back.
- In an installed plugin, `ROOT` is replaced at each update, so a verb written there is lost. Write it in a
  clone of the repo (and offer it as a pull request, CONTRIBUTING.md), or in a pack of the person's own:
  `packs/<name>/pack.yaml` and `verbs.yaml` in the working folder, with `PIXSCI_PACKS=packs` before each command.

```
Scene needs an action
 │
 ├─ A verb exists (pixsci.py verbs)? ── yes ──► use it
 │
 └─ no
     ├─ Can primitives of the core draw it? ── yes ──► new verb in packs/<pack>/verbs.yaml (YAML only)
     │
     └─ no
         ├─ Motion with no topic (a stream, a wave, a crack)?
         │      └─ yes ──► new primitive in pixel_kit/fx.py ── ask the person first ──► then the verb
         │
         └─ A shape with a topic (a cell divides, a B cell releases antibodies)?
                └─ yes ──► a sprite animation in the pack (CONTRIBUTING.md), not a verb

A verb with no topic that two packs or more need ──► move it to pixel_kit/verbs.yaml (core verbs)
```

## Rules

- **The meaning stays in the pack.** A pack has only verbs that exist in its subject. Biology has no
  fire, ice, magic, or explosions; cell death by an immune cell is `apoptosis`, not a blast. Physics can
  have `collide` or `decay`. The same primitive can serve both: `jet` is granzymes in biology, a beam in physics.
- **Do not stop the video for a verb.** When a plan needs a verb, add it to the pack and go on. Tell the
  person in the summary of the video which verbs you added.
- **A new primitive needs the person's "yes".** It is Python in the core. Before you add it, show the
  contact sheet and say why the primitives that exist cannot draw the action.
- **No coordinates and no colors in a verb.** Place comes from the actors (`at`, `from`/`to`); color is a
  role (`granule`), defined under `colors:` of the same `verbs.yaml`. A palette name, never a hex.
- **One place for verbs.** A verb for one video also goes into the pack, so the next video can use it.

## Steps: a verb (YAML)

1. Read `pixel_kit/verbs.yaml` (the format, the core verbs) and the pack's `verbs.yaml`.
2. Write the verb in `packs/<pack>/verbs.yaml`: `desc` (what the viewer sees), `target: true` if it acts on
   another actor, `steps` (primitives with `at` or `from`/`to`, `color`, `t`, `dur`, options), optional
   `hit` (`at`, `preset: soft|normal|heavy`, `by: actor|target`), `show` or `hide`.
   ```yaml
   secrete:
     desc: The actor releases granules at the target; they hit it.
     target: true
     hit: {at: 0.22, preset: soft}
     steps:
       - {prim: jet, from: actor, to: target, color: granule, dur: 0.6}
       - {prim: sparks, at: target, color: granule, t: 0.22, dur: 0.6, n: 6}
   ```
3. Run `pixsci.py verbs out/verbs.png` and look at the verb's row. Fix the worst thing, draw again.
4. Run `pixsci.py check <plan>`: no error, no speed warning for the verb.

## Steps: a primitive (Python, with the person's "yes")

1. Read the contract at the top of `pixel_kit/fx.py`. A primitive is `fn(cv, t, g, ramp, o)`: the frame
   comes from `t` and `o["seed"]` only; it draws nothing when `t < 0` or `t > o["dur"]`; it uses numpy.
2. Use the techniques of pixelfx and Sprite Fusion (MIT): lines and light, not fills; a bright core and dark
   edges; light from `cv.lamp` on every bright point; fast start, slow end; a flash on contact.
3. Add it to `PRIMS`, use it in a verb, draw the contact sheet, and look at it. Three rounds or more.
4. `pixsci.py check` warns when a verb takes more than 5 ms a frame. Keep it under.

## Done when

- `pixsci.py verbs` lists the verb, and its row on the contact sheet shows the action.
- `pixsci.py check <plan>` prints `CHECK PASSED` with no speed warning.
