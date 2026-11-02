# explainer.yaml format

Paths are relative to the plan file. Full examples: `examples/anti-pdl1/`, `examples/higgs-boson/`.

```yaml
title: "How NK cells find cancer"     # the summary heading and the storyboard page
name: nk-missing-self                 # output files: <name>-<format>.mp4
lang: en                              # en: on-screen text is plain ASCII
packs: [biology]                      # content packs, bottom -> top; a higher pack overrides a lower one
style: paper                          # paper | arcade | gameboy (pixsci styles); render --style overrides
voiceover: voiceover.md               # '## S01' headings, the text to read under each
formats: [landscape, vertical, square, banner]
seed: 7                               # generators: the same seed gives the same video
max_s: 60                             # optional: longest story before the summary (default 60 s)
sources:                              # required: the papers or textbooks behind each claim
  - "Author A. Title. Journal Year;Vol:Pages. doi:..."
model:                                # the mechanism: what takes part and every link, with its source
  things:                             #   (see "The mechanism model" below)
    t:     {sprite: killer_t, label: "KILLER T CELL", parts: {pd1: {label: "PD-1", color: LGREY}}}
    tumor: {sprite: tumor_pdl1, label: "TUMOR CELL", parts: {pdl1: {label: "PD-L1", color: PINK}}}
  links:
    brake: {kind: bind, a: pd1, b: pdl1, source: 1}
numbers:                              # each number shown on screen, with its source
  "125 GeV": "CMS Phys Lett B 2012;716:30-61"
voice:                                # optional: only with a recording
  audio: voice.m4a                    # pixsci transcribe writes voice.words.json next to it
scenes:
  - id: S01
    type: title
    ...
```

## Formats

| Name | Frame | Video | Use |
|---|---|---|---|
| `landscape` | 480x270 | 1920x1080 | YouTube, slides |
| `vertical` | 270x480 | 1080x1920 | Reels, Shorts, TikTok |
| `square` | 270x270 | 1080x1080 | feed posts |
| `banner` | 480x120 | 1920x480 | site header, wide banner |

One plan renders in every format. Layout is relative: items in a row become a grid in a tall frame,
a flow turns from left-to-right to top-to-bottom, captions shrink or wrap. In `vertical`, the caption
sits above the bottom 20 % (apps cover it). In `banner`, there is no heading and no actor labels.

## Timing

Each scene lasts as long as its words: 0.3 s, then the words at 2.7 words/s, then 0.5 s; 2 s at least.
With `voice`, scenes start on their first spoken words (fuzzy match of the text to the transcript).
`dur: 4` sets a scene by hand. The summary holds still 3 s after it appears.

Anything timed in a scene (a beat, a generator, a camera move) takes `t` (s from the scene start) or
`on: <word>` (that word of the scene's voice-over; `on: "cell#2"` is the second "cell"; `offset: -0.2`
shifts it). Prefer `on`: it stays right when the voice changes.

## Pace (pixsci check)

- A shot lasts 2 to 4 s. A scene starts a shot; inside a scene, a camera zoom or pan starts the next.
- In an action scene something new happens at least every 1.5 s: a beat, a generator, the camera.
- Something moves in every frame (check renders the video small and finds still stretches over 0.5 s).
- The story before the summary lasts 20 to 60 s.

## Fields of all scenes

| Field | Meaning |
|---|---|
| `id` | Unique id, the same as the heading in `voiceover.md`. |
| `type` | `title`, `cast`, `action`, `contact`, `fact`, `flow`, `summary`, `custom`. The last scene is a `summary`. |
| `caption` | 1 to 3 words at the bottom, on screen 2 s or more. |
| `title` | Short heading at the top left (not in `banner`). |
| `bg` | A background: `paper` (default), `plain`, or one of a pack (`pixsci find --kind background`). |
| `fade` | `false`: no dissolve into this scene (one continuous shot). |
| `key` | 0..1: where in the scene the storyboard takes its frame (default 0.75). |

Colors by name: `favorable` (blue), `unfavorable` (orange), `neutral` (grey), with `2` and `3` shades,
and `ink`, `accent`. Blue and orange, not green and red: people with red-green color blindness tell them apart.
Generators and fields take palette names (`LAV`, `BLUE`, `PLUM`, ...).

## Scene types

### title
`title` (A-Z, 0-9, `- ! . ? :`, about 13 characters at most for the vertical frame), `sub`, `credit`.

### cast
`items`: up to 4 of `{sprite, label, color, anim, scale}`. The characters of the story.

### action
Actors on a stage, timed beats, generators, effects, and a camera. Positions are fractions of the stage
(x, y from 0 to 1); keep x between 0.1 and 0.9 for the narrow vertical frame.

```yaml
scale: 3                                                       # sprite scale of the scene (default 2)
actors:
  t:     {sprite: killer_t, at: [0.2, 0.55], badge: badge_pd1}
  tumor: {sprite: tumor_pdl1, at: [0.72, 0.55], anim: pdl1_up, hold: 0}   # hold: show one frame (still breathes)
beats:
  - {t: 0.2, actor: t, move_to: [0.45, 0.55], dur: 1.0}        # move with easing
  - {on: ready, actor: t, anim: alert}                         # change animation (anim + hold: a fixed frame)
  - {on: ready, actor: t, fx: alert}                           # effect: hit, alert, sparkle, particles, wave, zzz, flash
  - {on: stops, actor: t, badge: null}                         # remove a badge (or set another)
  - {on: grows, actor: tumor, sprite: tumor_no_mhc}            # swap the sprite
  - {on: gone, actor: tumor, show: false}                      # hide (show: true to bring back)
  - {t: 0, actor: t, fx: zzz, dur: 1.0}                        # an effect for a limited time
camera:
  - {on: binds, zoom: 2, at: t}                                # cut to x2 (x3); an actor: the camera follows it
  - {on: stops, pan_to: [0.7, 0.5], dur: 0.6}                  # pan the center
  - {on: attacks, shake: 0.4, amp: 3}                          # shake (frame px)
  - {on: done, zoom: 1}                                        # cut back to the full frame
swarm:                                                         # N sprites that move by a rule
  - {sprite: antibody, n: 8, scale: 2, area: [0.05, 0.1, 0.4, 0.4], rule: seek, target: tumor,
     on: antibody, dur: 1.4, stagger: 0.12, radius: 0.1, arrive_anim: idle}
  # rule: wander | seek (to target, then stay) | orbit (around target) | flow (dir, speed) | flee
grow:                                                          # cells that divide: N doubles every "doubling" s
  - {sprites: [clone_a, clone_b, clone_c], at: [0.5, 0.5], n0: 1, max: 32, doubling: 0.6, on: divides, spread: 0.05}
field:                                                         # drawn behind the actors
  - {kind: dots, spacing: 12, color: LAV, size: 2, drag: q, radius: 0.24, pull: 0.4, grip_color: PLUM, wave: true}
  - {kind: dots, appear: true, t: 0.2, dur: 2.0}               # the lattice fades in
  - {kind: flow, n: 30, dir: [1, 0], speed: 0.2, color: LGREY}  # or sprite: glucose
  - {kind: gradient, at: tumor, radius: 0.4, color: PINK, on: signal, dur: 1.5}
```

Actor fields: `sprite`, `at`, `anim`, `hold`, `scale`, `flip`, `badge` (a sprite drawn on the top of the body),
`label`, `color`, `hidden`. A swarm `n`, a grow `max`, a flow `n` are schematic counts: check warns, and the
person hears about them before the render.

### contact
Two bodies face to face, their parts on stalks out of each surface, drawn from the model. Use it for every
step where two things touch: a receptor and its ligand, a drug on its target, two particles that collide.
```yaml
- id: S04
  type: contact
  left: t                       # things of the model, each with a sprite
  right: tumor
  show: [brake, signal]         # bind links as rows, top to bottom (default: every bind between the two)
  beats:
    - {on: binds, do: brake}    # do / undo a link of the model
    - {on: sticks, do: block}   # an occupy link: the agent flies in and takes the part's place
    - {on: dies, do: kill}      # a kill link: the right body dies (apoptosis) and stays dead
    - {on: stops, cell: left, anim: blocked}   # cell: left | right, with anim or fx
  camera:
    - {on: binds, zoom: 2, at: gap}            # at: left, right, gap, or [x, y]
```
The scene starts in the state the last scene left: a bound link stays bound, a docked agent stays docked,
a dead body stays dead. Labels show in the wide shot only.

## The mechanism model

The plan names what takes part in the story and how. There is no table of all molecules: write only the
links of this story (usually 3 to 6), each from a source.

- `things`: bodies with a `sprite`, a `label`, and `parts` (each with `label` and a palette `color` from
  the pack's `bible.md`); or a free agent (a drug, a photon) with `label` and `color` and no parts.
- `links`: `kind` is a verb that fits any science:
  - `bind`: two parts on two bodies touch and hold (`a` gets a socket, `b` the matching key).
  - `occupy`: free agent `a` sits on part `b`; `b` lets go of its other binds.
  - `kill`: thing `a` ends thing `b`.
  Each link has `source:` (its number in `sources`).

`pixsci check` holds every plan to the same rules: a bind only between parts of the two bodies on screen
(contact); a part on its own body (ownership); an agent only on its named part (specificity); the state
carries from scene to scene (persistence); `undo` only after `do` (causality); every link cites a source
and is shown in some scene. Shapes come from the links: partners fit, other parts do not.

### fact
`sprite`, `anim`, `text` (1 to 3 short lines). One idea, typed letter by letter.

### flow
`steps`: up to 4 of `{sprite, label, anim, scale}` with arrows. A process: step 1 leads to step 2.

### summary
`title`, `items` (up to 4 sprites with labels), `text` (1 or 2 lines). The last frame; it holds still.

### custom
`module` (path to a .py file), `function` (default `draw`). The function gets
`(img, t, scene, ctx)`; `ctx["layout"]` has the frame size, stage, and caption place. Read
`frame.W` and `frame.H`, never 480 and 270. A custom scene is a candidate for a new scene type.
