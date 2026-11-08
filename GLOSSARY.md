# Glossary

Terms of pixel_science. Use these words in code, docs, issues, and plans.

| Term | Meaning | Not |
|---|---|---|
| **Core** | `pixel_kit/`: rendering code with no topic. It knows no cell and no atom. | engine, framework |
| **Pack** | A folder in `packs/` that gives a topic its sprites, verbs, and color roles (`packs/biology/`). | plugin, module |
| **Plan** | `explainer.yaml`: the scenes of one video. | script, config |
| **Scene** | One part of a plan with one type (`title`, `action`, ...) and one voice-over block. | shot |
| **Set** | The composition that the viewer learns once and that stays to the end of a video (two panels, a cell in section, a timeline). The story happens inside it. Chosen in `storyboard` (`Set:`). | running device, background |
| **Timeline** | `timeline:` in a plan: a strip of time at the bottom of the stage with a "now" cursor and marks, over any set (`pixel_kit/timebar.py`). | timebar, scrubber |
| **Zone** | A part of a set where actors stand (`in: B`, `in: top`); their `at:` is a fraction of it. | region, area |
| **Candidate** | A custom scene or a new character that came out well, kept next to the video in `videos/<slug>/candidates/<name>/`. It goes into the library only when the person asks. | draft |
| **Actor** | A sprite on the stage of an `action` scene, with a name in the plan. | character, object |
| **Actor state** | Where an actor is and how it looks at time t: place, animation, flip, badge, shown, ghost, marks (`pixel_kit/stage.py`). | pose, sprite state |
| **Ghost** | An actor's look after `ghost: true`: a pale see-through silhouette of its sprite with an outline, made by the tool for any sprite. A destroyed actor may stay as a ghost. | shadow, memory |
| **Mark** | A sprite or a dot on an actor's body (`marks:`), at fractions of the sprite. Not the timeline's `mark:`, a point on the strip. | spot, sticker |
| **Behavior** | A beat that makes beats: `wander`, `hunt`, `divide`. It becomes plain beats (move, verb, show) once, when the plan is prepared, so check sees what plays. | AI, routine |
| **Beat** | One timed line of an `action` scene: an actor moves, changes animation, or does a verb. | event, keyframe |
| **Verb** | An action that a beat names (`secrete`, `block`, `hit`). Data in a pack's `verbs.yaml`: primitives, color roles, hit, show or hide. | effect, fx |
| **Primitive** | A function of motion in `pixel_kit/fx.py` with no topic (`jet`, `burst`, `ring`, `shell`, `sparks`, `dissolve`, `trail`, `glow`, `sign`). Only verbs use primitives. | effect, particle |
| **Color role** | A name for a color ramp in a verb (`granule`, `pdl1`), dark to bright, from palette names. | color, hex |
| **Light layer** | A second layer of the frame with glow; the style blends it over the colors (`fx.LIGHT`). | bloom, shader |
| **Hit** | Mechanics of a blow: windup of the attacker, freeze of the picture on contact, shake, push of the target. Presets `soft`, `normal`, `heavy`. | impact |
| **Contact sheet** | A grid of frames of each verb over time: `pixsci.py verbs /tmp/verbs.png`. Used to look at a verb. | preview |
| **Model** | `model:` in a plan: the things of one story, their parts, and its relations, each with a source. Written in `storyboard`, checked by `pixsci check` (`pixel_kit/model.py`). | mechanism table |
| **Part** | A thing's piece that acts at its surface (a receptor, a ligand). Drawn on a stalk out of its owner's membrane, with a lock or key head; on a molecule (`"body": "molecule"`), the site is the sprite's own edge. | badge, icon |
| **Relation** | One link of the model: `bind`, `occupy`, `transfer`, `change`, `destroy`. A verb names the kinds it shows (`relation:`); a beat with it must match a relation. | link, edge |
| **Voice** | The voice-over spoken by Qwen3-TTS: one wav per scene in `OUTDIR/voice/`, made by `pixsci voice` or `--voice`. | narration, audio |
| **Word times** | When each word of a scene is heard: `OUTDIR/voice/<scene>.words.json`, from forced alignment of the known text to the voice. | transcript, timestamps |
| **Word beat** | A beat with `word:` in place of `t:`: it starts when the word is heard. | cue point |
| **Subtitles** | The voice-over word for word in a box at the bottom (`subtitles: true`); each word types in while it is heard. | captions |
| **Spoken form** | In `voiceover.md`, `[written|spoken]`: the subtitles show the first, the voice says the second. | alias |
