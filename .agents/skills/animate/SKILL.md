---
name: animate
description: Make a 20 to 60 s pixel-art science explainer video on a topic the person names, in up to four formats (16:9, 9:16, 1:1, 4:1) and three styles (paper, arcade, gameboy), from a sourced voice-over. Use when the person asks for a pixel explainer, a science animation, or a reel about a science idea.
---

# Animate

One video explains one science idea to a viewer without training: one mechanism, a few characters,
one rule at the end. The voice explains; the picture shows. Each claim comes from a source.

The tool is `pixsci` (`pixsci.py` at the repo root). Run it from the repo root with `--json` and read the JSON:

```
.venv/bin/python pixsci.py <command> ... --json
```

Setup, once: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`. The render needs `ffmpeg`;
if `ffmpeg -version` fails, tell the person to install it (`brew install ffmpeg` on a Mac) and stop.

```
1 topic → 2 sources → 3 storyboard text [person] → 4 plan → 5 check → 6 storyboard [person]
        → 7 voice (optional) → 8 render → 9 summary
```

Work in `videos/<slug>/` (git ignores `out/`). Examples to copy: `examples/anti-pdl1/` (biology), `examples/higgs-boson/` (physics).

## Steps

1. **Topic.** Get the idea in one sentence, the viewer (school, adult, student), the formats, and the style. Default: adult viewer, all four formats, style `paper`. Cut the idea to one mechanism; a second mechanism is a second video. If the topic needs several mechanisms or more than 60 s, run the `story` and `script` skills first, then start at the plan step. Done when the idea fits one sentence with one mechanism.
2. **Sources.** Find 1 to 4 reliable sources: a review, a textbook, the original paper. Every sentence of the voice-over follows from them; mark a hypothesis as a hypothesis. Done when each sentence you will write has its source.
3. **Voice-over.** Write `voiceover.md`: one `## S01` heading per scene, the text to read under it. One idea per scene, 2 to 4 s of speech per shot (about 6 to 12 words), 55 to 150 words in total (the pace is 2.7 words a second). Name a term once, then show it with an image. Show the text with the sources to the person and ask: "Accept the voice-over? yes / changes". Done when the person says yes.
4. **Plan.** Write `explainer.yaml` in the format of [PLAN.md](PLAN.md), with the scene ids of the voice-over.
   - Choose the packs (`pixsci packs`) and find characters with `pixsci find <word> --json`; look at the sheet (`pixsci sheet out/sheet.png --pack <pack>`). If a character is missing, run the `add-sprite` skill first.
   - Write the `model:` first: the things, their parts, and each link of the mechanism with its source (PLAN.md, "The mechanism model"). Show the picture at the level where the mechanism acts: when parts touch, use a `contact` scene, where they are objects on the surfaces, not badges.
   - Start with `title`, move bodies with `action` scenes, show each link with a `contact` scene, end with `summary`. Keep a character in the same sprite and color in all scenes (the pack's `bible.md`).
   - Key beats to words: `on: attacks` fires on the word "attacks", with a recording or without.
   - Keep the pace: a camera cut or pan every 2 to 4 s, something new every 1.5 s. Use `swarm`, `grow`, `field` for crowds, growth, and fields; give the plan a `seed`.
5. **Check.** Run `pixsci check explainer.yaml --json`. Fix the plan until `passed` is true. Keep the `warnings`: each schematic count (a swarm `n`) and each number on screen goes to the person in step 6. A real number on screen is listed under `numbers:` with its source.
6. **Storyboard.** Run `pixsci board explainer.yaml out --html --json`. Look at each `out/board-<format>.png` yourself: text does not overlap or get cut, actors stay inside the frame, a badge or caption does not cover a face, and each link of the model is visible where its parts touch. Fix and run again. Then show the person the storyboard: publish `out/board.html` as an artifact when you can publish artifacts (format and style switches, the text to read under each frame); else show the PNGs. Tell the person the warnings (invented counts, numbers on screen) and ask: "Accept the storyboard? yes / changes". Done when the person says yes.
7. **Voice (optional).** Offer to time the video to a recording of the voice-over: the person records `voiceover.md` (a phone is fine) or gives a synthesized file. Add `voice: {audio: voice.m4a}` to the plan, run `pixsci transcribe explainer.yaml --json` (a local transcript; the first run installs faster-whisper and downloads the `small.en` model), then `pixsci align explainer.yaml --json`. Read `drift`: words the person skipped or added. If the drift changes the meaning, show it to the person. Run `pixsci check` again: the scene lengths now come from the voice. Without a recording the video is timed from the text.
8. **Render.** `pixsci render explainer.yaml out --json` (`--style arcade` for another style, `-f vertical` for one format, `--gif` for loops). With a recording the voice is in the video.
9. **Summary.** Give the person the paths of the videos and the storyboard, the warnings, and the decisions you made without the person, one line each.

## Rules

- One video, one mechanism. No fact in the picture that the voice-over and the sources do not have.
- Every interaction on screen is a link of the `model:` with its source, drawn where the two parts touch.
- A caption has 1 to 3 words and stays 2 s or more. The voice explains; the caption names.
- Cell death by an immune cell is apoptosis (shrink and break up), not an explosion.
- Sprites come from packs. A new character goes into a pack first (`add-sprite`), drawn in code or contributed as a PNG; AI-generated images are never sprites.
- A real person, a logo, or a brand stays out of the picture.

## Done when

- The person accepted `voiceover.md` with its sources, and the storyboard.
- `pixsci check` reports `passed: true`.
- `out/<name>-<format>.mp4` exists for each format of the plan.
