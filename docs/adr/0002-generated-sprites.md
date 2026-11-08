# 2. Sprites from an image generator are welcome

Date: 2026-11-08. Status: accepted (grilling session with Kosta).

## Context

The v0.1 plan said "no AI-generated sprites". In practice, the 99 sprites of the November 2026 batch (biology,
earth, physics) were made with an image generator and then fitted to the AAP-64 palette and the pack style.

## Decision

1. An agent or a contributor may make sprites with an image generator, and is encouraged to.
2. The PNG in the pack meets the same rules as any sprite: the palette, binary transparency, the outline, the
   sheet layout (`CONTRIBUTING.md`); `tools/validate_sprites.py` prints `VALID`.
3. Credit is the pack's `author` and `license` in `pack.yaml`. Prompts, concepts, and drafts are not kept in the repo.

## Consequences

- `skills/add-sprite/SKILL.md` starts a new raster drawing with an image generator.
- `CREDITS.csv` is removed; a sprite by an outside author names its author, license, and url in `sprites.json`.
