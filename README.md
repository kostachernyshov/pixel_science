# pixel_science

Pixel-art science explainers, made locally from a short plan. One plan renders four videos:

| Format | Size | For |
|---|---|---|
| landscape 16:9 | 1920x1080 | YouTube, slides |
| vertical 9:16 | 1080x1920 | Reels, Shorts, TikTok |
| square 1:1 | 1080x1080 | feed posts |
| banner 4:1 | 1920x480 | site header, wide banner |

The first topic is biology. The library has 70 sprites: immune cells, tumor cells, body cells, molecules,
lab props, and people, in one style (PICO-8 palette, 1 px outline, light background).

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # also needs ffmpeg
.venv/bin/python pixsci.py check  examples/nk-missing-self/explainer.yaml
.venv/bin/python pixsci.py board  examples/nk-missing-self/explainer.yaml out
.venv/bin/python pixsci.py render examples/nk-missing-self/explainer.yaml out
```

The render of the 46 s example in all four formats takes about 25 s on a laptop.

## With an agent

The skill `/explain` (in `.agents/skills/explain/`, linked for Claude Code in `.claude/skills/`)
takes a topic to a video: sources, a voice-over that you accept, a plan, a storyboard that you accept,
and the render. Ask: "make a pixel explainer about how vaccines train B cells".

## How it works

```
voiceover.md  ─┐
explainer.yaml ─┼─> pixel_kit/explain.py ──> Timeline ──> ffmpeg ──> <name>-<format>.mp4
sprites/*.png  ─┘        (layout per format: pixel_kit/frame.py)
```

- `explainer.yaml`: scenes (`title`, `cast`, `action`, `fact`, `flow`, `summary`, `custom`). Format: `.agents/skills/explain/PLAN.md`.
- `action` scenes place actors in fractions of the frame and run timed beats (move, animation, badge, effect), so one scene fits every format.
- The frame is small (480x270 for 16:9) and scaled x4 with nearest neighbor: sharp pixels at any size.

## Layout

```
pixsci.py              command line: check, board, render, frames, cues, animatic, preview, sheet
pixel_kit/             drawing library: frame, explain, sprites, ui, bg, fx, font, palette, voice, charts
sprites/               sprite sheets (PNG), sprites.json (cells and animations), CREDITS.csv
tools/                 build_sprites.py, validate_sprites.py, make_sheet.py, preview_sheets.py, voice_sync.py
examples/              example plans with voice-over
.agents/skills/explain the agent skill
```

## Contribute

New sprites, scene types, backgrounds, and example videos are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md).

## Origin

`pixel_kit` comes from the `/animate` skill of [kostachernyshov-skills](https://github.com/kostachernyshov)
and the *Cancer Wars* video series. This repo removes the data-report parts and adds the four formats.

## License

Code: MIT. Sprites: CC0-1.0 or CC-BY-4.0, per file in `sprites/CREDITS.csv`. Font: GNU Unifont. See [LICENSE](LICENSE).
