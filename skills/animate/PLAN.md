# explainer.yaml format

Paths are relative to the plan file.

```yaml
title: "How NK cells find cancer"     # used by the summary heading
name: nk-missing-self                 # output file names: <name>-<format>.mp4
lang: en                              # en: on-screen text must be plain ASCII
packs: [biology]                      # sprite packs in packs/ (default: all)
voiceover: voiceover.md               # '## S01' headings, the voice-over text under each
tts: {voice: ryan, instruct: "Warm, natural documentary narrator."}   # optional: the voice of `--voice` (docs/tool.md, Voice)
subtitles: true                       # optional: the voice-over word for word in a box at the bottom (replaces captions)
formats: [landscape, vertical, square, banner]
max_s: 60                             # optional: longest story before the summary (default 60 s)
sources:                              # required: the papers or textbooks behind each claim
  - "Author A. Title. Journal Year;Vol:Pages. doi:..."
model: {things: ..., relations: ...}  # a mechanism: see "Model and parts" below
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
sits above the bottom 20 % (apps cover it with buttons). In `banner`, there is no heading and actor labels.

## Timing

- A scene lasts (words of its voice-over) / 2.5 + 0.8 s, at least 2.5 s. `dur: 4` sets it by hand.
- With `--voice`, a scene lasts as long as its spoken audio (0.25 s before the words, 0.6 s after); `dur` can make it longer, not shorter.
- Story before the summary: 20 to 45 s. The summary holds 8 s (`dur` sets more).
- A beat can start on a word of its scene instead of a time: `{word: "attacks", dt: -0.3, actor: t, verb: hit}`
  (`n: 2`: the second time the word is said). The same word wins: "B" finds "B", not "because". Only when
  the scene does not say the word itself, its start is enough: "attack" finds "attacks".
  With `--voice`, the time is when the word is heard (`OUTDIR/voice/<scene>.words.json`); without it, estimated.
  A `custom` scene asks for the same time with `words.cue(ctx["plan"], scene, "attacks")`.
- In `voiceover.md`, `[PD-L1|pee dee el one]` shows the first form (subtitles) and speaks the second (voice).
  Write numbers, units, and gene or protein names this way.

## Subtitles

`subtitles: true` shows the voice-over word for word in a box at the bottom of every scene: each word types in
while it is heard, the word being said is highlighted. A page holds 2 lines (1 in the banner) and ends at the end
of a sentence or a pause. Captions are not drawn. Colors: `subtitles: {fill, border, inner, text, highlight}`,
each a palette index or `[r, g, b]`; `fade_color: [r, g, b]` is the color of the dissolve between scenes
(default the paper background) for a plan with its own palette.

## Fields of all scenes

| Field | Meaning |
|---|---|
| `id` | Unique id, the same as the heading in `voiceover.md`. |
| `type` | `title`, `cast`, `action`, `fact`, `flow`, `summary`, `custom`. The last scene is a `summary` (or a `custom` final frame). |
| `caption` | 1 to 3 words at the bottom, on screen 2 s or more. |
| `title` | Short heading at the top left (not in `banner`). |
| `bg` | `paper` (default), `plain`, `tissue`, `epithelium`, `bloodstream`, `lymph_node`, `tme`, `dishes`. |
| `fade` | `false`: no dissolve into this scene (one continuous shot). |
| `key` | 0..1: where in the scene the storyboard takes its frame (default 0.75). |

Colors by name: `favorable` (blue), `unfavorable` (orange), `neutral` (grey), with `2` and `3` shades,
and `ink`, `navy`. Blue and orange, not green and red: people with red-green color blindness tell them apart.

## Scene types

### title
`title` (A-Z, 0-9, `- ! . ? :`, at most about 13 characters for the vertical frame), `sub`, `credit`.

### cast
`items`: up to 4 of `{sprite, label, color, anim, scale}`. The characters of the story.

### action
The main scene type: actors on a stage and timed beats.

```yaml
actors:
  nk:   {sprite: nk, at: [0.15, 0.5], anim: move}              # at: fractions of the stage (x, y)
  cell: {sprite: epithelial, at: [0.72, 0.5], badge: badge_mhc_self, label: Healthy}
beats:                                                          # t: seconds from the scene start
  - {t: 0.3, actor: nk, move_to: [0.45, 0.5], dur: 1.6}         # move with easing
  - {t: 0.3, actor: nk, move_to: cell, dur: 1.6}                # or move until it touches an actor
  - {t: 1.9, actor: nk, anim: alert}                            # change animation
  - {t: 2.2, actor: nk, verb: alert}                            # a verb: an action with effects
  - {t: 2.6, actor: nk, verb: hit, target: cell}                # a verb with a target; hit: soft|normal|heavy|false
  - {t: 4.0, actor: nk, anim: move, flip: true}                 # face the other way
  - {t: 4.0, actor: cell, badge: null}                          # remove a badge (or set another)
  - {t: 5.0, actor: cell, show: false}                          # hide (show: true to bring back)
```

Actor fields: `sprite`, `at`, `anim`, `scale` (default 2), `flip`, `badge` (a sprite of group `badge`
drawn above), `label`, `color`, `hidden`. Keep x between 0.1 and 0.9: the vertical frame is narrow.

`move_to: <actor>` moves until the two sprites touch, edge to edge, on the side the mover comes from; the
tool knows both sizes, so this fits every format. When parts of the two actors bind (Model and parts), it
stops at the gap of the bind instead: room for both heads and labels, within reach of the stalks.
Use it whenever an actor must reach another one (a syringe, a hit, a bind): numbers only guess.

**Verbs.** A beat with `verb:` plays an action: effects with color and light, and for some verbs a hit
(the attacker pulls back, the picture stops on contact, the frame shakes, the target is pushed back).
`pixsci.py verbs` lists the verbs of the core and the packs; `pixsci.py verbs out/verbs.png` draws them.
Core verbs: `appear` (set `hidden: true` on the actor), `vanish`, `hit`, `highlight`, `alert`.
Biology verbs: `secrete`, `block`, `apoptosis`, `bind`. Effects have no coordinates: they take place and size
from the actor and the `target`. `hit: heavy` on a beat makes a hit stronger, `hit: false` removes it.
A verb is missing? Add it to the pack, then go on with the scene: [add-verb](../add-verb/SKILL.md).

**Model and parts.** A mechanism has `model:` at the top of the plan (from `storyboard.md`; format in
`pixel_kit/model.py`). Actors are things of the model by name (or `thing: t`, for a second T cell).
`parts: [tcr, pd1]` on an actor (or on a beat, to change them) shows parts on stalks out of its membrane,
facing the partner; partners get a matching lock and key. A verb with `relation:` (`bind`, `secrete`,
`apoptosis`) must match a relation: `{actor: pdl1, verb: bind, target: pd1}` closes a bind and it stays
closed in later scenes; `{actor: drug, verb: bind, target: pdl1}` puts the drug on PD-L1, which lets go of
PD-1. `pixsci check` fails on a relation not in the model, a part not shown, parts too far apart or with
no room for labels (it names the place that fixes it), labels that cover each other, a head or an actor
label, a destroyed actor that comes back, `after:` out of order, or a source with no quote. A verb with a hit
(`hit`, `secrete`, `block`) fails the check when the two actors do not touch at the moment of contact.
Bound parts on a level line put their labels on their stalks; on an upright line (one cell above the other),
beside the stalks, one left and one right.

### fact
`sprite`, `anim`, `text` (1 to 3 short lines). One idea, typed letter by letter.

### flow
`steps`: up to 4 of `{sprite, label, anim, scale}` with arrows. A process: step 1 leads to step 2.

### summary
`title`, `items` (up to 4 sprites with labels, or none for a text-only frame), `text` (1 or 2 lines). The last frame; it holds still.

### custom
`module` (path to a .py file), `function` (default `draw`), `title` (drawn by the tool, as in other scenes;
the function does not draw it). The function gets
`(img, t, scene, ctx)`; `ctx["layout"]` has the frame size, stage, and caption place. Read
`frame.W` and `frame.H`, never 480 and 270. With subtitles, the stage ends above their box. `ctx["dur"]` is
the scene length; time events with `words.cue` (see Timing). Colors are palette indices or `(r, g, b)`.
A custom scene is a candidate for a new scene type.
