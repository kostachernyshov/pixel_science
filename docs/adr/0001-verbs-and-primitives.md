# 1. Effects: verbs in packs, primitives in the core

Date: 2026-11-02. Status: accepted (grilling session with Kosta, after a review of pixelfx).

## Context

Videos repeat the same actions again and again: an immune cell attacks, a tumor cell hides, a cell dies.
The old `fx.py` had separate functions (`particles`, `hit_flash`, `wave`, `sparkle`) with flat colors,
called by name from the plan. We wanted effects that are livelier and nicer to look at, easy to reuse,
true to the topic (an ice blast is fine in a game, never in biology), and with little code.

[pixelfx](https://github.com/patch-gg/pixelfx) (MIT, 244 game effects in JavaScript, after Hugo Duprez's
Sprite Fusion VFX) showed the techniques: a frame from `t` and a seed only, a light layer over the colors,
a hit with windup, freeze, and recoil. Its effects are game effects, and its code is JavaScript.

## Decision

1. **Two levels.** Primitives (motion, no topic) live in the core, `pixel_kit/fx.py`. Verbs (meaning) live
   in packs, `packs/<pack>/verbs.yaml`. A verb lists primitives with color roles. Five core verbs with no
   topic (`appear`, `vanish`, `hit`, `highlight`, `alert`) serve all packs; a pack can replace them.
2. **We take the techniques, not the code.** No pixelfx effects are copied and pixelfx is not a dependency.
   Our primitives use its ideas (light layer, seeded frames, hit mechanics) in Python and numpy.
3. **A primitive is a pure function of time**: `fn(cv, t, g, ramp, o)`. No state between frames, no
   step-by-step physics; any frame renders alone.
4. **Hit mechanics are part of a beat**, in the core: presets `soft`, `normal`, `heavy`.
5. **The light layer strength comes from the style** (`fx.LIGHT`): "tint" on a light background, "add" on a dark one.
6. **A beat names only verbs.** `pixsci check` gives an error for an unknown verb and names the next step.
   The agent adds the verb to the pack and goes on; the person is not stopped.
7. **A verb is data** (YAML, no Python). Python is needed only for a new primitive.
8. **Place from actors** (`at`, `from`/`to`): a plan has no coordinates of effects.
9. **Colors by role**, defined in the pack, so a verb works in every style.
10. **Who decides**: the agent adds verbs; a new primitive needs the maintainer's "yes" after a contact sheet.
11. **First set**: 9 primitives (`jet`, `burst`, `ring`, `shell`, `sparks`, `dissolve`, `trail`, `glow`,
    `sign`). New ones only for a real scene. The old `fx.py` functions are removed.
12. **Verbs only in packs**, not in a plan, so the next video can use them. `pixsci verbs` lists them.
13. **Biology verbs**: `secrete` (granzymes), `block` (PD-L1 shield), `apoptosis` (quiet death, not an
    explosion), `bind` (antibody).
14. **Speed**: a verb draws a 480x270 frame in 5 ms or less; `pixsci check` warns when it is slower.

## Consequences

- A new action is usually 5 to 10 lines of YAML. The rules are in `.agents/skills/add-verb/SKILL.md`.
- `fx:` in a beat is replaced by `verb:`; `pixsci check` says so for an old plan.
- Effects blend with sprites through the light layer; a style with a dark background sets `LIGHT["mode"] = "add"`.
