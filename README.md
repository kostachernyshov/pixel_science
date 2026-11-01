# pixel_science

Short pixel-art science explainers (20 to 60 s), made locally from a plan and a voice-over.
One plan renders four formats and three styles:

| Format | Size | For |
|---|---|---|
| landscape 16:9 | 1920x1080 | YouTube, slides |
| vertical 9:16 | 1080x1920 | Reels, Shorts, TikTok |
| square 1:1 | 1080x1080 | feed posts |
| banner 4:1 | 1920x480 | site header, wide banner |

| Style | Look |
|---|---|
| `paper` | light paper, PICO-8 colors, soft shading (the base) |
| `arcade` | dark screen, flat neon bodies, a glow ring, CRT scanlines |
| `gameboy` | four greens, every frame cut to four shades |

## With an agent

The skill `/animate` (in `.agents/skills/animate/`, linked for Claude Code in `.claude/skills/`) takes a topic
to a video: sources, a voice-over you accept, a storyboard you accept (an HTML page with format and style
switches when the agent can publish one), an optional recording timed word by word, and the render.
Ask: "make a pixel explainer about how vaccines train B cells". `/add-sprite` draws a missing character.

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # the render also needs ffmpeg
.venv/bin/python pixsci.py check  examples/anti-pdl1/explainer.yaml
.venv/bin/python pixsci.py board  examples/anti-pdl1/explainer.yaml out --html
.venv/bin/python pixsci.py render examples/anti-pdl1/explainer.yaml out
.venv/bin/python pixsci.py render examples/higgs-boson/explainer.yaml out --style arcade -f vertical
```

Every command takes `--json`. `pixsci.py --help` lists them: `formats`, `packs`, `styles`, `find`, `catalog`,
`sheet`, `check`, `board`, `render`, `frames`, `transcribe`, `align`, `animatic`.

## How it works

```
voiceover.md ──> words (2.7 words/s, or a recording aligned word by word)
explainer.yaml ─┬─> pixel_kit/explain.py ──> Timeline ──> ffmpeg ──> <name>-<format>.mp4
packs/ ─────────┘   (layout per format, style per frame, generators, camera)
```

- **Packs.** Everything the core draws comes from a pack: a folder with `pack.yaml` that can hold sprites,
  code sprites, backgrounds, a style, and a `bible.md` of roles and colors. Packs stack (`packs: [biology]`);
  a higher pack overrides a lower one. Packs now: `biology`, `physics`, `style-paper`, `style-arcade`, `style-gameboy`.
- **The style cascade.** A sprite is looked up by name; the most specific variant wins: a PNG drawn for the
  style, then a code sprite drawn again with the style's parameters, then the base PNG recolored.
- **The catalog.** `packs/catalog.json` lists every sprite, background, and style with tags, animations,
  license, and a thumbnail box. `pixsci find immune killer --json` searches it; the cast sheet
  (`pixsci sheet out/sheet.png --style arcade`) is drawn from it.
- **Words.** Each scene lasts as long as its words. With a recording, `pixsci transcribe` makes a local
  transcript (faster-whisper `small.en`, installed on first use), and scenes start on their first spoken words.
  Beats are keyed to words: `on: attacks`. `pixsci align` reports the drift between the recording and the text.
- **Generators.** `swarm` (N sprites that seek, orbit, flow, wander), `grow` (cells that divide, colored by
  generation), `field` (a lattice that clings to a particle, a flow, a spreading gradient). Each has a seed.
- **Camera.** Integer zoom (x2, x3), pan, shake: pixels stay square.
- **Pace.** `pixsci check` enforces a shot every 2 to 4 s, something new every 1.5 s in an action scene,
  motion in every frame, and a final hold of 3 s. It warns about invented counts and numbers on screen.
- The frame is small (480x270 for 16:9) and scaled x4 with nearest neighbor: sharp pixels at any size.

## Layout

```
pixsci.py              command line (pixel_kit/cli.py)
pixel_kit/             the core: frame, palette, style, packs, sprites, catalog, words, voice, gen, camera,
                       pace, explain, scene, board, font, fx, ui, bg
packs/                 biology/, physics/, style-paper/, style-arcade/, style-gameboy/, catalog.json
tools/                 build_sprites.py, validate_sprites.py
examples/              anti-pdl1/ (biology), higgs-boson/ (physics)
.agents/skills/        animate, add-sprite
docs/                  design-v0.1.md (decisions), ci/check.yml (CI workflow to install)
```

## Contribute

New sprites, packs, styles, scene types, and example videos are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md).

## Origin

`pixel_kit` comes from the `/animate` skill of [kostachernyshov-skills](https://github.com/kostachernyshov)
and the *Cancer Wars* video series.

## License

Code: MIT. Sprites: CC0-1.0 or CC-BY-4.0, per file in each pack's `sprites/CREDITS.csv`. Font: GNU Unifont. See [LICENSE](LICENSE).
