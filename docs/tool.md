# The tool without an agent

The skills run these commands for you. Read this page to run them by hand, to work on the core, or to see how a
plan becomes a video. Paths are relative to the repo root.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # also needs ffmpeg
.venv/bin/python pixsci.py doctor                                     # what is there, what is missing
.venv/bin/python pixsci.py sheet  out/sheet.png                       # the sprites you can use
.venv/bin/python pixsci.py check  videos/my-topic/explainer.yaml       # a plan you wrote (PLAN.md)
.venv/bin/python pixsci.py board  videos/my-topic/explainer.yaml out   # storyboards, every format
.venv/bin/python pixsci.py render videos/my-topic/explainer.yaml out   # the videos
```

A 46 s video in all four formats renders in about 25 s on a laptop. Plans and videos are not committed.

## Voice and subtitles

`--voice` speaks `voiceover.md`, times each word, and puts the sound into the video:

```
voiceover.md ─> Qwen3-TTS ─> voice/<scene>.wav ─> Qwen3-ForcedAligner ─> voice/<scene>.words.json
                                                                               │
explainer.yaml: beats on words {word: "attacks"}, subtitles: true ─────────────┴─> render with sound
```

- [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) 1.7B CustomVoice speaks (Apache 2.0; English, Russian and 8 more
  languages; voices `ryan`, `aiden`; `tts: {instruct: ...}` sets the manner). Each scene lasts as long as its audio.
- [Qwen3-ForcedAligner](https://huggingface.co/Qwen/Qwen3-ForcedAligner-0.6B) finds when each word of the known text
  is heard (no transcription needed). Then the start and end of each word are trimmed to the sound.
- A beat on a word starts when the word is heard; `subtitles: true` shows the text word for word. Format: PLAN.md.

```bash
.venv/bin/pip install -r requirements-voice.txt          # Python 3.10 to 3.12, PyTorch
.venv/bin/pip install --no-deps qwen-asr==0.0.6           # the aligner; it pins another transformers but works with this one
.venv/bin/python pixsci.py voice  videos/my-topic/explainer.yaml out          # listen: out/<name>-voice.wav
.venv/bin/python pixsci.py render videos/my-topic/explainer.yaml out --voice  # video with sound and subtitles
```

The first run downloads about 6 GB from Hugging Face (a cloud sandbox must allow `huggingface.co` and `*.hf.co`).
On a CPU, speech takes about 5 to 10 times its length; a scene is spoken and aligned again only when its text or
`tts:` changes. Without the aligner, word times are estimated from the text. The progress bars and warnings of the models go to
`OUTDIR/voice/log.txt` (one run per file); the command prints a short result: the scenes spoken, the word times,
the scene times, and the path of the audio. An error stays on the screen. Progress of the first download:
`tail OUTDIR/voice/log.txt`.

## How it works

```
voiceover.md  ─┐
explainer.yaml ─┼─> pixel_kit/explain.py ──> Timeline ──> ffmpeg ──> <name>-<format>.mp4
packs/         ─┘        (layout per format: pixel_kit/frame.py)
```

- `explainer.yaml`: scenes (`title`, `cast`, `action`, `fact`, `flow`, `summary`, `custom`). Format: `skills/animate/PLAN.md`.
- `action` scenes place actors in fractions of the frame and run timed beats (move, animation, badge, verb), so one scene fits every format.
- Verbs are actions with effects (`secrete`, `block`, `hit`): YAML in a pack that lists primitives of the core
  (`pixel_kit/fx.py`), with a light layer over the colors and hit mechanics (windup, freeze, shake, push).
  `pixsci.py verbs out/verbs.png` lists and draws them. Why: `docs/adr/0001-verbs-and-primitives.md`.
- The frame is small (480x270 for 16:9) and scaled x4 with nearest neighbor: sharp pixels at any size.
- Text: Medeo Pixel on a grid 2 times finer than the frame (one text pixel is half a frame pixel), so
  text keeps its size (16 px line at scale 1) with finer letters. Sizes stay in frame pixels. Text is drawn
  over the picture of the frame (over sprites). Medeo Pixel has Latin and Cyrillic.
  `PIXEL_TEXT_FONT=unifont` brings back Unifont 16 px. How it works: `pixel_kit/font.py`, top.

## Layout

```
pixsci.py              command line: doctor, formats, sheet, verbs, check, board, render, frames, voice
fonts/                 unifont.otf, MedeoPixel.ttf (from npm medeo-font 1.0.0, WOFF to TTF) and their licenses
pixel_kit/             the core: frame, explain, sets, timebar, packs, sprites, verbs, ui, bg, fx, font, palette, scene, voice
packs/biology/         pack.yaml; verbs.yaml; sprites/ (PNG sheets, sprites.json, CREDITS.csv); code/ (sprites drawn in code)
packs/earth/           shared water, weather, and soil sprites; the same pack structure
tools/                 build_sprites.py, validate_sprites.py, make_sheet.py
skills/                agent skills: setup, storyboard, animate, add-verb (linked from .claude/skills and .agents/skills)
.claude-plugin/        plugin.json and marketplace.json: the repo installs as a Claude plugin
```

For choosing base sprites and their meaningful states, see
[`packs/biology/bible.md`](../packs/biology/bible.md) and
[`packs/earth/bible.md`](../packs/earth/bible.md). A new environment style reuses these
sprite files; it does not need another sprite library.
