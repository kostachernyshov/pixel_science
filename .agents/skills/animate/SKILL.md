---
name: animate
description: Make a short pixel-art science video (20 to 45 s and a summary frame) in up to four formats (16:9, 9:16 reels, 1:1, 4:1 banner) from a sourced voice-over, when the person already knows what to show. Use when the person asks to animate a pixel explainer, a science animation, or a reel about a biology idea.
---

# Animate

The video explains one science idea to a viewer without training: one mechanism, a few characters,
one rule at the end. The voice explains; the picture shows. Each claim comes from a source.

The tool is `pixsci.py` at the repo root. Run each command from the repo root:

```
.venv/bin/python pixsci.py <command> ...
```

If `.venv` does not exist: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
The tool needs `ffmpeg`. If `ffmpeg -version` fails, tell the person to install it (`brew install ffmpeg` on a Mac). Stop.

```
1 topic → 2 sources → 3 voice-over [person] → 4 plan → 5 check
        → 6 storyboard [person] → 7 render → 8 summary
```

Work in `videos/<slug>/`, outside the repo or ignored by git: plans and videos are not committed.
Sprites come from the packs in `packs/` (now `biology`); name them in the plan with `packs: [biology]`.

If the person does not know what to show yet, or the topic is long or has 3 or more steps, run the `storyboard` skill first. With an accepted `videos/<slug>/storyboard.md`, take the topic, sources, and voice-over from it (one scene per frame), skip steps 1 to 3, and use step 6 only as a technical check.

## Steps

1. **Topic.** Get the idea in one sentence ("how NK cells find cancer cells"), the viewer (school, adult, student), and the formats. Default: adult viewer, all four formats. Cut the idea to one mechanism. A second mechanism is a second video.
2. **Sources.** Find 1 to 3 reliable sources: a review, a textbook, the original paper. Write them in `sources`. Each sentence of the voice-over must follow from them. Mark a hypothesis as a hypothesis in the voice-over.
3. **Voice-over.** Write `voiceover.md`: one `## S01` heading for each scene, the text under it. One idea in each scene. 60 to 110 words in total (25 to 45 s at 2.5 words a second). Plain words; name a term once, then explain it with an image ("MHC class one ... works like an ID badge"). Show the text and the sources to the person and ask: "Accept the voice-over? yes / changes". Do not continue without "yes".
4. **Plan.** Write `explainer.yaml` in the format of [PLAN.md](PLAN.md). Use the scene ids of the voice-over.
   - Start with `title`, then `cast` (who is in the story). Show the mechanism with `action` scenes. End with `summary`.
   - Choose sprites from the cast sheet: `pixsci.py sheet out/sheet.png`. Look at it. Check the pack's sprites before you name one.
   - Keep the same character in the same color in all scenes.
   - Time the beats of an `action` scene to its voice-over: the attack happens on the word "attacks".
   - If no scene type fits, write a `custom` scene and tell the person that it is a candidate for the library.
5. **Check.** Run `pixsci.py check explainer.yaml`. Fix the plan until the output is `CHECK PASSED`.
6. **Storyboard.** Run `pixsci.py board explainer.yaml out`. Look at each `out/board-<format>.png` yourself: text does not overlap or get cut, actors stay inside the frame, the badge and the caption do not cover a face. Fix and run again. Then show the boards to the person and ask: "Accept the storyboard? yes / changes". Do not render without "yes".
7. **Render.** `pixsci.py render explainer.yaml out` (add `--gif` for loops, `-f vertical` for one format).
8. **Summary.** Give the person the paths of the videos and the boards. Name the decisions that you made without the person, one line each.

## Rules

- One video, one mechanism. No new facts in the picture that the voice-over and the sources do not have.
- A caption has 1 to 3 words and stays 2 s or more. The voice explains; the caption names.
- No invented numbers. A number on screen is in a source.
- Cell death by an immune cell is apoptosis (shrink and break up), not an explosion.
- Do not draw new sprites in the plan. A new character goes into a pack first (see CONTRIBUTING.md), and the person sees the cast sheet before the render.
- Do not show a real person, a logo, or a brand.

## Done when

- The person accepted `voiceover.md` (with its sources) and the storyboards.
- `pixsci.py check` prints `CHECK PASSED`.
- `out/<name>-<format>.mp4` exists for each format of the plan, and the last scene is a `summary`.
