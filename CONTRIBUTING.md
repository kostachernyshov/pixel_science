# Contributing

Thank you for helping. The library stays useful only if every piece has a clear role, a clear license,
and works in every style.

## Packs

Everything the core draws lives in a pack: a folder in `packs/` with `pack.yaml`.

```
packs/<name>/
  pack.yaml          name, kind (content | style), version, description, license
  bible.md           roles and colors of the characters (content packs)
  sprites/           PNG sheets, sprites.json, CREDITS.csv
  code/              __init__.py and library.py with build() -> sprites drawn in code
  backgrounds.py     BACKGROUNDS = {name: fn(t)}, ANIMATED = {...}, TAGS = {name: [...]}
```

A style pack has a `style:` block in `pack.yaml` (see `pixel_kit/style.py`) and may hold PNGs in `sprites/`
that redraw content sprites for that style (same name, same animations). A plan stacks content packs with
`packs: [...]`; a higher pack overrides a lower one, and a sprite that replaces one of a lower pack says
`"overrides": true` in its `sprites.json` entry. Packs in other folders load from `$PIXSCI_PACKS`.

## Add a sprite

The agent skill `add-sprite` walks through this. By hand:

1. **License.** Your own drawing, or a file under CC0-1.0 or CC-BY-4.0. No NC, no ND, no BY-SA, no "free for personal use". No images made by an image-generation model.
2. **Style.** Colors only from the 16 main PICO-8 colors (`pixel_kit/palette.py`), no half-transparent pixels, a 1 px black outline, a body about 24 to 40 px for a cell, 12 to 20 px for a molecule. Follow the pack's `bible.md`.
3. **Sheet.** One PNG: one row for each animation, one column for each frame, all cells one size, transparent background, 2 px of room around the body. Each sprite needs `idle`; characters also want `blink` and `hit`; cells want `move` and `death` (apoptosis: shrink and break up).
4. **Code or PNG.** A sprite drawn in code goes into the pack's `code/library.py` and builds with `python tools/build_sprites.py <pack> <name>`; every style can then draw it again with its own parameters. A PNG sprite gets an entry in `sprites.json`:
   ```json
   "virus": {"file": "virus.png", "group": "villain", "cell": [32, 32], "anchor": [16, 16],
             "tags": ["virus", "pathogen", "infection"], "description": "A virus particle",
             "anims": {"idle": {"row": 0, "frames": 2, "fps": 3, "loop": true},
                       "death": {"row": 1, "frames": 4, "fps": 6, "loop": false}}}
   ```
   Groups: `hero`, `villain`, `civilian`, `people`, `prop`, `badge` (biology); `particle`, `machine`, `field` (physics); `body`.
5. **Credits.** Add a row to the pack's `sprites/CREDITS.csv`: sprite, file, author, license, source, notes.
6. **Check.** `python tools/validate_sprites.py` prints `VALID`; `python pixsci.py catalog` updates the catalog.
   Look at the sheet in all three styles: `python pixsci.py sheet out/sheet.png --pack <pack> --style arcade`.

## Add a style

A style pack sets roles (background, ink, accent, caption plate), UI colors, sprite parameters (shading,
outline, glow), a background filter, a frame filter, and scanlines. Copy `packs/style-arcade/pack.yaml`.
Check it with the storyboards of every example: `python pixsci.py board examples/<x>/explainer.yaml out --html`.

## Add a scene type, a generator, or a background

Scene painters are the `p_<type>` functions in `pixel_kit/explain.py`; generators are in `pixel_kit/gen.py`;
backgrounds are in a pack's `backgrounds.py`. Read `frame.W` and `frame.H` at draw time, never fixed sizes;
use roles (`INK`, `ACCENT`, `PLATE`) for text so that every style can set them. Backgrounds draw in base
colors; the style filters them. Check the result in all formats and styles with `pixsci board --html`.
Document new fields in `.agents/skills/animate/PLAN.md`.

## Add an example video

A folder in `examples/` with `explainer.yaml`, `voiceover.md`, and real sources. `pixsci check` passes
(pace and motion included). CI checks the plan and draws its storyboards.

## Pull requests

One topic in one pull request. CI must pass: sprites, catalog, plans, storyboards. Put a storyboard image in the description.
