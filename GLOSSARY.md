# Glossary

Terms of pixel_science. Use these words in code, docs, issues, and plans.

| Term | Meaning | Not |
|---|---|---|
| **Core** | `pixel_kit/`: rendering code with no topic. It knows no cell and no atom. | engine, framework |
| **Pack** | A folder in `packs/` that gives a topic its sprites, verbs, and color roles (`packs/biology/`). | plugin, module |
| **Plan** | `explainer.yaml`: the scenes of one video. | script, config |
| **Scene** | One part of a plan with one type (`title`, `action`, ...) and one voice-over block. | shot |
| **Actor** | A sprite on the stage of an `action` scene, with a name in the plan. | character, object |
| **Beat** | One timed line of an `action` scene: an actor moves, changes animation, or does a verb. | event, keyframe |
| **Verb** | An action that a beat names (`secrete`, `block`, `hit`). Data in a pack's `verbs.yaml`: primitives, color roles, hit, show or hide. | effect, fx |
| **Primitive** | A function of motion in `pixel_kit/fx.py` with no topic (`jet`, `burst`, `ring`, `shell`, `sparks`, `dissolve`, `trail`, `glow`, `sign`). Only verbs use primitives. | effect, particle |
| **Color role** | A name for a color ramp in a verb (`granule`, `pdl1`), dark to bright, from palette names. | color, hex |
| **Light layer** | A second layer of the frame with glow; the style blends it over the colors (`fx.LIGHT`). | bloom, shader |
| **Hit** | Mechanics of a blow: windup of the attacker, freeze of the picture on contact, shake, push of the target. Presets `soft`, `normal`, `heavy`. | impact |
| **Contact sheet** | A grid of frames of each verb over time: `pixsci.py verbs out/verbs.png`. Used to look at a verb. | preview |
| **Model** | `model:` in a plan: the things of one story, their parts, and its relations, each with a source. Written in `storyboard`, checked by `pixsci check` (`pixel_kit/model.py`). | mechanism table |
| **Part** | A thing's piece that acts at its surface (a receptor, a ligand). Drawn on a stalk out of its owner's membrane, with a lock or key head. | badge, icon |
| **Relation** | One link of the model: `bind`, `occupy`, `transfer`, `change`, `destroy`. A verb names the kinds it shows (`relation:`); a beat with it must match a relation. | link, edge |
