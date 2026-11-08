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
timeline: {from: 1982, to: 2014, unit: year}   # optional: a strip of time under the stage (see "Timeline")
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
- With a voice in OUTDIR (`pixsci voice` or `--voice`), a scene lasts as long as its spoken audio (0.25 s before the words, 0.6 s after); `dur` can make it longer, not shorter.
- Story before the summary: 20 to 45 s. The summary holds 8 s (`dur` sets more).
- A beat can start on a word of its scene instead of a time: `{word: "attacks", dt: -0.3, actor: t, verb: hit}`
  (`n: 2`: the second time the word is said). The same word wins: "B" finds "B", not "because". Only when
  the scene does not say the word itself, its start is enough: "attack" finds "attacks".
  With a voice in OUTDIR, the time is when the word is heard (`OUTDIR/voice/<scene>.words.json`); without it, estimated.
  A `custom` scene asks for the same time with `words.cue(ctx["plan"], scene, "attacks")`.
- In `voiceover.md`, `[PD-L1|pee dee el one]` shows the first form (subtitles) and speaks the second (voice).
  Write numbers, units, and gene or protein names this way.

## Timeline

`timeline:` at the top of the plan puts a strip at the bottom of the stage: a scale of time, a "now" cursor,
and marks. It is a layer over any set: it stays through the scenes and does not dissolve. Title and summary
scenes, and a scene with `timeline: false`, hide it; the strip keeps its place in every scene, so the stage does not jump. Beats (with `word:` or `t:`,
no actor) move the cursor and add marks:

```yaml
timeline: {from: 1980, to: 2000, unit: year, now: 1998}    # unit in the singular: year, day, million year
                                                            # now: where the cursor starts (default: from)
beats:
  - {word: "back", timeline: 1982}                          # the cursor goes there
  - {word: "donor", mark: 1982, label: DONOR, color: unfavorable}   # a mark stays; color: a color name
```

A jump of more than a quarter of the scale, back or forward, shows `<<` or `>>` while the cursor moves and
leaves its span on the line with a label ("16 YEARS") until the cursor moves again. Mark labels stand side by
side above the line; check fails when they do not fit, so keep them short and the marks apart. The cursor
value has as many decimals as `from:` and `to:`. In the banner the strip has no labels: the line, the marks,
and the cursor with its value at the right end. Values are in the scale; a year or a date on screen is in a
source.

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
| `type` | `title`, `cast`, `action`, `fact`, `flow`, `summary`, `custom`. The last scene is a `summary` (or a `custom` final frame, with `why:`). |
| `caption` | 1 to 3 words at the bottom, on screen 2 s or more. |
| `title` | Short heading at the top left (not in `banner`). |
| `bg` | `paper` (default), `plain`, `tissue`, `epithelium`, `bloodstream`, `lymph_node`, `tme`, `dishes`. |
| `fade` | `false`: no dissolve into this scene (one continuous shot). |
| `continue` | `true`: an action scene goes on from the action scene before (Set, under action). |
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
  - {word: "died", actor: cell, ghost: true}                    # fades to its ghost in 1 s and stays
  - {word: "plaster", actor: cell, marks: [{at: [0.5, 0.7], sprite: plaster}]}   # the marks from this word
  - {word: "patrol", actor: nk, wander: true}                   # walks in its zone until its next beat
  - {word: "hunt", actor: nk, hunt: [c1, c2], verb: hit, then: apoptosis}   # to each target in turn
  - {word: "divide", actor: c3, divide: c4}                     # c4: a hidden actor, the daughter
```

Actor fields: `sprite`, `at`, `anim`, `scale` (default 2), `flip`, `badge` (a sprite of group `badge`
drawn above), `label`, `color`, `hidden`, `in` (a zone of the set), `ghost` (true: it starts as a ghost),
`marks`, `still`. Keep x between 0.1 and 0.9: the vertical frame is narrow.

- **Ghost.** Any sprite has a ghost: a pale see-through silhouette with an outline, made by the tool. A beat
  `ghost: true` fades the actor to its ghost in 1 s (a hidden actor appears as one); `ghost: false` brings it
  back. Only the sprite becomes a ghost: its marks and badge stay, its parts are not drawn. A destroyed actor
  cannot come back (`ghost: false` or `show: true` fails the check), but its ghost can stay or appear: a
  character who died stays in the set. Put `ghost: true` on the word of the verb that destroys it
  (`apoptosis`): the actor then stays as a ghost; the verb does not hide it.
- **Behaviors** make plain beats, so `check` sees what plays (who is hit, who is destroyed). They work in a
  `continue: true` scene too. A problem in a beat they make names the behavior ("made by the hunt at 0.75 s").
  - `wander: true`: the actor walks from point to point in its zone and faces where it goes, until its next
    beat, a beat of a behavior on it (a hunter comes), or the end of the scene (`dur:`: one walk, default 1.5 s).
  - `hunt: [t1, t2]` with `verb:`: the actor goes to each target in turn (each once, in its zone; `dur:` each,
    default 1.2 s) and does the verb to it. `then:` is the verb each target does after it (`apoptosis`,
    `vanish`); with a model, a destroying verb needs its `destroy` relation, and the target cannot come back.
    `ghost: true` keeps each target as its ghost. Check fails when the hunt ends after the scene, or when the
    hunter has another beat while the hunt runs.
  - `divide: c4`: the cell plays its `divide` animation (if its sprite has one); then the daughter `c4`
    (declared with `hidden: true` in the same zone; no `at:` needed) appears at its place with its marks and
    badge, and the two move apart, edge to edge: the cell steps aside and the daughter moves to it
    (`apart:`: a fraction of the zone between them instead). Right after a `move_to: <actor>` of the cell,
    give `apart:` or a place first: check says so.
- **At rest** an actor moves a little (one sprite pixel): not while it moves or does a verb, or a verb is done
  to it. `still: true` on the actor stops it (a prop, an organ, a slide).
- **Marks** on the body: a spot, a plaster, an organ. Each mark has `at:` (fractions of the sprite, 0 to 1,
  mirrored with `flip`) and a `sprite:` (it takes the actor's scale; `anim:` starts when the mark appears, for
  example `kidney` with `anim: glow`) or a `color:` (a dot; `size:` in sprite pixels, default 2). A beat with
  `marks:` gives the list from its word on: list all marks that stay. Not `mark:`, a point on the timeline.

**Set.** `set:` builds the set of the storyboard once; the next scenes go on in it with `continue: true`.
An actor with `in: <zone>` stands in that zone: its `at:` and `move_to: [x, y]` are fractions of the zone,
and its sprite and label stay inside it. The actors in zones share one scale: the largest at which each
fits its zone (smaller in the banner or in small panels), so that sizes still compare.

```yaml
set: {type: panels, panels: [{title: CONTROL, counter: "0 OF 15"}, {title: MHC LOW, counter: "0 OF 15"}]}
actors:
  nk:   {sprite: nk, in: all, at: [0.2, 0.5]}       # in every panel; no parts; a target of its verbs is in: all too
  cell: {sprite: tumor, in: B, at: [0.7, 0.5]}      # zones A, B, C, D (or name: in a panel)
beats:
  - {word: "seven", panel: B, counter: "7 OF 15"}   # a counter changes on its word; the number is in a source
```

```yaml
set: {type: border, at: 0.45, top: OUTSIDE, bottom: INSIDE, line: membrane}   # zones top, bottom, border
actors:
  rec: {sprite: membrane_receptor, in: border, at: [0.6, 0]}    # stands on the line
```

- `panels`: 2 to 4 frames with a title and a counter each: side by side (also 2 or 3 in the square), stacked
  in the vertical frame, 2 x 2 for 4 in the square. The banner shows frames and counters, no titles.
  `check` fails when a title and its counter do not fit their panel in a format of the plan.
- `border`: a line across the stage at `at` (0.2 to 0.8 of its height) between two zones: the outside and the
  inside of a cell, air and water, above and below the ground. `line:` names a look from a pack (`pack.yaml`,
  `borders:`; biology has `membrane`).
- `continue: true` (an action scene after an action scene): no dissolve; the set, the background, the title,
  the counters, and the actors go on as they are at the end of the scene before (place, zone, flip, badge,
  parts, ghost, marks, shown or hidden; a destroyed actor stays hidden, or stays as its ghost).
  The scene's own `actors:` add actors or change fields of the ones that go on.

`move_to: <actor>` moves until the two sprites touch, edge to edge, on the side the mover comes from; the
tool knows both sizes, so this fits every format. When parts of the two actors bind (Model and parts), it
stops at the gap of the bind instead: room for both heads and labels, within reach of the stalks.
Use it whenever an actor must reach another one (a syringe, a hit, a bind): numbers only guess.

**Verbs.** A beat with `verb:` plays an action: effects with color and light, and for some verbs a hit
(the attacker pulls back, the picture stops on contact, the frame shakes, the target is pushed back).
`pixsci.py verbs` lists the verbs of the core and the packs; `pixsci.py verbs /tmp/verbs.png` draws them.
Core verbs: `appear` (set `hidden: true` on the actor), `vanish`, `hit`, `highlight`, `alert`.
Biology verbs: `secrete`, `block`, `apoptosis`, `bind`. Effects have no coordinates: they take place and size
from the actor and the `target`. `hit: heavy` on a beat makes a hit stronger, `hit: false` removes it.
A verb is missing? Add it to the pack, then go on with the scene: [add-verb](../add-verb/SKILL.md).

**Model and parts.** A mechanism has `model:` at the top of the plan (from `storyboard.md`; format in
`pixel_kit/model.py`). Actors are things of the model by name (or `thing: t`, for a second T cell).
`parts: [tcr, pd1]` on an actor (or on a beat, to change them) shows parts on stalks out of its membrane,
facing the partner; partners get a matching lock and key. A part on a sprite marked `"body": "molecule"` (a ligand, an
antibody) has no stalk and no head: its site is the sprite's own edge, and the partner's head reaches it.
Its site is drawn on the right (a membrane receptor's on top): when the molecule stands to the right of its partner, give it `flip: true`. A verb with `relation:` (`bind`, `secrete`,
`apoptosis`) must match a relation: `{actor: pdl1, verb: bind, target: pd1}` closes a bind and it stays
closed in later scenes; `{actor: drug, verb: bind, target: pdl1}` puts the drug on PD-L1, which lets go of
PD-1. `pixsci check` fails on a relation not in the model, a part not shown, parts too far apart or with
no room for labels (it names the place that fixes it), labels that cover each other, a head or an actor
label, a destroyed actor that comes back (its ghost may stay), `after:` out of order, or a source with no quote. A verb with a hit
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
`module` (path to a .py file), `function` (default `draw`), `why`, `title` (drawn by the tool, as in other
scenes; the function does not draw it). `why` is one line: no other scene type shows this set, or the frame is
key (hook, turn, end) and a scene type shows it worse. `check` fails without it. The function gets
`(img, t, scene, ctx)`; `ctx["layout"]` has the frame size, stage, and caption place. Read
`frame.W` and `frame.H`, never 480 and 270. With subtitles or a timeline, the stage ends above their box or strip. `ctx["dur"]` is
the scene length; time events with `words.cue` (see Timing). Colors are palette indices or `(r, g, b)`.
A custom scene that draws a relation of the model says so with a beat: `{word: rain, shows: rain_falls}`.
The code reads its time from `ctx["shows"]["rain_falls"]` (seconds in the scene, the first time if it is
shown twice) and draws it then; `check`
counts the relation as shown and checks its source and `after:` order, and says that the drawing is not
checked. `shows:` is for custom scenes only; an action scene shows a relation with a verb.
A custom scene is a candidate for a new scene type.

Start from this frame: one set for the whole scene, the actors on it, the events on their words.

```python
from PIL import ImageDraw
from pixel_kit import sprites as S, ui, words
from pixel_kit.font import text
from pixel_kit.palette import INK

def draw(img, t, scene, ctx):
    plan, L = ctx["plan"], ctx["layout"]
    x0, y0, x1, y1 = L["stage"]          # under the title, above the caption or the subtitles
    W, cx, cy = x1 - x0, (x0 + x1) // 2, (y0 + y1) // 2
    d = ImageDraw.Draw(img)
    # 1. Set: the same in each frame, from the first second to the last (here: two panels)
    ui.box(d, x0 + 4, y0 + 4, cx - 2, y1 - 4)
    ui.box(d, cx + 2, y0 + 4, x1 - 4, y1 - 4)
    # 2. Sprites: on the set; a character that dies stays as a shadow
    k = L["sprite_scale"]
    S.idle(img, "nk", t, x0 + W // 4, cy, scale=k)
    # 3. What changes: each change on its word (words.cue), or at ctx["shows"][...] for a relation of the model
    if t >= words.cue(plan, scene, "attacks", default=ctx["dur"] / 2):
        S.idle(img, "tumor", t, x0 + 3 * W // 4, cy, scale=k)
        if not L["banner"]:                # the banner is too low for a label above the sprite
            text(img, x0 + 3 * W // 4, y0 + 8, "7 OF 15", INK, align="c")
```
