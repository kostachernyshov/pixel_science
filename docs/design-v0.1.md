# pixel_science v0.1: design decisions

Agreed with Kosta in a grilling session on 2026-11-01. This file is the source for the v0.1 rebuild.

## Product

- Local tool + agent skills + asset library for short pixel-art science explainers. Open to the community.
- Users: anyone interested; first Kosta and other bioinformaticians.
- Agent first. The person types `/animate`. The skill runs the internal CLI `pixsci`; only people without an agent type `pixsci` by hand. Installed as a Claude Code / Codex plugin.
- Everything in the repo is in English (code, docs, on-screen text, voice). Discussion with Kosta is in Russian.
- License: MIT for code, CC0-1.0 for sprites (CC-BY-4.0 accepted for outside sprites, per file in CREDITS.csv).
- Length: 20 to 60 s. A longer video is several short ones.

## Formats

landscape 16:9 (1920x1080), vertical 9:16 (1080x1920), square 1:1 (1080x1080), banner 4:1 (1920x480). One plan renders all four; layout is relative to the frame.

## Workflow of /animate

1. Request (topic, viewer, formats).
2. Sources, then storyboard with the voice-over text for each scene. If the harness can publish artifacts, the storyboard is an HTML artifact (frames in each format, text to read, style switch); else PNG. The person accepts it.
3. The skill offers to record (or synthesize) the voice-over.
4. With a voice: `pixsci` makes a local transcript (faster-whisper `small.en`, installed on first use), finds where each scene starts by fuzzy match of the scene text, and times actions to words (`on: attacks`). Drift from the text is reported.
5. Without a voice: the animation is timed from the storyboard text (2.7 words/s).
6. Render in the chosen formats.

Storytelling and storyboard skills get their own design session later.

## Pace (enforced by `pixsci check`)

- A shot changes every 2 to 4 s.
- Something moves in every frame; a new action at least every 1.5 s.
- The final frame holds 3 s.
- Camera in action scenes: zoom, pan, shake, integer zoom only (x2, x3).

## Numbers

- Real numbers (from sources) are shown neatly, with no extra marks.
- Invented numbers (schematic N, rates) get no on-screen mark, but the skill warns the person before render.

## Styles: the cascade

A sprite is looked up by name; the most specific variant wins:

1. a PNG drawn for this style (`style-arcade/sprites/nk.png`);
2. a code sprite (`library.py`) drawn again with the style's parameters (outline, shading, number of tones);
3. the base indexed PNG, recolored with the style's palette (free default).

First styles: `paper` (light, PICO-8, current), `arcade` (dark, CRT scanlines, neon; Space Invaders, Galaga), `gameboy` (4 greens; Dr. Mario era). References: character-select screens, PICO-8 (lospec), Pedro Medeiros (saint11), Pixelblog (slynyrd). Take techniques and composition, never copy sprites.

## Everything is a pack

- A pack is a folder with `pack.yaml`. It can provide sprites, a style, scene types, backgrounds, a `bible.md` (roles and colors), examples. The core knows no pack.
- Packs stack; a higher pack overrides a lower one (the same cascade as styles).
- v0.1 packs: `biology` (cells, immunity, plants, fungi), `earth` (planet, meteorite, crater, dinosaurs, shock wave), `physics` (particles, fields, detector), and `style-paper`, `style-arcade`, `style-gameboy`.
- All packs live in this repo now. The format allows packs in other git repos later.
- A generated catalog (name, tags, animations, pack, license, thumbnail) lets the agent find sprites: `pixsci find immune --json`. The human cast sheet is built from the same catalog.

## Sprites

Drawn in code by the agent (`/add-sprite`) or contributed as PNG by artists. No AI-generated sprites.

## Procedural scenes

Generators inside action scenes, each with a `seed` (same seed, same video): `swarm` (N sprites, motion by rule), `grow` (division or growth by formula), `field` (flow of molecules, a field or gradient); color by rule (state, generation).

## Skills

- `/animate`: topic to video.
- `/add-sprite`: the agent draws a sprite in code, validates it, shows the sheet.

## Sound

Voice only in v0.1. Music and 8-bit sound effects later, as a pack.

## v0.1 scope and order

1. Core with packs and the style cascade; catalog; `--json` on all commands.
2. Styles paper, arcade, gameboy.
3. Voice: transcript, alignment to words.
4. Generators, camera, pace checks.
5. Storyboard artifact.
6. Videos: anti-PD-L1 mechanism, Higgs boson. The Missing-self demo is removed.

Next: mycorrhiza, the Chicxulub impact energy; then external packs, TTS, sound. The repo goes public after 3 to 5 videos and one outside sprite that passes the checks.
