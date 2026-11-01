---
name: add-sprite
description: Add a new character, molecule, or prop to a pack of pixel_science: draw it in code, check it, and show the person the cast sheet. Use when a video needs a sprite that `pixsci find` does not have, or when the person asks for a new sprite.
---

# Add a sprite

A sprite is drawn in code in the pack's `code/` folder, from palette indices, so that every style can draw
it again (outline, shading, colors). An artist may instead contribute a PNG (see `CONTRIBUTING.md`).
Images made by an image-generation model are never sprites.

Run commands from the repo root with `.venv/bin/python`.

## Steps

1. **Need.** Name the sprite (`snake_case`), the pack, its group, and the animations the video needs.
   Run `pixsci find <word> --json` first: reuse or extend an existing sprite when one is close.
   Read the pack's `bible.md`: the role decides the colors (in biology: an immune cell has a white body and
   the rim color of its type; red belongs to tumor cells).
2. **Draw.** Add a generator function to the pack's code (`packs/<pack>/code/`) and register it in
   `library.py` `build()`. Use `pixel_kit.pixdraw` (`Spr`, masks, `paint_body`, `outline`) and only the
   16 main palette colors. Sizes: a cell body 24 to 40 px, a molecule 12 to 20 px, a particle 10 to 26 px.
   Every sprite has `idle` (two frames, a 1 px bob); characters also get `blink`, `hit`, and the actions
   the video needs (cells: `move`, `death` as apoptosis).
3. **Build.** `python tools/build_sprites.py <pack> <name>`. Add `tags` (5 to 8 words a person would search)
   and a one-line `description` to the entry in `packs/<pack>/sprites/sprites.json`, add a row to
   `packs/<pack>/sprites/CREDITS.csv` (author, `CC0-1.0`), and build again.
4. **Check.** `python tools/validate_sprites.py <pack>` prints `VALID`; `pixsci catalog` updates the catalog;
   `pixsci find <tag> --json` finds the sprite.
5. **Look.** Draw the sheet in all three styles: `pixsci sheet out/sheet-<style>.png --pack <pack> --style <style>`
   for `paper`, `arcade`, `gameboy`. Look at each: the role reads in greyscale (gameboy), the face is clear at x2,
   the sprite is distinct from its neighbours. Fix and build again.
6. **Show.** Show the person the three sheets and ask: "Accept the sprite? yes / changes". Done when the person says yes.
