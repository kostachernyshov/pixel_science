# pixel_science

Pixel-art science explainers, made locally from a short plan. One plan renders four videos:

| Format | Size | For |
|---|---|---|
| landscape 16:9 | 1920x1080 | YouTube, slides |
| vertical 9:16 | 1080x1920 | Reels, Shorts, TikTok |
| square 1:1 | 1080x1080 | feed posts |
| banner 4:1 | 1920x480 | site header, wide banner |

Sprites come in packs (`packs/`). The first pack is `biology`: 70 sprites of immune cells, tumor cells,
body cells, molecules, lab props, and people, in one style (PICO-8 palette, 1 px outline, light background).

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # also needs ffmpeg
.venv/bin/python pixsci.py sheet  out/sheet.png                       # the sprites you can use
.venv/bin/python pixsci.py check  videos/my-topic/explainer.yaml       # a plan you wrote (PLAN.md)
.venv/bin/python pixsci.py board  videos/my-topic/explainer.yaml out   # storyboards, every format
.venv/bin/python pixsci.py render videos/my-topic/explainer.yaml out   # the videos
```

A 46 s video in all four formats renders in about 25 s on a laptop. Plans and videos are not committed.

## With an agent

The skill `/animate` (in `.agents/skills/animate/`, linked for Claude Code in `.claude/skills/`)
takes a topic to a video: sources, a voice-over that you accept, a plan, a storyboard that you accept,
and the render. Ask: "make a pixel explainer about how vaccines train B cells".

## How it works

```
voiceover.md  ─┐
explainer.yaml ─┼─> pixel_kit/explain.py ──> Timeline ──> ffmpeg ──> <name>-<format>.mp4
packs/         ─┘        (layout per format: pixel_kit/frame.py)
```

- `explainer.yaml`: scenes (`title`, `cast`, `action`, `fact`, `flow`, `summary`, `custom`). Format: `.agents/skills/animate/PLAN.md`.
- `action` scenes place actors in fractions of the frame and run timed beats (move, animation, badge, effect), so one scene fits every format.
- The frame is small (480x270 for 16:9) and scaled x4 with nearest neighbor: sharp pixels at any size.

## Layout

```
pixsci.py              command line: formats, sheet, check, board, render, frames
pixel_kit/             the core: frame, explain, packs, sprites, ui, bg, fx, font, palette, scene
packs/biology/         pack.yaml; sprites/ (PNG sheets, sprites.json, CREDITS.csv); code/ (sprites drawn in code)
tools/                 build_sprites.py, validate_sprites.py, make_sheet.py
.agents/skills/animate the agent skill
```

## Contribute

New sprites, packs, scene types, and backgrounds are welcome. Ideas and bugs go to GitHub Issues. Read [CONTRIBUTING.md](CONTRIBUTING.md).

## Origin

`pixel_kit` comes from the `/animate` skill of [kostachernyshov-skills](https://github.com/kostachernyshov)
and the *Cancer Wars* video series. This repo removes the data-report parts and adds the four formats.

## License

Code: MIT. Sprites: CC0-1.0 or CC-BY-4.0, per file in each pack's `sprites/CREDITS.csv`. Font: GNU Unifont. See [LICENSE](LICENSE).
