# Contributing

Thank you for helping. The library stays useful only if every piece has one style and a clear license.

## Packs

Sprites live in packs: `packs/<name>/` with `pack.yaml` (name, version, description, license, author; optional
`borders:`, the look of the line of a border set, see PLAN.md),
`sprites/` (PNG sheets, `sprites.json`), and `code/` (a package whose `library.py` has
`build()` for sprites drawn in code). A plan picks its packs with `packs: [biology]`. Packs in other
folders load from `$PIXSCI_PACKS`. A sprite name is unique across packs.

## Add a sprite

1. **License.** Your own drawing (an image generator is welcome, `docs/adr/0002-generated-sprites.md`), or a file under CC0-1.0 or CC-BY-4.0. No NC, no ND, no BY-SA, no "free for personal use".
2. **Style.** New PNG art uses the shared AAP-64 palette by Adigun A. Polack (`pixel_kit/palette.py`), declared as `"palette": "AAP-64"` in its existing sprite entry. Existing PICO-8 sprites keep their colors and indices; an omitted palette means PICO-8. Use binary transparency and a crisp dark outline. For detailed receptor/protein art, start with a 128 px canvas and a few meaningful forms; simpler props stay smaller. Rectangular cells are allowed. The old 24–40 px cell / 12–20 px molecule bodies are legacy scale guidance, not a source-size limit.
3. **Sheet.** One PNG: one row for each animation, one column for each frame, all cells one size, transparent background. Each sprite needs `idle`; cells also want `move`, `hit`, `death` (apoptosis: shrink and break up).
4. **Metadata.** Add an entry to the pack's `sprites/sprites.json`:
   ```json
   "virus": {"file": "virus.png", "group": "villain", "cell": [32, 32], "anchor": [16, 16],
             "anims": {"idle": {"row": 0, "frames": 2, "fps": 3, "loop": true},
                       "death": {"row": 1, "frames": 4, "fps": 6, "loop": false}}}
   ```
   Groups: `hero` (immune cells), `villain` (tumor cells, pathogens), `civilian` (body cells), `people`, `prop`, `badge` (molecules shown above a cell).
   A free molecule that binds by its own surface (a ligand, an antibody) adds `"body": "molecule"`: the tool then draws
   no stalk and no head on its parts, so draw the contact site (a notch or a bump) as one piece with the body, on the
   side that faces the partner and on the straight line through the anchor (with several parts, on that part's row):
   the tool finds the site there, along a level or upright line. A free molecule faces right (in a scene, the one on the right of its partner gets
   `flip: true`); a membrane receptor faces up, out of the cell. Cells need no key: the tool draws their parts on
   stalks out of the membrane.
   For a higher-resolution sheet that keeps its size in scenes, set `source_cell` to the PNG cell dimensions. The original `cell` and `anchor` still define the size and alignment in scenes. For different aspect ratios, center the drawing in the part of the source cell that fits the display cell. Extra padding is cropped.
5. **Credits.** The pack's `license` and `author` in `pack.yaml` cover its sprites. A sprite by an outside author adds
   `"author"`, `"license"` (CC0-1.0 or CC-BY-4.0), and `"url"` (where it comes from) to its entry in `sprites.json`.
6. **Check.** `python tools/validate_sprites.py` prints `VALID`. Look at the cast sheet: `python pixsci.py sheet /tmp/sheet.png`.

Sprites drawn in code live in the pack's `code/library.py` and build with `python tools/build_sprites.py <pack> <name>`. Sprites added as PNG stay when the code sprites are built again.

## Add a verb or a primitive

Actions in scenes are verbs: YAML in `packs/<pack>/verbs.yaml` that lists primitives of `pixel_kit/fx.py`.
Follow `skills/add-verb/SKILL.md`. A verb fits its pack's subject (no ice or fire in biology).
Look at it on the contact sheet: `python pixsci.py verbs /tmp/verbs.png`.

## Add a scene type or a background

Scene painters are the `p_<type>` functions in `pixel_kit/explain.py`; backgrounds are in `pixel_kit/bg.py`. Read `frame.W` and `frame.H` at draw time, never fixed sizes. Check the result in all four formats with `pixsci.py board`. Document the new fields in `skills/animate/PLAN.md`.

## Work on the core

- **Frames.** A refactor of the core keeps the frames of the smoke plan as they were. Hash them before the change
  and after, and compare:
  ```
  python tools/frame_hashes.py skills/setup/smoke/explainer.yaml /tmp/before.json
  python tools/frame_hashes.py skills/setup/smoke/explainer.yaml /tmp/after.json /tmp/before.json
  ```
  It prints `EQUAL`. A change that alters frames on purpose names the scenes that differ in its pull request.
- **Named data.** Data that crosses modules travels in named fields (a dataclass or a NamedTuple), not by index:
  no `state[name][8]`.
- **Public names.** A module calls only public names of another module, never `<module>._name`; CI fails on it.
  `ruff check --select F --ignore F403,F405 pixel_kit pixsci.py tools` passes (CI runs it; locally
  `.venv/bin/pip install ruff` once, then `.venv/bin/ruff check ...`).

## Pull requests

One topic in one pull request. CI must pass: the sprite check, the setup check plan, the linter, and the
public-names check. Put a storyboard image in the description.
