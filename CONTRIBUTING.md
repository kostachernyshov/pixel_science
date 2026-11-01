# Contributing

Thank you for helping. The library stays useful only if every piece has one style and a clear license.

## Add a sprite

1. **License.** Your own drawing, or a file under CC0-1.0 or CC-BY-4.0. No NC, no ND, no BY-SA, no "free for personal use".
2. **Style.** Colors only from the PICO-8 palette (`pixel_kit/palette.py`), no half-transparent pixels, a 1 px black outline, body about 24 to 40 px for a cell, 12 to 20 px for a molecule.
3. **Sheet.** One PNG: one row for each animation, one column for each frame, all cells one size, transparent background. Each sprite needs `idle`; cells also want `move`, `hit`, `death` (apoptosis: shrink and break up).
4. **Metadata.** Add an entry to `sprites/sprites.json`:
   ```json
   "virus": {"file": "virus.png", "group": "villain", "cell": [32, 32], "anchor": [16, 16],
             "anims": {"idle": {"row": 0, "frames": 2, "fps": 3, "loop": true},
                       "death": {"row": 1, "frames": 4, "fps": 6, "loop": false}}}
   ```
   Groups: `hero` (immune cells), `villain` (tumor cells, pathogens), `civilian` (body cells), `people`, `prop`, `badge` (molecules shown above a cell).
5. **Credits.** Add a row to `sprites/CREDITS.csv`: sprite, file, author, license, source URL, notes.
6. **Check.** `python tools/validate_sprites.py` prints `VALID`. Look at the cast sheet: `python pixsci.py sheet out/sheet.png`.

Sprites drawn in code live in `pixel_kit/library.py` and build with `python tools/build_sprites.py <name>`. Sprites added as PNG stay when the code sprites are built again.

## Add a scene type or a background

Scene painters are the `p_<type>` functions in `pixel_kit/explain.py`; backgrounds are in `pixel_kit/bg.py`. Read `frame.W` and `frame.H` at draw time, never fixed sizes. Check the result in all four formats with `pixsci.py board`. Document the new fields in `.agents/skills/explain/PLAN.md`.

## Add an example video

A folder in `examples/` with `explainer.yaml`, `voiceover.md`, and real sources. CI checks the plan and draws its storyboards.

## Pull requests

One topic in one pull request. CI must pass: sprite check, plan check, storyboards. Put a storyboard image in the description.
