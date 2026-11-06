---
name: add-sprite
description: Add, import, or redraw a reusable pixel_science sprite when the library lacks a suitable object or a meaningful visual state.
---

# Add a sprite

Create beautiful, scientifically clear sprites for still illustrations and videos. Follow "less, but better": reuse what exists, then add what is needed.

## Preparation

Find the project root: `${CLAUDE_PLUGIN_ROOT}` for an installed plugin, or the root of the working clone. Save shared library changes in a working clone, not in the plugin cache that updates replace.

Read `CONTRIBUTING.md` and the sections of `docs/tool.md` about sprites and scale. Inspect the PNGs, `sprites.json`, `CREDITS.csv`, and art guidance in the chosen pack.

## 1. Check whether a new drawing is needed

Review the existing sprites. Identify:
- what the viewer must recognize from the shape;
- which parts are needed for the explanation or motion;
- which other stories could reuse the object.

First check whether an existing drawing, one of its states, or ordinary scene motion is sufficient.

A new protein name or video topic alone does not require a new sprite. Choose an existing pack by subject area.

## 2. Find a simple, expressive form

For a new design, first make one concept with the intended on-screen size in mind. Reuse an approved concept when one already fits.

Keep:
- a recognizable silhouette;
- a few large, meaningful forms;
- clear volume and consistent lighting;
- details that help explain the function.

Remove incidental texture, visual noise, and folds that disappear at the display size. Add faces when the story needs them.

Simplify the design itself, rather than only shrinking a complex image.

Preserve scientific meaning. For example, a protein's binding domain remains part of that protein. A molecule must not look like a cell containing another molecule. Generalize the shape only while the mechanism remains correct. When a specific structure is uncertain, check a primary source.

## 3. Choose the size and palette

For a detailed protein or receptor, start with a 128×128 px canvas. Use smaller sizes for simpler objects. Rectangular cells are allowed.

Choose the source size for the largest intended appearance in the working frame. Source resolution, color count, and display size are separate parameters.

Use the shared, fixed AAP-64 palette for new and redrawn PNGs. Take the exact colors from `pixel_kit.palette.AAP64`. Select the colors needed from this palette; do not create a separate adaptive palette for each object.

## 4. Prepare the drawing for reuse

For a new raster drawing or an artistic revision, use an available image generator and approved visual references. Use ordinary image-processing tools for technical PNG preparation.

Keep crisp pixel shapes, a dark outline, and alpha values of only 0 or 255. Check the edges for background remnants and halos.

One base drawing should work in different environments. Set scene lighting, weather, labels, and presentation in the scene. Separate sprite versions for every style are unnecessary.

The `idle` state is required. Add other states and separate parts when an action needs them. Use existing tool features for movement, appearance, and scaling. Do not generate an image for every video frame.

For a sheet, use equal-sized cells: one row per animation, one column per frame. Keep the anchor consistent across states.

## 5. Save in the existing library

Use the current layout:
- PNG directly in `packs/<pack>/sprites/`;
- an entry in the existing `sprites.json`;
- a row in the existing `CREDITS.csv`.

For each new or redrawn PNG, explicitly set `"source": "png"` and `"palette": "AAP-64"`. A molecule or protein that binds by its own surface also gets `"body": "molecule"`: draw its binding site where `CONTRIBUTING.md` says, so the tool can find it. Follow `CONTRIBUTING.md` for the other fields and license requirements.

Name the object, not the video or style. Assign specific scientific roles and labels in the scene.

Save only reusable sprites in the library. Keep prompts, concepts, comparisons, and intermediate exports in existing ignored working outputs. Do not create extra asset folders, text descriptions, or separate registries.

When replacing an accepted drawing, preserve a way to restore the previous version. Do not run a full rebuild of code sprites merely to register one PNG.

## 6. Verify the result

From the working clone root, run:

```bash
.venv/bin/python tools/validate_sprites.py
.venv/bin/python pixsci.py sheet out/sheet.png
```

The validator must print `VALID`.

Also:
- load the sprite through the project's normal loader;
- inspect it on light and dark backgrounds;
- check it at the intended display size, not only when enlarged;
- for multiple states, check the sequence and anchor stability.

Technical validation does not replace art review: the silhouette, volume, and scientific meaning must remain clear.

When comparing variants, change one parameter at a time at the same display size.

Show the finished sprite and briefly report its location, dimensions, file size, reusable parts or states, and verification results.
